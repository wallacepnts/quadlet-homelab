#!/usr/bin/env python3
"""The app store: a web front end over `qh --catalog` and `qh <app> --apply`.

It installs nothing by itself. The catalog is `qh --catalog`, the plan is the
same dry-run a person reads in the terminal, and the install is the same
`qh <app> --apply` — one install path, not two. What the terminal would ask
(`manual` secrets, `[vars]`) the form asks first, and it is stored through the
same functions install.py uses, so a value the terminal refuses is refused here.

It runs on the host as a systemd --user service, not as a container: its whole
job is driving systemd and podman as you. A container would need your home,
your podman socket and your systemd bus, which is the same access without the
honesty (store/qh-store.service, docs/tools.md).

Access is a token in ~/.config/quadlet-homelab/store-token, created on the
first start. It listens on 127.0.0.1 unless told otherwise.

    python3 store.py                          # http://127.0.0.1:8484
    python3 store.py --listen 100.64.0.1:8484 # the host's tailnet address
    QH_STORE_LISTEN=100.64.0.1:8484 store.py  # the same, as the service reads it
    python3 store.py --prefix /tmp/test       # against a sandbox, like qh --prefix
    python3 store.py --selftest

No dependencies: stdlib only.
"""

import argparse
import contextlib
import hashlib
import hmac
import importlib.util
import json
import os
import re
import secrets
import subprocess
import sys
import threading
import time
from http import cookies
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import parse_qs, urlparse

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))
import qhui  # noqa: E402

_spec = importlib.util.spec_from_file_location("qh_install", ROOT / "install.py")
I = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(I)

PT = {
    "the store is at": "a loja está em",
    "token created in": "token criado em",
    "the token is in": "o token está em",
    "read it with": "leia com",
    "another job is running": "outra tarefa está rodando",
    "unknown service": "serviço desconhecido",
    "unknown unit": "unit desconhecida",
    "unknown action": "ação desconhecida",
    "not asked by this service": "não é pedido por este serviço",
    "no spaces: Volume= would cut the path there": "sem espaços: o Volume= cortaria o caminho ali",
    "the service refused this value:": "o serviço recusou este valor:",
    "secret stored": "secret gravado",
    "sandbox, not executed": "sandbox, não executado",
    "the web store over qh (install, update, remove, logs)":
        "a loja web sobre o qh (instalar, atualizar, remover, logs)",
    "address and port to listen on": "endereço e porta para escutar",
    "use another home (to test without touching the real one)":
        "usar outro home (para testar sem tocar no real)",
    "test the store against a sandbox": "testar a loja contra um sandbox",
}
loc = qhui.translator(PT)

STATIC = ROOT / "store"
ARQUIVOS = {"/": "index.html", "/login": "login.html",
            "/app.js": "app.js", "/style.css": "style.css"}
TIPOS = {".html": "text/html; charset=utf-8", ".js": "text/javascript; charset=utf-8",
         ".css": "text/css; charset=utf-8"}
# Nothing inline, nothing from elsewhere but the icons: every string the page
# shows goes in through textContent, and this is the second fence behind that.
CSP = ("default-src 'none'; script-src 'self'; style-src 'self'; img-src https: data:; "
       "connect-src 'self'; form-action 'self'; frame-ancestors 'none'; base-uri 'none'")
COOKIE = "qh_store"
NOME = re.compile(r"^[a-z0-9][a-z0-9._-]*$")
ACOES = {"install": [], "update": ["--update"], "remove": ["--remove"]}
VERBOS = {"start", "stop", "restart"}

PREFIX = None              # --prefix: the sandbox every qh call is pointed at
JOBS, JOB_LOCK = {}, threading.Lock()


# -- the host, through qh --------------------------------------------------------

def qh(*args):
    """argv for install.py, carrying --prefix when there is one."""
    cmd = [sys.executable, str(ROOT / "install.py"), *args]
    return cmd + (["--prefix", PREFIX] if PREFIX else [])


def qh_env(lang):
    # NO_COLOR: the output lands in a <pre>, where escape codes are noise.
    return {**os.environ, "QH_LANG": "pt_BR" if lang == "pt" else "en", "NO_COLOR": "1"}


def catalog(lang="en"):
    r = subprocess.run(qh("--catalog"), capture_output=True, text=True,
                       env=qh_env(lang), cwd=ROOT, timeout=120)
    return json.loads(r.stdout)


def service_dir(app):
    """The folder of a service the store may act on, or None."""
    if not NOME.match(app or ""):
        return None
    d = I.APPS / app
    return d if d.is_dir() and any(d.glob("*.container")) else None


def unit_exists(unit):
    return bool(NOME.match(unit or "")) and any(I.APPS.glob(f"*/{unit}.container"))


def asks(app):
    """({manual secret names}, {Volume= variable names}) — the only answers accepted."""
    s = I.Service(app, PREFIX)
    manuais = set()
    if s.ini.has_section("secrets"):
        manuais = {n for n, r in s.ini.items("secrets")
                   if r.strip().partition(" ")[0] == "manual" and n in s.secrets()}
    variaveis = {n for p, f in s.volumes() if f is None
                 for n in re.findall(r"\$\{([A-Za-z_][A-Za-z0-9_]*)\}", p)}
    return manuais, variaveis


def provision(app, segredos, variaveis):
    """Stores the answers the terminal would have asked for. False stops the job.

    Runs before `qh --apply`, which then finds the secret existing and the
    variable set and asks nothing. An empty answer is skipped, as in the
    terminal: the install goes on and says what is still missing.
    """
    s = I.Service(app, PREFIX)
    for nome, valor in variaveis.items():
        if not valor.strip() or I.manager_var(nome):
            continue
        conf, valor = I.save_var(s, nome, valor)
        if conf is None:
            print(f"  {nome}: " + loc("no spaces: Volume= would cut the path there"))
            return False
        print(f"  -> {conf}: {nome}={valor}")
    for nome, valor in segredos.items():
        valor = valor.strip()
        if not valor:
            continue
        ok, porque = I.secret_ok(s, nome, valor)
        if not ok:
            print(f"  {nome}: " + loc("the service refused this value:") + f" {porque}")
            return False
        if porque:
            print(f"  !  {porque}")
        I.store_secret(s, nome, valor)
        print(f"  {nome}: " + loc("secret stored"))
    return True


class Job:
    """One run, its output as it arrives, and its exit code once it has one."""

    def __init__(self, app, action):
        self.id = secrets.token_hex(8)
        self.app, self.action = app, action
        self.out, self.rc = [], None

    def write(self, texto):           # a file, for redirect_stdout
        if texto:
            self.out.append(texto)

    def flush(self):
        pass


def start_job(app, action, cmd, lang, prepare=None):
    """The job, running in the background — or None when another one still is.

    One at a time: two `qh --apply` racing each other over the same
    systemd/ tree is the one thing the terminal never does.
    """
    if not JOB_LOCK.acquire(blocking=False):
        return None
    job = Job(app, action)
    JOBS[job.id] = job
    for velho in list(JOBS)[:-20]:
        JOBS.pop(velho, None)

    def worker():
        try:
            if prepare:
                # One job at a time is what makes swapping the global stdout
                # safe here: install.py's helpers say() what they do.
                with contextlib.redirect_stdout(job):
                    seguir = prepare()
                if seguir is False:
                    job.rc = 1
                    return
            if PREFIX and cmd[0] == "systemctl":
                job.write(f"({loc('sandbox, not executed')}: {' '.join(cmd)})\n")
                job.rc = 0
                return
            p = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                                 stdin=subprocess.DEVNULL, text=True, cwd=ROOT,
                                 env=qh_env(lang))
            for linha in p.stdout:
                job.write(linha)
            job.rc = p.wait()
        except Exception as e:        # the page must learn the job ended
            job.write(f"\n{type(e).__name__}: {e}\n")
            job.rc = 1
        finally:
            JOB_LOCK.release()

    threading.Thread(target=worker, daemon=True).start()
    return job


# -- access ----------------------------------------------------------------------

def token_file():
    return Path(PREFIX or Path.home()) / ".config/quadlet-homelab/store-token"


def load_token():
    """(token, created now?) — written 0600 on the first start."""
    f = token_file()
    if f.is_file() and f.read_text().strip():
        return f.read_text().strip(), False
    f.parent.mkdir(parents=True, exist_ok=True)
    fd = os.open(f, os.O_WRONLY | os.O_CREAT | os.O_TRUNC, 0o600)
    with os.fdopen(fd, "w") as fh:
        fh.write(secrets.token_urlsafe(24) + "\n")
    return f.read_text().strip(), True


def cookie_for(token):
    # A digest, not the token: the cookie jar is not where the key should live.
    return hashlib.sha256(f"qh-store:{token}".encode()).hexdigest()


# -- HTTP -----------------------------------------------------------------------

class Handler(BaseHTTPRequestHandler):
    token = ""
    server_version = "qh-store"

    def log_message(self, fmt, *args):     # the journal gets errors, not every poll
        pass

    def _send(self, code, body=b"", tipo="application/json", headers=()):
        self.send_response(code)
        self.send_header("Content-Type", tipo)
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        self.send_header("X-Content-Type-Options", "nosniff")
        self.send_header("Referrer-Policy", "no-referrer")
        self.send_header("Content-Security-Policy", CSP)
        for k, v in headers:
            self.send_header(k, v)
        self.end_headers()
        self.wfile.write(body)

    def _json(self, code, data):
        self._send(code, json.dumps(data, ensure_ascii=False).encode())

    def _redirect(self, where, headers=()):
        self._send(303, b"", "text/plain", [("Location", where), *headers])

    def _logged(self):
        jar = cookies.SimpleCookie(self.headers.get("Cookie", ""))
        valor = jar[COOKIE].value if COOKIE in jar else ""
        return hmac.compare_digest(valor, cookie_for(self.token))

    def _body(self, limite=65536):
        n = int(self.headers.get("Content-Length") or 0)
        if n > limite:
            raise ValueError("body too large")
        return self.rfile.read(n) if n else b""

    def _static(self, nome):
        f = STATIC / nome
        self._send(200, f.read_bytes(), TIPOS[f.suffix])

    # GET ---------------------------------------------------------------------

    def do_GET(self):
        url = urlparse(self.path)
        q = {k: v[0] for k, v in parse_qs(url.query).items()}
        if url.path in ("/login", "/style.css"):
            return self._static(ARQUIVOS[url.path])
        if not self._logged():
            if url.path.startswith("/api/"):
                return self._json(401, {"error": "login"})
            return self._redirect("/login")
        if url.path in ARQUIVOS:
            return self._static(ARQUIVOS[url.path])
        lang = "pt" if q.get("lang") == "pt" else "en"
        if url.path == "/api/catalog":
            return self._json(200, catalog(lang))
        if url.path == "/api/plan":
            app, action = q.get("app", ""), q.get("action", "")
            if not service_dir(app):
                return self._json(400, {"error": loc("unknown service")})
            if action not in ACOES:
                return self._json(400, {"error": loc("unknown action")})
            r = subprocess.run(qh(app, *ACOES[action]), capture_output=True, text=True,
                               stdin=subprocess.DEVNULL, env=qh_env(lang), cwd=ROOT,
                               timeout=120)
            return self._json(200, {"rc": r.returncode, "output": r.stdout + r.stderr})
        if url.path.startswith("/api/job/"):
            job = JOBS.get(url.path.rsplit("/", 1)[1])
            if not job:
                return self._json(404, {"error": "job"})
            desde = int(q.get("from", "0") or 0)
            return self._json(200, {"app": job.app, "action": job.action, "rc": job.rc,
                                    "next": len(job.out), "output": "".join(job.out[desde:])})
        if url.path == "/api/logs":
            unit = q.get("unit", "")
            if not unit_exists(unit):
                return self._json(400, {"error": loc("unknown unit")})
            if PREFIX:
                return self._json(200, {"output": ""})
            r = subprocess.run(["journalctl", "--user", "-u", f"{unit}.service", "-n", "200",
                                "--no-pager", "-o", "short-iso"],
                               capture_output=True, text=True, timeout=30)
            return self._json(200, {"output": r.stdout + r.stderr})
        return self._json(404, {"error": "not found"})

    # POST --------------------------------------------------------------------

    def do_POST(self):
        url = urlparse(self.path)
        try:
            corpo = self._body()
        except ValueError:
            return self._json(413, {"error": "too large"})
        if url.path == "/login":
            dado = parse_qs(corpo.decode(errors="replace")).get("token", [""])[0].strip()
            if dado and hmac.compare_digest(dado, self.token):
                return self._redirect("/", [("Set-Cookie", f"{COOKIE}={cookie_for(self.token)}; "
                                             "Path=/; HttpOnly; SameSite=Strict")])
            time.sleep(1)                 # a guess per second, not thousands
            return self._redirect("/login?e=1")
        if not self._logged():
            return self._json(401, {"error": "login"})
        # A header a plain <form> cannot send: a page elsewhere that posts here
        # with the cookie still fails, without a CSRF token to keep in sync.
        if self.headers.get("X-QH-Store") != "1":
            return self._json(403, {"error": "missing X-QH-Store"})
        try:
            d = json.loads(corpo or b"{}")
        except ValueError:
            return self._json(400, {"error": "json"})
        lang = "pt" if d.get("lang") == "pt" else "en"

        if url.path == "/api/run":
            app, action = d.get("app", ""), d.get("action", "")
            if not service_dir(app):
                return self._json(400, {"error": loc("unknown service")})
            if action not in ACOES:
                return self._json(400, {"error": loc("unknown action")})
            segredos, variaveis = d.get("secrets") or {}, d.get("vars") or {}
            if not (isinstance(segredos, dict) and isinstance(variaveis, dict)
                    and all(isinstance(v, str) for v in [*segredos.values(), *variaveis.values()])):
                return self._json(400, {"error": "secrets/vars"})
            manuais, nomes = asks(app)
            fora = sorted(set(segredos) - manuais) + sorted(set(variaveis) - nomes)
            if fora:
                return self._json(400, {"error": f"{', '.join(fora)}: "
                                        + loc("not asked by this service")})
            prepare = ((lambda: provision(app, segredos, variaveis))
                       if action == "install" and (segredos or variaveis) else None)
            job = start_job(app, action, qh(app, *ACOES[action], "--apply"), lang, prepare)
        elif url.path == "/api/unit":
            unit, verbo = d.get("unit", ""), d.get("verb", "")
            if not unit_exists(unit):
                return self._json(400, {"error": loc("unknown unit")})
            if verbo not in VERBOS:
                return self._json(400, {"error": loc("unknown action")})
            # The verbs Quadlet units take (rule 4): never enable/disable.
            job = start_job(unit, verbo, ["systemctl", "--user", verbo, unit], lang)
        else:
            return self._json(404, {"error": "not found"})
        if job is None:
            return self._json(409, {"error": loc("another job is running")})
        return self._json(202, {"job": job.id})


# -- entry points ----------------------------------------------------------------

def serve(listen):
    host, _, porta = listen.rpartition(":")
    token, novo = load_token()
    Handler.token = token
    srv = ThreadingHTTPServer((host.strip("[]"), int(porta)), Handler)
    print(loc("the store is at") + f" http://{listen}", flush=True)
    print((loc("token created in") if novo else loc("the token is in"))
          + f" {token_file()}  ({loc('read it with')}: cat {token_file()})", flush=True)
    return srv


def selftest():
    """Login, the fences, and an install end to end — all against a sandbox."""
    import tempfile
    import urllib.error
    import urllib.request

    global PREFIX
    with tempfile.TemporaryDirectory() as tmp:
        PREFIX = tmp
        I.SANDBOX = True
        token, _ = load_token()
        Handler.token = token
        srv = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
        threading.Thread(target=srv.serve_forever, daemon=True).start()
        base = f"http://127.0.0.1:{srv.server_address[1]}"

        class SemRedirect(urllib.request.HTTPRedirectHandler):
            def redirect_request(self, *a, **kw):
                return None
        abrir = urllib.request.build_opener(SemRedirect).open

        def pedir(path, data=None, headers=None, metodo=None):
            req = urllib.request.Request(base + path, data=data, headers=headers or {},
                                         method=metodo)
            try:
                r = abrir(req, timeout=300)
                return r.status, r.headers, r.read()
            except urllib.error.HTTPError as e:
                return e.code, e.headers, e.read()

        try:
            st, h, _ = pedir("/")
            assert st == 303 and h["Location"] == "/login", (st, h)
            st, _, _ = pedir("/api/catalog")
            assert st == 401, st
            st, h, _ = pedir("/login", b"token=wrong")
            assert st == 303 and "e=1" in h["Location"], h["Location"]
            st, h, _ = pedir("/login", f"token={token}".encode())
            assert st == 303 and h["Location"] == "/", h
            biscoito = h["Set-Cookie"].split(";")[0]
            assert token not in biscoito
            assert "HttpOnly" in h["Set-Cookie"] and "SameSite=Strict" in h["Set-Cookie"]
            ok = {"Cookie": biscoito}
            api = {**ok, "X-QH-Store": "1", "Content-Type": "application/json"}

            st, h, corpo = pedir("/", headers=ok)
            assert st == 200 and b"app.js" in corpo and "script-src 'self'" in h["Content-Security-Policy"]
            st, _, corpo = pedir("/api/catalog?lang=pt", headers=ok)
            cat = json.loads(corpo)
            assert st == 200 and any(a["id"] == "homebox" for a in cat["apps"])

            st, _, corpo = pedir("/api/plan?app=homebox&action=install", headers=ok)
            assert st == 200 and json.loads(corpo)["rc"] == 0
            for ruim in ("../etc", "nao-existe", "homebox;id"):
                st, _, _ = pedir(f"/api/plan?app={ruim}&action=install", headers=ok)
                assert st == 400, (ruim, st)

            corpo = json.dumps({"app": "homebox", "action": "install"}).encode()
            st, _, _ = pedir("/api/run", corpo, ok)
            assert st == 403, st                      # no X-QH-Store: a <form> elsewhere
            st, _, _ = pedir("/api/run", json.dumps(
                {"app": "homebox", "action": "install", "secrets": {"x-y": "z"}}).encode(), api)
            assert st == 400, st                      # a secret the service does not ask
            st, _, _ = pedir("/api/run", json.dumps({"app": "homebox", "action": "purge"}).encode(), api)
            assert st == 400, st
            st, _, _ = pedir("/api/unit", json.dumps({"unit": "homebox", "verb": "enable"}).encode(), api)
            assert st == 400, st                      # rule 4: no enable/disable

            st, _, corpo = pedir("/api/run", corpo, api)
            assert st == 202, (st, corpo)
            job = json.loads(corpo)["job"]
            for _ in range(300):
                st, _, corpo = pedir(f"/api/job/{job}", headers=ok)
                estado = json.loads(corpo)
                if estado["rc"] is not None:
                    break
                time.sleep(0.5)
            assert estado["rc"] == 0, estado["output"]
            st, _, corpo = pedir("/api/catalog", headers=ok)
            hb = next(a for a in json.loads(corpo)["apps"] if a["id"] == "homebox")
            assert hb["installed"], "the install shows up in the catalog"

            # A `manual` secret goes through the same store_secret as the terminal
            st, _, corpo = pedir("/api/run", json.dumps(
                {"app": "vaultwarden", "action": "install",
                 "secrets": {"vaultwarden-admin-token": "$argon2id$teste"}}).encode(), api)
            assert st == 202, (st, corpo)
            job = json.loads(corpo)["job"]
            for _ in range(300):
                estado = json.loads(pedir(f"/api/job/{job}", headers=ok)[2])
                if estado["rc"] is not None:
                    break
                time.sleep(0.5)
            gravado = Path(tmp, ".config/containers/secrets/vaultwarden/admin-token.txt")
            assert estado["rc"] == 0 and gravado.read_text() == "$argon2id$teste", estado["output"]
            assert oct(gravado.stat().st_mode)[-3:] == "600"
        finally:
            srv.shutdown()
    print("store selftest: ok")


def main():
    qhui.argparse_ptbr()
    ap = argparse.ArgumentParser(description=loc("the web store over qh (install, update, remove, logs)"))
    ap.add_argument("--listen", default=os.environ.get("QH_STORE_LISTEN") or "127.0.0.1:8484",
                    help=loc("address and port to listen on") + " (QH_STORE_LISTEN)")
    ap.add_argument("--prefix", help=loc("use another home (to test without touching the real one)"))
    ap.add_argument("--selftest", action="store_true", help=loc("test the store against a sandbox"))
    a = ap.parse_args()
    if a.selftest:
        selftest()
        return 0
    global PREFIX
    PREFIX = a.prefix
    I.SANDBOX = bool(a.prefix)
    srv = serve(a.listen)
    try:
        srv.serve_forever()
    except KeyboardInterrupt:
        pass
    return 0


if __name__ == "__main__":
    sys.exit(main())
