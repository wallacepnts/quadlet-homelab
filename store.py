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
import shutil
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
_spec = importlib.util.spec_from_file_location("qh_updates", ROOT / "updates.py")
U = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(U)

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
    "no such backup of this service": "não há esse backup deste serviço",
    "not a .tar.gz": "não é um .tar.gz",
    "the upload was cut short": "o envio foi interrompido",
    "a backup with this name already exists; try again in a second":
        "já existe um backup com esse nome; tente de novo em um segundo",
    "not installed": "não instalado",
    "an upgrade edits the repository, which a sandbox does not have":
        "atualizar a versão edita o repositório, que um sandbox não tem",
    "a restore overwrites the data: type the service name to confirm":
        "restaurar sobrescreve os dados: digite o nome do serviço para confirmar",
    "no GitHub releases for this image": "sem releases no GitHub para esta imagem",
    "no GitHub repository known for this image": "nenhum repositório do GitHub conhecido para esta imagem",
    "GitHub did not answer (rate limit?)": "o GitHub não respondeu (limite de requisições?)",
    "no spaces: Volume= would cut the path there": "sem espaços: o Volume= cortaria o caminho ali",
    "the service refused this value:": "o serviço recusou este valor:",
    "secret stored": "secret gravado",
    "sandbox, not executed": "sandbox, não executado",
    "the web store over qh (install, update, remove, logs)":
        "a loja web sobre o qh (instalar, atualizar, remover, logs)",
    "address and port to listen on, comma-separated for several":
        "endereço e porta para escutar, separados por vírgula para vários",
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
ACOES = ("install", "update", "remove", "backup", "restore", "upgrade", "access")
BACKUP = re.compile(r"-\d{8}-\d{6}\.tar\.gz")     # what --backup names its archive after the app
VERBOS = {"start", "stop", "restart"}

PREFIX = None              # --prefix: the sandbox every qh call is pointed at
JOBS, JOB_LOCK = {}, threading.Lock()
# What is installed against what upstream released. Network-bound, and
# upstream does not move by the hour: kept on disk for a day, so a restart does
# not ask again either. A job re-asks for its own service only — what it
# changed is that service's installed side, never anyone's upstream.
UPDATES, UPDATES_LOCK, UPDATES_TTL = {"at": None, "rows": None}, threading.Lock(), 24 * 3600
# The jobs that change what is installed, and with it the comparison.
MUDA_VERSAO = {"install", "update", "upgrade", "remove"}


# -- the host, through qh --------------------------------------------------------

def qh(*args):
    """argv for install.py, carrying --prefix when there is one."""
    cmd = [sys.executable, str(ROOT / "install.py"), *args]
    return cmd + (["--prefix", PREFIX] if PREFIX else [])


def qh_env(lang):
    """The environment for qh; `lang` None keeps the host's own language.

    NO_COLOR: the output lands in a <pre>, where escape codes are noise.
    """
    env = {**os.environ, "NO_COLOR": "1"}
    if lang:
        env["QH_LANG"] = "pt_BR" if lang == "pt" else "en"
    return env


def catalog(lang="en"):
    r = subprocess.run(qh("--catalog"), capture_output=True, text=True,
                       env=qh_env(lang), cwd=ROOT, timeout=120)
    return json.loads(r.stdout)


def updates_file():
    return Path(PREFIX or Path.home()) / ".cache/quadlet-homelab/store-updates.json"


def ask_updates(*apps):
    """`qh-updates --host --json [APP...]`: rows, or None when it could not answer."""
    r = subprocess.run([sys.executable, str(ROOT / "updates.py"), *apps, "--host", "--json"],
                       capture_output=True, text=True, cwd=ROOT, env=qh_env("en"), timeout=300)
    if r.returncode != 0:
        return None
    return json.loads(r.stdout) if r.stdout.strip() else []


def save_updates():
    f = updates_file()
    f.parent.mkdir(parents=True, exist_ok=True)
    f.write_text(json.dumps({"at": UPDATES["at"], "rows": UPDATES["rows"]}))


def updates(force=False):
    """The comparison, from memory, then disk, then the network: {checked, rows}.

    Under --prefix there is no host to compare and the sandbox must not reach
    the network, so it answers empty.
    """
    if PREFIX:
        return {"checked": None, "rows": []}
    with UPDATES_LOCK:
        if UPDATES["rows"] is None and updates_file().is_file():
            try:
                UPDATES.update(json.loads(updates_file().read_text()))
            except (ValueError, OSError):
                pass          # unreadable cache: asked again below
        velho = UPDATES["at"] is None or time.time() - UPDATES["at"] > UPDATES_TTL
        if force or velho or UPDATES["rows"] is None:
            linhas = ask_updates()
            if linhas is not None:
                UPDATES.update(at=time.time(), rows=linhas)
                save_updates()
        return {"checked": UPDATES["at"], "rows": UPDATES["rows"] or []}


def refresh_updates(app):
    """Re-asks one service after a job changed what it runs, keeping every other row.

    A few lookups instead of all of them, and the time of the last full check
    stays what it was: the other rows are no newer than before.
    """
    if PREFIX or UPDATES["rows"] is None:
        return            # nothing cached yet: the next read asks for everything
    linhas = ask_updates(app)
    if linhas is None:
        return
    with UPDATES_LOCK:
        UPDATES["rows"] = [r for r in UPDATES["rows"] if r["app"] != app] + linhas
        save_updates()


NOTES, NOTES_TTL = {}, 3600     # repo -> (when, releases): the API quota is 60 an hour


def notes(unit):
    """The release notes between the installed tag of `unit` and upstream's.

    Only what GitHub publishes as releases: an image followed by registry tag
    or by another project's compose has none to read here, and says so.
    """
    host = Path(PREFIX or Path.home()) / ".config/containers/systemd"
    item = next((i for i in U.services(host) if i[1] == unit), None)
    vazio = {"repo": None, "url": None, "releases": []}
    if item is None:
        return {**vazio, "reason": loc("not installed")}
    _, _, imagem, override, _ = item
    if override and override.startswith(("registry", "compose:")):
        return {**vazio, "reason": loc("no GitHub releases for this image")}
    repo = U.github_repo(imagem, override)
    if not repo:
        return {**vazio, "reason": loc("no GitHub repository known for this image")}
    url = f"https://github.com/{repo}/releases"
    aqui = imagem.split("@")[0].rpartition(":")[2]
    linha = next((r for r in (UPDATES["rows"] or []) if r["unit"] == unit), None)
    teto = linha["there"] if linha and linha["bucket"] == "BEHIND" else None
    guardado = NOTES.get(repo)
    if not guardado or time.time() - guardado[0] > NOTES_TTL:
        lidas = U.fetch_releases(repo)
        if lidas is None:
            return {"repo": repo, "url": url, "releases": [],
                    "reason": loc("GitHub did not answer (rate limit?)")}
        NOTES[repo] = guardado = (time.time(), lidas)
    return {"repo": repo, "url": url, "releases": U.releases_between(guardado[1], aqui, teto)[:20]}


def login(app):
    """The credential `[login]` names, as `qh` prints it after an install."""
    s = I.Service(app, PREFIX)
    par = s.login()
    # Under --prefix there is no podman secret to read: the sandbox never
    # created one, and the real one with the same name is not the sandbox's.
    if not par or PREFIX or not I.secret_exists(par[1]):
        return {"available": False}
    user, secret = par
    senha = I.read_secret(secret)
    if user is None:
        user, _, senha = senha.partition(":")     # one secret holding user:password
    return {"available": True, "user": user, "password": senha}


def backup_dir():
    return Path(PREFIX or Path.home()) / ".local/share/quadlet-homelab/backups"


def backup_file(app, nome):
    """The archive `nome` of `app` in the backup folder, or None.

    A bare name in the exact shape --backup writes, never a path: `../` and
    another service's archive both fail the pattern, so nothing outside the
    folder and nothing of another app is reachable through it. qh --restore
    checks the contents belong to the service on top of this.
    """
    if not (nome or "").startswith(f"{app}-") or not BACKUP.fullmatch(nome[len(app):]):
        return None
    f = backup_dir() / nome
    return f if f.is_file() else None


def backups(app):
    d = backup_dir()
    if not d.is_dir():
        return []
    saida = []
    for f in d.iterdir():
        if backup_file(app, f.name):
            st = f.stat()
            saida.append({"file": f.name, "size": st.st_size, "date": int(st.st_mtime)})
    return sorted(saida, key=lambda x: x["file"], reverse=True)


def bump_cmd(app, aplicar):
    """qh-updates --bump for this one service: the repository's Image= and Pinned lines."""
    return [sys.executable, str(ROOT / "updates.py"), app, "--bump"] + (["--apply"] if aplicar else [])


def bump_vazio(saida):
    """Whether a bump dry-run found nothing to take (or held it back as a major)."""
    return not any(f in saida for f in ("BUMP (", U.PT.get("BUMP (", "BUMP (")))


def flags(app, action, arquivo=""):
    """The qh flags for an action, or None when it is not one (or its archive is missing)."""
    if action == "restore":
        f = backup_file(app, arquivo)
        return ["--restore", str(f)] if f else None
    if action in ("upgrade", "access"):
        return []           # not a single qh flag: built in the handler
    return {"install": [], "update": ["--update"], "remove": ["--remove"],
            "backup": ["--backup", "--out", str(backup_dir())]}.get(action)


def em_dia(saida):
    """Whether a dry-run said there is nothing to change.

    qh exits 0 either way, so the page could not tell "here is the plan" from
    "there is no plan" and offered a Confirm that did nothing. EM_DIA is the
    line qh prints for exactly that case, in either language.
    """
    return any(f in saida for f in (I.EM_DIA, I.PT.get(I.EM_DIA, I.EM_DIA)))


def service_dir(app):
    """The folder of a service the store may act on, or None."""
    if not NOME.match(app or ""):
        return None
    d = I.APPS / app
    return d if d.is_dir() and any(d.glob("*.container")) else None


def unit_exists(unit):
    return bool(NOME.match(unit or "")) and any(I.APPS.glob(f"*/{unit}.container"))


def chain(app):
    """The services an install of `app` needs first, in install order, then `app`.

    qh refuses an install whose network's owner is missing (79 of the 82 need
    tsdproxy's). Followed through: an owner may have owners of its own.
    """
    faltam, fila = [], [app]
    while fila:
        for dono, _ in I.missing_prereqs(I.Service(fila.pop(), PREFIX)):
            if dono not in faltam and dono != app:
                faltam.append(dono)
                fila.append(dono)
    return I.install_order(faltam) + [app]


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


def start_job(app, action, cmd, lang, prepare=None, entrada=None, refrescar=None):
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
            # One command, or several in order (an upgrade is a bump, then an
            # update): each runs only if the one before it succeeded.
            for i, uno in enumerate(cmd if isinstance(cmd[0], list) else [cmd]):
                if i:
                    job.write("\n" + "─" * 60 + "\n")
                # `entrada` is what the person typed where the terminal asks —
                # the app name a restore wants before overwriting. qh checks it.
                # The host's language, not the page's: qh translates the
                # dashboard labels it writes into the unit, so a unit installed
                # from a page in English read as "changed" to qh in Portuguese
                # ever after. Only read-only output follows the page.
                p = subprocess.Popen(uno, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                                     stdin=subprocess.PIPE if entrada else subprocess.DEVNULL,
                                     text=True, cwd=ROOT, env=qh_env(None))
                if entrada:
                    p.stdin.write(entrada + "\n")
                    p.stdin.close()
                for linha in p.stdout:
                    job.write(linha)
                rc = p.wait()
                if rc:
                    break
            # Refreshed BEFORE the exit code is published: the page asks for
            # the comparison as soon as it sees the job end, and it got the
            # pre-update answer — 26.11.0 installed, "new version 26.11.0".
            if action in MUDA_VERSAO:
                for x in (refrescar or [app]):
                    refresh_updates(x)
            job.rc = rc
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

    def _download(self, f):
        """Streams an archive: a backup can be gigabytes, so never read whole."""
        self.send_response(200)
        self.send_header("Content-Type", "application/gzip")
        self.send_header("Content-Length", str(f.stat().st_size))
        self.send_header("Content-Disposition", f'attachment; filename="{f.name}"')
        self.send_header("Cache-Control", "no-store")
        self.send_header("X-Content-Type-Options", "nosniff")
        self.end_headers()
        with f.open("rb") as fh:
            shutil.copyfileobj(fh, self.wfile, 1 << 20)

    def _upload(self, app):
        """An archive sent from the browser, saved under the name --backup would give it.

        Streamed to a hidden .part and renamed only once complete and gzip, so
        a cut upload never shows up in the list as something to restore.
        """
        n = int(self.headers.get("Content-Length") or 0)
        if n <= 0:
            return self._json(400, {"error": loc("not a .tar.gz")})
        d = backup_dir()
        d.mkdir(parents=True, exist_ok=True)
        nome = f"{app}-{time.strftime('%Y%m%d-%H%M%S')}.tar.gz"
        destino, parte = d / nome, d / f".{nome}.part"
        if destino.exists():
            return self._json(409, {"error": loc("a backup with this name already exists; "
                                                 "try again in a second")})
        restante = n
        with parte.open("wb") as fh:
            while restante:
                bloco = self.rfile.read(min(1 << 20, restante))
                if not bloco:
                    break
                fh.write(bloco)
                restante -= len(bloco)
        with parte.open("rb") as fh:
            gzip = fh.read(2) == b"\x1f\x8b"
        if restante or not gzip:
            parte.unlink()
            return self._json(400, {"error": loc("the upload was cut short") if restante
                                    else loc("not a .tar.gz")})
        parte.rename(destino)
        return self._json(201, {"file": nome})

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
        if url.path == "/api/updates":
            return self._json(200, updates(force=q.get("refresh") == "1"))
        if url.path == "/api/plan":
            app, action = q.get("app", ""), q.get("action", "")
            if not service_dir(app):
                return self._json(400, {"error": loc("unknown service")})
            extra = flags(app, action, q.get("file", ""))
            if extra is None:
                return self._json(400, {"error": loc("unknown action") if action not in ACOES
                                        else loc("no such backup of this service")})
            if action == "upgrade" and PREFIX:
                return self._json(400, {"error": loc("an upgrade edits the repository, "
                                                     "which a sandbox does not have")})
            cmds = [bump_cmd(app, False)] if action == "upgrade" else [qh(app, *extra)]
            if action == "install":
                # The dry-run of each service the install takes along, in order.
                cmds = [qh(x) for x in chain(app)]
            saida, rc = "", 0
            for i, c in enumerate(cmds):
                r = subprocess.run(c, capture_output=True, text=True, stdin=subprocess.DEVNULL,
                                   env=qh_env(lang), cwd=ROOT, timeout=300)
                saida += ("\n" + "─" * 60 + "\n" if i else "") + r.stdout + r.stderr
                rc = rc or r.returncode
            r = subprocess.CompletedProcess(cmds[-1], rc)
            vazio = bump_vazio(saida) if action == "upgrade" else em_dia(saida)
            return self._json(200, {"rc": r.returncode, "output": saida, "nothing": vazio})
        if url.path in ("/api/login", "/api/backups", "/api/backup/file"):
            app = q.get("app", "")
            if not service_dir(app):
                return self._json(400, {"error": loc("unknown service")})
            if url.path == "/api/login":
                return self._json(200, login(app))
            if url.path == "/api/backups":
                return self._json(200, {"dir": str(backup_dir()), "backups": backups(app)})
            f = backup_file(app, q.get("file", ""))
            if not f:
                return self._json(404, {"error": loc("no such backup of this service")})
            return self._download(f)
        if url.path == "/api/notes":
            unit = q.get("unit", "")
            if not unit_exists(unit):
                return self._json(400, {"error": loc("unknown unit")})
            return self._json(200, notes(unit))
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
        if url.path == "/login":
            try:
                corpo = self._body()
            except ValueError:
                return self._json(413, {"error": "too large"})
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
        if url.path == "/api/backup/upload":
            app = parse_qs(url.query).get("app", [""])[0]
            if not service_dir(app):
                return self._json(400, {"error": loc("unknown service")})
            return self._upload(app)
        try:
            d = json.loads(self._body() or b"{}")
        except ValueError:
            return self._json(400, {"error": "json"})
        lang = "pt" if d.get("lang") == "pt" else "en"

        if url.path == "/api/run":
            app, action = d.get("app", ""), d.get("action", "")
            if not service_dir(app):
                return self._json(400, {"error": loc("unknown service")})
            extra = flags(app, action, d.get("file", ""))
            if extra is None:
                return self._json(400, {"error": loc("unknown action") if action not in ACOES
                                        else loc("no such backup of this service")})
            segredos, variaveis = d.get("secrets") or {}, d.get("vars") or {}
            if not (isinstance(segredos, dict) and isinstance(variaveis, dict)
                    and all(isinstance(v, str) for v in [*segredos.values(), *variaveis.values()])):
                return self._json(400, {"error": "secrets/vars"})
            # An install takes the services it needs along, and the answers
            # for all of them: each name goes to the service that asks it.
            cadeia = chain(app) if action == "install" else [app]
            dono_s, dono_v = {}, {}
            for x in cadeia:
                manuais, nomes = asks(x)
                for n in manuais:
                    dono_s.setdefault(n, x)
                for n in nomes:
                    dono_v.setdefault(n, x)
            fora = sorted(set(segredos) - set(dono_s)) + sorted(set(variaveis) - set(dono_v))
            if fora:
                return self._json(400, {"error": f"{', '.join(fora)}: "
                                        + loc("not asked by this service")})

            def prepare():
                for x in cadeia:
                    if provision(x, {n: v for n, v in segredos.items() if dono_s[n] == x},
                                 {n: v for n, v in variaveis.items() if dono_v[n] == x}) is False:
                        return False
                return True
            if action != "install" or not (segredos or variaveis):
                prepare = None
            entrada = None
            if action == "restore":
                # The same guard the terminal has: the name, typed by the person.
                entrada = d.get("confirm", "")
                if not isinstance(entrada, str) or entrada.strip() != app:
                    return self._json(400, {"error": loc("a restore overwrites the data: "
                                                         "type the service name to confirm")})
            cmd = qh(app, *extra, "--apply")
            if action == "upgrade":
                # The version is taken in the repository first — it stays the
                # source, and the change is there to review and commit — then
                # brought to the host by the same --update as always.
                if PREFIX:
                    return self._json(400, {"error": loc("an upgrade edits the repository, "
                                                         "which a sandbox does not have")})
                cmd = [bump_cmd(app, True), qh(app, "--update", "--apply")]
            if action == "install" and len(cadeia) > 1:
                cmd = [qh(x, "--apply") for x in cadeia]
            if action == "access":
                # An exception for this service, then the update that writes it
                # into the unit. `default` drops it, back to the rule.
                modo = d.get("mode", "")
                if modo not in I.ACCESS_MODES + ("default",):
                    return self._json(400, {"error": loc("unknown action")})
                cmd = [qh("--set-access", modo, app)]
                if I.Service(app, PREFIX).installed():
                    cmd.append(qh(app, "--update", "--apply"))
            job = start_job(app, action, cmd, lang, prepare, entrada, refrescar=cadeia)
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
    """One server per address in `listen`, comma-separated.

    Several, so the store can stay on 127.0.0.1 for this machine and also
    answer on the host's tailnet address for tsdproxy — rather than 0.0.0.0,
    which would put it on the LAN as well.
    """
    token, novo = load_token()
    Handler.token = token
    servidores = []
    for endereco in (x.strip() for x in listen.split(",") if x.strip()):
        host, _, porta = endereco.rpartition(":")
        servidores.append(ThreadingHTTPServer((host.strip("[]"), int(porta)), Handler))
        print(loc("the store is at") + f" http://{endereco}", flush=True)
    print((loc("token created in") if novo else loc("the token is in"))
          + f" {token_file()}  ({loc('read it with')}: cat {token_file()})", flush=True)
    return servidores


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

            st, _, corpo = pedir("/api/updates", headers=ok)
            assert st == 200 and json.loads(corpo) == {"checked": None, "rows": []}, corpo

            # an install takes the network's owner along, and plans both
            assert chain("homebox") == ["tsdproxy", "homebox"], chain("homebox")
            assert chain("tsdproxy") == ["tsdproxy"]

            st, _, corpo = pedir("/api/plan?app=homebox&action=install", headers=ok)
            assert "tsdproxy" in json.loads(corpo)["output"], "the plan shows the owner too"
            assert st == 200 and json.loads(corpo)["rc"] == 0 and not json.loads(corpo)["nothing"]
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
            ts = next(a for a in json.loads(corpo)["apps"] if a["id"] == "tsdproxy")
            assert ts["installed"] and hb["requires"] == [], "and the owner came first"

            # access: an exception for one service, applied; `default` drops it
            for modo, esperado in (("local", "local"), ("default", None)):
                st, _, corpo = pedir("/api/run", json.dumps(
                    {"app": "homebox", "action": "access", "mode": modo}).encode(), api)
                assert st == 202, (st, corpo)
                job = json.loads(corpo)["job"]
                for _ in range(300):
                    estado = json.loads(pedir(f"/api/job/{job}", headers=ok)[2])
                    if estado["rc"] is not None:
                        break
                    time.sleep(0.5)
                assert estado["rc"] == 0, estado["output"]
                assert I.app_accesses(Path(tmp)).get("homebox") == esperado, modo
            st, _, _ = pedir("/api/run", json.dumps(
                {"app": "homebox", "action": "access", "mode": "lan"}).encode(), api)
            assert st == 400, st
            for caminho in ("/api/plan?app=homebox&action=upgrade", None):
                if caminho:
                    st, _, _ = pedir(caminho, headers=ok)
                else:
                    st, _, _ = pedir("/api/run", json.dumps(
                        {"app": "homebox", "action": "upgrade"}).encode(), api)
                assert st == 400, ("a sandbox never bumps the real repository", st)
            assert bump_vazio("nada a subir.") and not bump_vazio("SUBIR (1):  (dry-run)")
            assert em_dia(f"homebox: {I.EM_DIA}") and em_dia("homebox: já está em dia — nada a mudar")
            assert not em_dia("homebox: update, 5 steps  (dry-run)")

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

            def esperar(resposta):
                job = json.loads(resposta)["job"]
                for _ in range(300):
                    estado = json.loads(pedir(f"/api/job/{job}", headers=ok)[2])
                    if estado["rc"] is not None:
                        return estado
                    time.sleep(0.5)
                raise AssertionError("job never finished")

            # login: the sandbox has no podman secret to read, and says so
            st, _, corpo = pedir("/api/login?app=vaultwarden", headers=ok)
            assert st == 200 and json.loads(corpo) == {"available": False}, corpo

            # backup through qh --backup, listed, downloadable, and nothing else is
            st, _, corpo = pedir("/api/run", json.dumps({"app": "homebox", "action": "backup"}).encode(), api)
            assert st == 202 and esperar(corpo)["rc"] == 0
            lista = json.loads(pedir("/api/backups?app=homebox", headers=ok)[2])["backups"]
            assert len(lista) == 1 and lista[0]["file"].startswith("homebox-"), lista
            nome = lista[0]["file"]
            st, h, corpo = pedir(f"/api/backup/file?app=homebox&file={nome}", headers=ok)
            assert st == 200 and corpo[:2] == b"\x1f\x8b" and len(corpo) == lista[0]["size"]
            assert "attachment" in h["Content-Disposition"]
            for ruim in ("../../.config/quadlet-homelab/store-token", f"x{nome}", nome + ".bak"):
                st, _, _ = pedir(f"/api/backup/file?app=homebox&file={ruim}", headers=ok)
                assert st == 404, (ruim, st)
            st, _, _ = pedir(f"/api/backup/file?app=vaultwarden&file={nome}", headers=ok)
            assert st == 404, "one service's archive is not reachable through another"

            # upload: gzip only, and never under a name the list would show half-written
            up = {**ok, "X-QH-Store": "1", "Content-Type": "application/octet-stream"}
            time.sleep(1.1)                       # --backup names by the second
            st, _, _ = pedir("/api/backup/upload?app=homebox", b"not a tarball", up)
            assert st == 400, st
            st, _, corpo = pedir("/api/backup/upload?app=homebox", corpo, up)
            assert st == 201, (st, corpo)
            assert len(json.loads(pedir("/api/backups?app=homebox", headers=ok)[2])["backups"]) == 2
            assert not list(backup_dir().glob(".*.part")), "no partial file left behind"

            # restore: the plan first, then qh --restore with that archive
            st, _, corpo = pedir(f"/api/plan?app=homebox&action=restore&file={nome}", headers=ok)
            assert st == 200 and json.loads(corpo)["rc"] == 0, corpo
            st, _, _ = pedir("/api/plan?app=homebox&action=restore&file=../x", headers=ok)
            assert st == 400, st
            st, _, _ = pedir("/api/run", json.dumps(
                {"app": "homebox", "action": "restore", "file": nome}).encode(), api)
            assert st == 400, "a restore without the typed name is refused"
            st, _, corpo = pedir("/api/run", json.dumps(
                {"app": "homebox", "action": "restore", "file": nome,
                 "confirm": "homebox"}).encode(), api)
            assert st == 202, (st, corpo)
            estado = esperar(corpo)
            assert estado["rc"] == 0, estado["output"]

            # release notes: a unit that is not installed answers without the network
            st, _, corpo = pedir("/api/notes?unit=memos", headers=ok)
            assert st == 200 and json.loads(corpo)["releases"] == [], corpo
        finally:
            srv.shutdown()
    print("store selftest: ok")


def main():
    qhui.argparse_ptbr()
    ap = argparse.ArgumentParser(description=loc("the web store over qh (install, update, remove, logs)"))
    ap.add_argument("--listen", default=os.environ.get("QH_STORE_LISTEN") or "127.0.0.1:8484",
                    help=loc("address and port to listen on, comma-separated for several")
                    + " (QH_STORE_LISTEN)")
    ap.add_argument("--prefix", help=loc("use another home (to test without touching the real one)"))
    ap.add_argument("--selftest", action="store_true", help=loc("test the store against a sandbox"))
    a = ap.parse_args()
    if a.selftest:
        selftest()
        return 0
    global PREFIX
    PREFIX = a.prefix
    I.SANDBOX = bool(a.prefix)
    *outros, ultimo = serve(a.listen)
    for srv in outros:
        threading.Thread(target=srv.serve_forever, daemon=True).start()
    try:
        ultimo.serve_forever()
    except KeyboardInterrupt:
        pass
    return 0


if __name__ == "__main__":
    sys.exit(main())
