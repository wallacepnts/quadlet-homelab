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
import ssl
import urllib.error
import urllib.parse
import urllib.request
import configparser
import contextlib
import hashlib
import hmac
import importlib.util
import json
import os
import platform
import re
import secrets
import shutil
import subprocess
import sys
import tempfile
import threading
import time
from concurrent.futures import ThreadPoolExecutor
from http import cookies
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import parse_qs, urlparse

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))
import overrides as O  # noqa: E402
import qhui  # noqa: E402
import resources  # noqa: E402
import hostctl  # noqa: E402
import migrate  # noqa: E402
import ctrinfo  # noqa: E402
import alerts as A  # noqa: E402
import network as N  # noqa: E402
import svcwidgets as W  # noqa: E402
import imagepin  # noqa: E402
import manifest  # noqa: E402
import trials  # noqa: E402
import wsterm  # noqa: E402

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
    "nothing to do": "nada a fazer",
    "not running": "não está rodando",
    "this image is in use or an installed unit asks for it: not removed": "esta imagem está em uso ou uma unit instalada a pede: não foi removida",
    "your own .container saved": "o seu .container foi guardado",
    "back to the repository's .container": "de volta ao .container do repositório",
    "The service did not come up with this .container. Going back to the previous one:": "O serviço não subiu com este .container. Voltando ao anterior:",
    "confirm the warnings to go on": "confirme os avisos para continuar",
    "pick a time between a minute and a week from now": "escolha um horário entre um minuto e uma semana a partir de agora",
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
    "unknown file": "arquivo desconhecido",
    "marked deprecated, no install:": "marcado como descontinuado, sem instalação:",
    "invalid form": "formulário inválido",
    "no Quadlet generator here: only the form's own rules were checked":
        "sem o gerador do Quadlet aqui: só as regras do próprio formulário foram conferidas",
    "customization removed": "personalização removida", "written": "gravado",
    "restarted — it came up": "reiniciado — subiu",
    "The service did not come up with this customization. Going back to the previous one:":
        "O serviço não subiu com esta personalização. Voltando para a anterior:",
    "back as it was, and running": "voltou como estava, e está rodando",
    "back as it was, but it still does not start": "voltou como estava, mas ainda não sobe",
    "not a setting of this file, or not a single line":
        "não é uma opção deste arquivo, ou não é uma linha só",
    "set": "definido", "turned off": "desligado",
    "nothing to update": "nada para atualizar",
    "this deletes the data, secrets and .env: type the service name to confirm":
        "isto apaga os dados, os secrets e o .env: digite o nome do serviço para confirmar",
    "not a folder this form may use": "não é uma pasta que este formulário possa usar",
    "applying the customization of": "aplicando a personalização de",
    "this address takes a WebSocket": "este endereço espera um WebSocket",
    "a sandbox has no containers to enter": "um sandbox não tem containers para entrar",
    "too many consoles open": "consoles demais abertos",
    "too many log streams open": "muitos logs ao vivo abertos",
    "this service keeps no data to back up": "este serviço não guarda dados para copiar",
    "not a valid value for the type": "não é um valor válido para o tipo",
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
            "/app.js": "app.js", "/style.css": "style.css", "/fonts/jakarta.woff2": "fonts/jakarta.woff2"}
IMAGENS = {".svg": "image/svg+xml", ".png": "image/png", ".webp": "image/webp", ".jpg": "image/jpeg",
           ".jpeg": "image/jpeg", ".gif": "image/gif"}
ASSET = re.compile(r"^/assets/([a-z0-9][a-z0-9._-]*)/(icon\.(?:svg|png|webp|jpg)|screenshots/[A-Za-z0-9._-]+)$")
TIPOS = {".html": "text/html; charset=utf-8", ".js": "text/javascript; charset=utf-8",
         ".css": "text/css; charset=utf-8", ".woff2": "font/woff2"}
# Nothing inline, nothing from elsewhere: the logos and screenshots are served by this very server
# (/assets/...), and every string the page
# shows goes in through textContent, and this is the second fence behind that.
CSP = ("default-src 'none'; script-src 'self'; style-src 'self'; img-src 'self' data:; font-src 'self'; "
       "connect-src 'self'; form-action 'self'; frame-ancestors 'none'; base-uri 'none'")
ACOES = ("install", "update", "remove", "backup", "restore", "upgrade", "access", "trial-keep")
COOKIE = "qh_store"
NOME = re.compile(r"^[a-z0-9][a-z0-9._-]*$")
BACKUP = re.compile(r"-\d{8}-\d{6}\.tar\.gz")     # what --backup names its archive after the app
VERBOS = {"start", "stop", "restart", "force-stop", "force-restart"}

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


def pinning(app):
    """(some, all): whether some / every container of the service leaves its version to the host.

    Those are moved by `qh --update --latest`, on the host; the others still have a tag in the
    repository, and moving that is `qh-updates --bump`, a change to review and commit."""
    s = I.Service(app, PREFIX)
    stems = [u.stem for u in s.units if u.suffix == ".container"]
    tpls = imagepin.templates(s.ini)
    com = [x for x in stems if x in tpls]
    return bool(com), bool(stems) and len(com) == len(stems)


def upgrade_cmds(app, aplicar=True):
    """The commands of "Update to X" for one service: a bump in the repository for what keeps its tag
    there, and `--update --latest` for what leaves its version to the host."""
    algum, todos = pinning(app)
    return ([] if todos else [bump_cmd(app, aplicar)]) + [
        qh(app, "--update", *(["--latest"] if algum else []), *(["--apply"] if aplicar else []))]


def apps_with_update(lang="en"):
    """[(app, "upgrade"|"update")] for the installed services that have something to take: a newer
    release than what runs, or a repository that changed since the install."""
    cat = catalog(lang)
    linhas = {r["unit"]: r for r in updates()["rows"]}
    saida = []
    for a in cat["apps"]:
        us = [u for u in a["units"] if u["installed"]]
        if not us or any(u.get("stopped") for u in us) and all(u.get("stopped") for u in us):
            continue                    # nothing installed, or stopped on purpose: left as it is
        if any(linhas.get(u["unit"], {}).get("bucket") == "BEHIND" for u in us):
            algum, todos = pinning(a["id"])
            if PREFIX and not todos:
                continue                # a bump edits the repository, which a sandbox does not have
            saida.append((a["id"], "upgrade"))
        elif any(u.get("drift") for u in us):
            saida.append((a["id"], "update"))
    return saida


# -- alerts ----------------------------------------------------------------------

ALERT_LOCK, ALERT_EVERY = threading.Lock(), 300


def alert_home():
    return Path(PREFIX) if PREFIX else Path.home()


def alerts_tick(**kw):
    """One check of what is wrong, telling the ntfy topic (alerts.py); quiet when alerts are off."""
    cfg = A.load(alert_home())
    if not cfg["enabled"]:
        return []
    cat = catalog("en")["apps"]
    with ALERT_LOCK:
        return A.run(cat, updates()["rows"], alert_home(), cfg, **kw)


def alerts_loop():
    while True:
        time.sleep(ALERT_EVERY)
        try:
            alerts_tick()
        except Exception as e:        # a failed check must not end the watcher
            print(f"alerts: {type(e).__name__}: {e}", file=sys.stderr, flush=True)


def alert_backup_failed(job):
    """A backup job ended with an error: told at once, not at the next check."""
    cfg = A.load(alert_home())
    if not cfg["enabled"] or not cfg["kinds"].get("backup"):
        return
    ev = {"key": f"backup:{job.app}", "kind": "backup", "title": f"Backup of {job.app} failed",
          "message": f"The backup exited with code {job.rc}. See the history in the store."}
    with ALERT_LOCK:
        A.run([], [], alert_home(), cfg, extra=[ev])


def alerts_state(home=None):
    try:
        return json.loads(A.state_file(home or alert_home()).read_text())
    except (OSError, ValueError):
        return {}


# -- appearance -------------------------------------------------------------------

UI_DEFAULTS = {"theme": "system", "accent": "blue", "card": "shadow", "density": "comfortable",
               "bg_blur": 8, "bg_dim": 35, "icon_size": "medium", "depth": "flat"}
UI_CHOICES = {"theme": ("system", "light", "dark"),
              "accent": ("orange", "blue", "green", "teal", "purple", "pink", "red", "slate"),
              "card": ("shadow", "hairline"), "density": ("comfortable", "compact"),
              "icon_size": ("small", "medium", "large"), "depth": ("flat", "soft")}
UI_RANGES = {"bg_blur": (0, 20), "bg_dim": (0, 80)}
BG_MAX = 8 * 1024 * 1024
IMAGE_TYPES = {"png": "image/png", "jpg": "image/jpeg", "jpeg": "image/jpeg", "gif": "image/gif", "webp": "image/webp", "bmp": "image/bmp"}
BG_TYPES = {".png": "image/png", ".jpg": "image/jpeg", ".webp": "image/webp"}


def ui_dir():
    return Path(PREFIX or Path.home()) / ".config/quadlet-homelab"


def ui_settings():
    """The panel's appearance (theme, accent, background...), kept on the server so every browser sees the same."""
    try:
        d = json.loads((ui_dir() / "store-ui.json").read_text())
    except (OSError, ValueError):
        d = {}
    saida = dict(UI_DEFAULTS)
    saida.update({k: v for k, v in (d if isinstance(d, dict) else {}).items() if ui_clean({k: v})[1] == []})
    bg = ui_background()
    saida["background"] = bool(bg)
    saida["bg_version"] = int(bg.stat().st_mtime) if bg else None
    return saida


def ui_clean(d):
    """(the valid settings out of `d`, errors)."""
    ok, erros = {}, []
    for k, v in d.items():
        if k in UI_CHOICES:
            (ok.__setitem__(k, v) if v in UI_CHOICES[k] else erros.append(f"{k}: one of {', '.join(UI_CHOICES[k])}"))
        elif k in UI_RANGES:
            lo, hi = UI_RANGES[k]
            (ok.__setitem__(k, v) if isinstance(v, int) and not isinstance(v, bool) and lo <= v <= hi
             else erros.append(f"{k}: a whole number from {lo} to {hi}"))
        else:
            erros.append(f"unknown setting {k!r}")
    return ok, erros


def ui_save(d):
    ok, erros = ui_clean(d)
    if erros:
        return erros
    atual = {k: v for k, v in ui_settings().items() if k in UI_DEFAULTS}
    atual.update(ok)
    ui_dir().mkdir(parents=True, exist_ok=True)
    (ui_dir() / "store-ui.json").write_text(json.dumps(atual, indent=2) + "\n")
    return []


def ui_background():
    return next((ui_dir() / f"store-bg{e}" for e in BG_TYPES if (ui_dir() / f"store-bg{e}").is_file()), None)


def bg_kind(dados):
    """The extension of an image by its first bytes (never by what the browser claims), or None."""
    if dados.startswith(b"\x89PNG\r\n\x1a\n"):
        return ".png"
    if dados.startswith(b"\xff\xd8\xff"):
        return ".jpg"
    if dados[:4] == b"RIFF" and dados[8:12] == b"WEBP":
        return ".webp"
    return None


def ui_set_background(dados):
    """Saves the background image (or removes it, for an empty body). Returns an error, or None."""
    for e in BG_TYPES:
        (ui_dir() / f"store-bg{e}").unlink(missing_ok=True)
    if not dados:
        return None
    tipo = bg_kind(dados)
    if not tipo:
        return "not a PNG, JPEG or WebP image"
    ui_dir().mkdir(parents=True, exist_ok=True)
    (ui_dir() / f"store-bg{tipo}").write_bytes(dados)
    return None


# -- site monitor -----------------------------------------------------------------

MON, MON_LOCK, MON_TTL = {"at": 0.0, "data": {}}, threading.Lock(), 60


def probe(url, timeout=5):
    """{ok, status, ms} for one address: up when it answers at all below a 500 (a login page's 401 is up).

    Only reachability is asked, nothing is sent, so the certificate is not checked: a self-signed app is
    still an app that answers."""
    inicio = time.monotonic()
    ctx = ssl._create_unverified_context()
    status = None
    for metodo in ("HEAD", "GET"):
        try:
            req = urllib.request.Request(url, method=metodo, headers={"User-Agent": "qh-store-monitor"})
            with urllib.request.urlopen(req, timeout=timeout, context=ctx) as resp:
                status = resp.status
            break
        except urllib.error.HTTPError as e:
            status = e.code
            if e.code != 405 or metodo == "GET":      # some apps refuse HEAD: then a GET
                break
        except (urllib.error.URLError, OSError, ValueError):
            return {"ok": False, "status": None, "ms": None}
    return {"ok": status is not None and status < 500, "status": status, "ms": round((time.monotonic() - inicio) * 1000)}


def monitor(force=False, sondar=probe):
    """{app: {ok, status, ms}} of the installed apps that have one address to open, refreshed once a minute.

    It catches the container that is "healthy" while the app inside it does not answer. A sandbox has no
    apps running, so it answers empty."""
    if PREFIX and sondar is probe:
        return {}
    with MON_LOCK:
        if not force and time.time() - MON["at"] < MON_TTL:
            return MON["data"]
        alvos = {}
        for a in catalog("en")["apps"]:
            instaladas = {u["unit"] for u in a["units"] if u["installed"] and not u.get("stopped")}
            urls = [w.get("tailnet") or w.get("local") for w in a.get("web", []) if w["unit"] in instaladas]
            urls = [u for u in urls if u]
            if len(urls) == 1:
                alvos[a["id"]] = urls[0]
        with ThreadPoolExecutor(8) as ex:
            res = dict(zip(alvos, ex.map(sondar, alvos.values())))
        MON.update(at=time.time(), data=res)
        return res


# -- service widgets ---------------------------------------------------------------

SVC, SVC_LOCK, SVC_TTL = {"at": 0.0, "data": {}}, threading.Lock(), 60


def svc_home():
    return Path(PREFIX) if PREFIX else Path.home()


def svc_slots(apps):
    """[(app, widget, slot, unit, url)] of the widgets of the installed apps, with the address to call."""
    saida = []
    cfg = W.load(svc_home())
    for a in apps:
        ws = manifest.load(I.APPS / a["id"]).get("widgets") or []
        instaladas = {u["unit"] for u in a["units"] if u["installed"]}
        for w in ws if isinstance(ws, list) else []:
            if not isinstance(w, dict) or w.get("type") not in W.TYPES:
                continue
            unit = w.get("unit") or a.get("main_unit")
            if unit not in instaladas:
                continue
            web = next((x for x in a.get("web", []) if x["unit"] == unit), {})
            url = (cfg.get(W.slot(a["id"], w)) or {}).get("url") or web.get("tailnet") or web.get("local")
            saida.append((a["id"], w, W.slot(a["id"], w), unit, url))
    return saida


def svc_state(force=False, apps=None, get=W.http_get):
    """{app: [{type, unit, slot, auth, configured, url, fields | error}]}, read at most once a minute.

    The credential never leaves: what goes back is whether there is one, and the numbers."""
    with SVC_LOCK:
        if not force and apps is None and time.time() - SVC["at"] < SVC_TTL:
            return SVC["data"]
        apps = catalog("en")["apps"] if apps is None else apps
        cfg = W.load(svc_home())
        itens = []
        for app, w, slot, unit, url in svc_slots(apps):
            cred = cfg.get(slot) or {}
            itens.append(({"type": w["type"], "unit": unit, "slot": slot, "auth": list(W.AUTH[W.TYPES[w["type"]][0]]),
                           "configured": W.configured(w["type"], cred), "url": bool(url)}, app, cred, url))
        def ler(item):
            meta, _app, cred, url = item
            if not (meta["configured"] and url) or (PREFIX and get is W.http_get):
                return meta
            return {**meta, **W.read(meta["type"], url, cred, get)}
        with ThreadPoolExecutor(8) as ex:
            lidos = list(ex.map(ler, itens))
        saida = {}
        for (_, app, _, _), meta in zip(itens, lidos):
            saida.setdefault(app, []).append(meta)
        SVC.update(at=time.time(), data=saida)
        return saida


def svc_config(app, slot, valores):
    """Saves a widget's credential: only the keys its type takes (plus an address), an empty one kept as it was.
    Returns an error, or None."""
    pastas = {x[2]: x[1] for x in svc_slots([a for a in catalog("en")["apps"] if a["id"] == app])}
    if slot not in pastas:
        return "unknown widget"
    campos = W.AUTH[W.TYPES[pastas[slot]["type"]][0]]
    cfg = W.load(svc_home())
    atual = dict(cfg.get(slot) or {})
    if valores.get("clear"):
        atual = {}
    for k, v in valores.items():
        if k in ("clear", "lang"):
            continue
        if k not in campos and k != "url":
            return f"unknown field {k!r}"
        if not isinstance(v, str) or len(v) > 500:
            return f"{k}: text up to 500 characters"
        v = v.strip()
        if k == "url" and v and not re.fullmatch(r"https?://[^\s]+", v):
            return "url: an http:// or https:// address"
        if v:
            atual[k] = v
        elif k == "url":
            atual.pop("url", None)
    cfg[slot] = atual
    W.save(svc_home(), cfg)
    with SVC_LOCK:
        SVC["at"] = 0.0
    return None


def settings():
    """What the Settings screen shows: the access rule, who does not follow it, the tailnet."""
    home = Path(PREFIX) if PREFIX else None
    regra = I.saved_access(home)
    return {"access": regra or "tailnet", "default": regra is None,
            "drift": I.access_drift(regra or "tailnet", PREFIX), "tailnet": bool(I.find_tailnet()),
            "modes": list(I.ACCESS_MODES)}


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
    if action == "trial-keep":
        return ["--trial-keep"]
    return {"install": [], "update": ["--update"], "remove": ["--remove"],
            "backup": ["--backup", "--out", str(backup_dir())]}.get(action)


# -- history ---------------------------------------------------------------------

HISTORY_LOCK = threading.Lock()
HISTORY_CAP, HISTORY_KEEP, OUTPUT_CAP = 2 * 1024 * 1024, 1024 * 1024, 20000
# What qh prints after an install (show_secrets), in either language: the one
# place a credential reaches the output. The page shows it live, as the
# terminal does; the record on disk must not keep it.
CREDENCIAL = re.compile(r"^(\s*(?:user|password|usuário|usuario|senha)\s*:\s*)(.*)$", re.I | re.M)


def redact(texto):
    return CREDENCIAL.sub(lambda m: m.group(1) + "***", texto)


def history_file():
    return Path(PREFIX or Path.home()) / ".local/share/quadlet-homelab/store-history.jsonl"


def history_add(job):
    """Appends a finished job: what, when, how it ended, from where, and its output.

    One JSON line per job, private to the user (the output names paths and
    units), with the credentials masked and only the tail of a long output
    kept — an error is at the end. The file is compacted to its newest half
    when it passes 2 MB, so it cannot grow without a bound.
    """
    saida = redact("".join(job.out))
    if len(saida) > OUTPUT_CAP:
        saida = "…\n" + saida[-OUTPUT_CAP:]
    linha = json.dumps({"id": job.id, "app": job.app, "action": job.action, "unit": job.unit,
                        "start": round(job.started, 1), "end": round(time.time(), 1),
                        "rc": job.rc, "from": job.origem, "output": saida,
                        "rolled_back": "[rolled back]" in saida},
                       ensure_ascii=False)
    f = history_file()
    f.parent.mkdir(parents=True, exist_ok=True)
    with HISTORY_LOCK:
        fd = os.open(f, os.O_WRONLY | os.O_APPEND | os.O_CREAT, 0o600)
        with os.fdopen(fd, "a") as fh:
            fh.write(linha + "\n")
        if f.stat().st_size > HISTORY_CAP:
            mantidas, total = [], 0
            for velha in reversed(f.read_text().splitlines()):
                total += len(velha) + 1
                if total > HISTORY_KEEP:
                    break
                mantidas.append(velha)
            tmp = f.with_name(f.name + ".tmp")
            fd = os.open(tmp, os.O_WRONLY | os.O_CREAT | os.O_TRUNC, 0o600)
            with os.fdopen(fd, "w") as fh:
                fh.write("\n".join(reversed(mantidas)) + "\n")
            tmp.replace(f)


def history_read(app=None, limite=100):
    """Entries newest first, without their output; `app` narrows to one service."""
    f = history_file()
    if not f.is_file():
        return []
    saida = []
    for linha in reversed(f.read_text().splitlines()):
        try:
            e = json.loads(linha)
        except ValueError:
            continue              # a torn last line is a lost entry, not a broken page
        if app and e.get("app") != app:
            continue
        e.pop("output", None)
        saida.append(e)
        if len(saida) >= limite:
            break
    return saida


def history_get(id_):
    f = history_file()
    if f.is_file():
        for linha in reversed(f.read_text().splitlines()):
            try:
                e = json.loads(linha)
            except ValueError:
                continue
            if e.get("id") == id_:
                return e
    return None


# -- links to the project ---------------------------------------------------------

REPO = re.compile(r"[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+")


def image_path(imagem):
    """An image reference without its digest and tag: `ghcr.io/owner/name`."""
    ref = imagem.split("@")[0]
    return ref.rpartition(":")[0] if ":" in ref.split("/")[-1] else ref


def repo_url(imagem, override):
    """The project's repository, only where something reliable says which it is.

    The `[upstream]` override is the author naming it. Without one — and for
    `-` and `registry`, which only say how to compare versions, not where the
    project lives — only a registry that mirrors the repository's own path says
    it too (ghcr.io, lscr.io, GitLab's). A Docker Hub name proves nothing:
    `vaultwarden/server` is built from `dani-garcia/vaultwarden`, and a guess
    would be a link to a 404.
    """
    if override and override != "-" and not override.startswith("registry"):
        alvo = override[len("compose:"):].split(":")[0] if override.startswith("compose:") else override
        return f"https://github.com/{alvo}" if REPO.fullmatch(alvo) else None
    partes = image_path(imagem).split("/")
    if partes[0] == "ghcr.io" and len(partes) >= 3:
        return f"https://github.com/{partes[1]}/{partes[2]}"
    if partes[0] == "lscr.io" and len(partes) >= 3:
        return f"https://github.com/{partes[1]}/docker-{partes[2]}"
    if partes[0] == "registry.gitlab.com" and len(partes) == 3:
        return f"https://gitlab.com/{partes[1]}/{partes[2]}"
    return None


def image_page(imagem):
    """The registry's own page for an image, or None for a registry with no such page."""
    p = image_path(imagem).split("/")
    if p[0] == "docker.io" and len(p) == 3:
        return (f"https://hub.docker.com/_/{p[2]}" if p[1] == "library"
                else f"https://hub.docker.com/r/{p[1]}/{p[2]}")
    if p[0] == "ghcr.io" and len(p) >= 3:
        return f"https://github.com/{p[1]}/{p[2]}/pkgs/container/{p[-1]}"
    if p[0] == "quay.io" and len(p) == 3:
        return f"https://quay.io/repository/{p[1]}/{p[2]}"
    return None


def remote_https(remoto):
    """https://github.com/<owner>/<repo> from a git remote in either its ssh or https form."""
    m = re.fullmatch(r"(?:git@github\.com:|https://github\.com/)([\w.-]+/[\w.-]+?)(?:\.git)?/?", remoto.strip())
    return f"https://github.com/{m.group(1)}" if m else None


def recipe_base():
    """This repository's page on GitHub, from the clone's own origin, or None."""
    if "base" not in RECIPE:
        r = subprocess.run(["git", "-C", str(ROOT), "remote", "get-url", "origin"],
                           capture_output=True, text=True)
        RECIPE["base"] = remote_https(r.stdout) if r.returncode == 0 else None
    return RECIPE["base"]


RECIPE = {}


def repo_from_field(valor):
    """The project's page from `[store] repo`: `owner/repo` on GitHub, or a full https URL."""
    v = (valor or "").strip().rstrip("/")
    if REPO.fullmatch(v):
        return f"https://github.com/{v}"
    return v if re.fullmatch(r"https://[A-Za-z0-9.-]+/[A-Za-z0-9._/-]+", v) else None


def issues_url(repo):
    """Where a project takes bug reports, for the hosts whose address is known; else None."""
    host = repo.split("/")[2] if repo.startswith("https://") else ""
    if host in ("github.com", "codeberg.org"):
        return repo + "/issues"
    if host == "gitlab.com":
        return repo + "/-/issues"
    return None


def docs_url(app):
    """The documentation link the service's `app.json` names (`docs`), or None."""
    v = (manifest.load(I.APPS / app).get("docs") or "").strip()
    return v if v.startswith("https://") else None


def same_page(a, b):
    """Whether two addresses are the same page, ignoring a #fragment and a trailing slash."""
    norm = lambda u: u.split("#")[0].rstrip("/").lower()
    return norm(a) == norm(b)


def links(app):
    """[{kind, url}]: the project, its documentation and issues, releases, image page, and this repo's recipe.

    The project's repository comes from `[store] repo` when the unit's own image would point
    at the wrong place (the registry path is not always the repository's); else from the
    sources `repo_url` trusts."""
    s = I.Service(app, PREFIX)
    principal = s.main_unit()
    saida = []
    repo = repo_from_field(s.ini.get("store", "repo", fallback=None)) if s.ini.has_section("store") else None
    imagem = ""
    if principal:
        imagem = next((v for k, v in I.directives_of(principal) if k == "Image"), "")
        override = s.ini.get("upstream", principal.stem, fallback=None) if s.ini.has_section("upstream") else None
        repo = repo or repo_url(imagem, override)
    if repo:
        saida.append({"kind": "repo", "url": repo})
    docs = docs_url(app)
    if docs and not (repo and same_page(docs, repo)):      # a README anchor of the repo is the repo
        saida.append({"kind": "docs", "url": docs})
    if repo and issues_url(repo):
        saida.append({"kind": "issues", "url": issues_url(repo)})
    if repo and repo.startswith("https://github.com/"):
        saida.append({"kind": "releases", "url": repo + "/releases"})
    pagina = image_page(imagem) if imagem else None
    if pagina:
        saida.append({"kind": "image", "url": pagina})
    base = recipe_base()
    if base:
        saida.append({"kind": "recipe", "url": f"{base}/tree/main/apps/{app}"})
    return saida


# -- customizing a unit: the drop-in ---------------------------------------------------

def systemd_dir():
    return Path(PREFIX or Path.home()) / ".config/containers/systemd"


def installed_unit(unit):
    """The unit's installed file, flat or in its folder, or None."""
    return next(iter(systemd_dir().rglob(f"{unit}.container")), None)


def listening():
    """{(port, proto)} bound on the host now. Empty in a sandbox: it has no host to ask."""
    if PREFIX:
        return set()
    saida = set()
    for linha in (I.run_read(["ss", "-H", "-ltun"]) or "").splitlines():
        c = linha.split()
        m = re.search(r":(\d+)$", c[4]) if len(c) >= 5 else None
        if m:
            saida.add((int(m.group(1)), "udp" if c[0].startswith("udp") else "tcp"))
    return saida


def volume_roots():
    """Where a NEW volume may live. The containers' own folder, the folders the person
    wrote in `store-roots`, and the ones the repository's units already ask them for
    (${MEDIA_DATA_DIR}): they chose those, so the store trusts them."""
    casa = Path(PREFIX or Path.home())
    raizes = [str(casa / ".config/containers/volumes")]
    arq = casa / ".config/quadlet-homelab/store-roots"
    if arq.is_file():
        raizes += [l.strip() for l in arq.read_text().splitlines()
                   if l.strip().startswith("/")]
    if not PREFIX:
        for u in systemd_dir().rglob("*.container"):
            for k, v in I.directives_of(u):
                if k == "Volume":
                    for nome in re.findall(r"\$\{([A-Za-z_][A-Za-z0-9_]*)\}", v.split(":")[0]):
                        if I.manager_var(nome):
                            raizes.append(I.manager_var(nome))
    return list(dict.fromkeys(raizes))


DIRS_CAP = 500


def host_value(path):
    """A path as the unit file should carry it: `%h/...` under the home, the plain path elsewhere."""
    casa = str(Path(PREFIX or Path.home()))
    return "%h" + path[len(casa):] if path == casa or path.startswith(casa + "/") else path


def list_dirs(path=""):
    """The folders the volume picker may show: {path, value, shown, parent, dirs: [{name, path}]}.

    Only inside the permitted roots (the same list the form validates against), by real path, so a
    symlink cannot lead out of them; a folder entry that is itself a symlink is not followed. With no
    path it is the roots themselves. Hidden folders are left out, and so are files: it is for choosing
    where a volume lives, not for browsing."""
    raizes = [os.path.realpath(r) for r in volume_roots()]
    if not path:
        return {"path": "", "value": "", "shown": "", "parent": None,
                "dirs": [{"name": host_value(r).replace("%h", "~"), "path": r} for r in raizes if os.path.isdir(r)]}
    real = O.resolve_host(path, Path(PREFIX or Path.home()), I.manager_var)
    if not real or not real.startswith("/"):
        raise ValueError(loc("not a folder this form may use"))
    real = os.path.realpath(real)
    dentro_de_raiz = real in raizes
    if not (dentro_de_raiz or O.under(real, raizes)) or not os.path.isdir(real):
        raise ValueError(loc("not a folder this form may use"))
    dirs = []
    try:
        with os.scandir(real) as it:
            for e in sorted(it, key=lambda x: x.name.lower()):
                if len(dirs) >= DIRS_CAP:
                    break
                if e.name.startswith(".") or not e.is_dir(follow_symlinks=False):
                    continue
                dirs.append({"name": e.name, "path": os.path.join(real, e.name)})
    except OSError:
        pass
    pai = os.path.dirname(real)
    return {"path": real, "value": host_value(real), "shown": host_value(real).replace("%h", "~"),
            "parent": pai if (not dentro_de_raiz and (pai in raizes or O.under(pai, raizes))) else None,
            "at_root": dentro_de_raiz, "dirs": dirs}


def cgroup_limits():
    """Whether this user's systemd delegates the memory and CPU controllers.

    Without them `--memory` and `--cpu-shares` stop the container from starting
    (`memory.swap.max: no such file or directory`), so the form does not offer them."""
    uid = os.getuid()
    # QH_CGROUP_CONTROLLERS names a file standing in for the real one, so a host that does not
    # delegate them can still exercise the form (the tests do).
    f = Path(os.environ.get("QH_CGROUP_CONTROLLERS")
             or f"/sys/fs/cgroup/user.slice/user-{uid}.slice/user@{uid}.service/cgroup.controllers")
    try:
        c = f.read_text().split()
    except OSError:
        return {"memory": False, "cpu": False}
    return {"memory": "memory" in c, "cpu": "cpu" in c}


def custom_context(unit, efetivo):
    """What validation needs to know about this host, for this unit."""
    try:
        floor = int(Path("/proc/sys/net/ipv4/ip_unprivileged_port_start").read_text())
    except (OSError, ValueError):
        floor = 1024
    em_uso = {}
    for outra in systemd_dir().rglob("*.container"):
        if outra.stem == unit:
            continue
        listas, _ = O.merged(O.base_of(outra.read_text()), O.read_override(outra))
        for raw in listas["ports"]:
            it = O.parse_item("ports", raw)
            if not it.get("opaque"):
                em_uso[(it["host"], it["proto"])] = outra.stem
    proprias = {(i["host"], i["proto"]) for i in O.describe(efetivo[0])["ports"] if not i.get("opaque")}
    try:
        mem_total = int(re.search(r"MemTotal:\s+(\d+)", Path("/proc/meminfo").read_text()).group(1)) * 1024
    except (OSError, AttributeError, ValueError):
        mem_total = 0
    return O.Contexto(Path(PREFIX or Path.home()), roots=volume_roots(), floor=floor, em_uso=em_uso,
                      escutando=listening() - proprias, var=I.manager_var, limits_ok=cgroup_limits(),
                      mem_total=mem_total, ncpu=os.cpu_count() or 0)


def unit_source(unit, pre=False):
    """(installed path or None, the unit's text, its drop-in text or None).

    The text is the installed file's. With `pre` and no installed file it is what `qh` WOULD write
    — the repository's unit rendered for the access rule in force — which is what a customization
    made before the install has to be measured against."""
    p = installed_unit(unit)
    if p is not None:
        return p, p.read_text(), O.read_override(p)
    if pre and unit_exists(unit):
        caminho = next(I.APPS.glob(f"*/{unit}.container"))
        sv = I.Service(caminho.parent.name, PREFIX)
        modo, href = I.effective_access(sv)
        return None, I.unit_bytes(sv.source(caminho.name), modo, href).decode(), None
    raise LookupError(loc("not installed"))


def custom_state(unit, pre=False):
    """What the Customize screen starts from: the unit, what it carries now, and the rules."""
    p, unit_texto, texto = unit_source(unit, pre)
    base = O.base_of(unit_texto)
    efetivo = O.merged(base, texto)
    gravada = O.recorded_base(texto) if texto else None
    casa = str(Path(PREFIX or Path.home()))
    destino = O.dropin_path(p or systemd_dir() / f"{unit}.container")
    return {"unit": unit, "file": str(destino).replace(casa, "~"), "pre": p is None,
            "override": texto is not None, "text": texto,
            "base_changed": bool(gravada and gravada != O.base_hash(base)),
            "base": O.describe(base[0]), "base_restart": base[1],
            "effective": O.describe(efetivo[0]), "restart": efetivo[1],
            "roots": [r.replace(casa, "~") for r in volume_roots()], "caps_ok": list(O.CAPS_OK),
            "restarts": list(O.RESTARTS), "quadlet": O.quadlet_binary() is not None,
            "unit_source": (unit_custom_file(unit).read_text() if unit_custom_file(unit) and unit_custom_file(unit).is_file()
                            else unit_repo_text(unit)),
            "repo_text": unit_repo_text(unit), "custom_unit": bool(unit_custom_file(unit) and unit_custom_file(unit).is_file()),
            "installed_text": unit_texto if p is not None else None,
            "limits": cgroup_limits(), "limit_values": O.merged_limits(unit_texto, texto)}


# -- the unit as text: see it, rewrite it, or install the person's own -------------------------------
UNIT_MAX = 64 * 1024
RISKY = (("Container", "SecurityLabelDisable", "true", "desliga o rótulo SELinux do container"),
         ("Container", "Network", "host", "usa a rede do host, sem isolamento"),
         ("Container", "UserNS", "host", "usa o espaço de usuários do host"),
         ("Container", "PodmanArgs", None, "passa argumentos soltos ao podman"),
         ("Container", "AutoUpdate", None, "baixa imagens sozinho (regra 9: nada atualiza sozinho)"))
SERVICE_EXEC = ("ExecStart", "ExecStartPre", "ExecStartPost", "ExecStop", "ExecStopPost", "ExecReload")


def unit_pasta(unit):
    c = next(I.APPS.glob(f"*/{unit}.container"), None)
    return c.parent.name if c else None


def unit_repo_text(unit):
    """The repository's `.container` as written: what the editor starts from when the person has not rewritten it."""
    c = next(I.APPS.glob(f"*/{unit}.container"), None)
    return c.read_text() if c else ""


def unit_custom_file(unit):
    pasta = unit_pasta(unit)
    return I.custom_unit_file(Path(PREFIX or Path.home()), pasta, f"{unit}.container") if pasta else None


def unit_risks(texto):
    """The set of things in `texto` that run commands on the host, widen what the container may do or leave the rules."""
    secoes = O.parse_sections(texto)
    achados = set()
    for sec, chave, valor, porque in RISKY:
        for k, v in secoes.get(sec, []):
            if k == chave and (valor is None or v.lower() == valor):
                achados.add(f"{chave}={v}: {porque}")
    for k, v in secoes.get("Container", []):
        if k == "PodmanArgs" and "--privileged" in v:
            achados.add(f"PodmanArgs={v}: roda com --privileged, acesso total ao host")
    for k, v in secoes.get("Service", []):
        if k in SERVICE_EXEC:
            achados.add(f"{k}=: executa um comando no host, como o seu usuário")
    for k, v in secoes.get("Container", []):
        if k == "AddCapability":
            for c in re.split(r"[\s,]+", v):
                c = c.upper().removeprefix("CAP_")
                if c and c not in O.CAPS_OK and c != "ALL":
                    achados.add(f"AddCapability={c}: fora da lista curta ({', '.join(O.CAPS_OK[:4])}…)")
        elif k == "Volume":
            host = v.split(":")[0]
            if host.startswith("/") and not O.under(host, volume_roots()) and host not in ("/etc/localtime",):
                achados.add(f"Volume={host}: pasta do host fora das permitidas")
        elif k == "Image" and re.search(r":(latest|main|master|stable)$", v):
            achados.add(f"Image={v}: tag flutuante (regra 9)")
    return achados


def quadlet_check_text(unit, texto):
    """(ok or None, problems): the host's own generator on a scratch copy of the app's units with `texto` as this one."""
    binario = O.quadlet_binary()
    if not binario or not unit_pasta(unit):
        return None, []
    with tempfile.TemporaryDirectory() as tmp:
        copia = Path(tmp) / "units"
        copia.mkdir()
        # Every unit of the repository, so what this one names (a network of another app) is there to be found.
        for f in [*I.APPS.glob("*/*.container"), *I.APPS.glob("*/*.network")]:
            shutil.copy2(f, copia / f.name)
        (copia / f"{unit}.container").write_text(texto)
        r = subprocess.run([binario, "-dryrun", "-user"], capture_output=True, text=True,
                           env={**os.environ, "QUADLET_UNIT_DIRS": str(copia)}, timeout=60)
    problemas = [re.sub(r"^quadlet-generator\[\d+\]:\s*", "", l).replace(str(copia), "")
                 for l in r.stderr.splitlines() if f'"{unit}.container"' in l and "converting" in l]
    return (not problemas), problemas


def unit_review(unit, texto):
    """{errors, warnings, changed}: what blocks saving `texto` as the unit, what only deserves a second look
    (what it adds against the repository's own file), and whether it differs from that file at all."""
    erros = []
    if not isinstance(texto, str) or not texto.strip():
        return {"errors": ["o texto está vazio"], "warnings": [], "changed": False}
    if len(texto.encode()) > UNIT_MAX or "\0" in texto:
        erros.append(f"o arquivo passa de {UNIT_MAX // 1024} KB ou tem bytes nulos")
    secoes = O.parse_sections(texto) if not erros else {}
    if not erros and not any(k == "Image" and v for k, v in secoes.get("Container", [])):
        erros.append("falta [Container] com Image=")
    if not erros:
        ok, problemas = quadlet_check_text(unit, texto)
        erros += [f"quadlet: {x}" for x in problemas]
    repo = unit_repo_text(unit)
    novos = sorted(unit_risks(texto) - unit_risks(repo)) if not erros else []
    return {"errors": erros, "warnings": novos, "changed": texto.strip() != repo.strip()}


def apply_custom_unit(app, unit, texto):
    """Keeps `texto` as the person's own `.container` (None goes back to the repository's), has qh write it where systemd
    reads it, and puts the previous one back if the service no longer comes up. Runs inside a job."""
    arq = I.custom_unit_file(Path(PREFIX or Path.home()), app, f"{unit}.container")
    anterior = arq.read_text() if arq.is_file() else None

    def guardar(t):
        if t is None:
            arq.unlink(missing_ok=True)
            with contextlib.suppress(OSError):
                arq.parent.rmdir()
        else:
            arq.parent.mkdir(parents=True, exist_ok=True)
            arq.write_text(t)

    def atualizar():
        r = subprocess.run(qh(app, "--update", "--apply"), capture_output=True, text=True, cwd=ROOT, env=qh_env(None))
        print((r.stdout + r.stderr).rstrip())
        return r.returncode == 0

    ativo_antes = PREFIX or subprocess.run(["systemctl", "--user", "is-active", f"{unit}.service"], capture_output=True).returncode == 0
    guardar(texto)
    print(("  " + loc("your own .container saved")) if texto is not None else ("  " + loc("back to the repository's .container")))
    if atualizar() and (PREFIX or not ativo_antes or systemctl("is-active", f"{unit}.service")):
        return True
    print("\n" + loc("The service did not come up with this .container. Going back to the previous one:"))
    guardar(anterior)
    atualizar()
    return False


def unit_drift_diff(unit):
    """{unit, changed, diff}: the installed `.container` against what `qh --update` would write now (the repository's, or the
    person's own, rendered for the access rule the unit was installed with), as a unified diff. Empty when they agree."""
    import difflib
    p = installed_unit(unit)
    pasta = unit_pasta(unit)
    if p is None or not pasta:
        raise LookupError(loc("not installed"))
    fonte = I.Service(pasta, PREFIX).source(p.name)
    lido = I.installed_access(p, fonte)
    modo = lido[0] if lido and lido[0] else "tailnet"
    href = lido[1] if lido and lido[1] is not None else modo == "local"
    novo = I.unit_bytes(fonte, modo, href).decode("utf-8", "replace")
    linhas = list(difflib.unified_diff(p.read_text().splitlines(), novo.splitlines(), "installed", "repository", lineterm="", n=2))
    return {"unit": unit, "changed": bool(linhas), "diff": "\n".join(linhas)}


def clean_config(config):
    """The form's payload as items of the right types, or ValueError."""
    if not isinstance(config, dict):
        raise ValueError("config")
    saida = {}
    for grupo, _ in O.GROUPS:
        itens = config.get(grupo)
        if itens is None:
            continue
        if not isinstance(itens, list) or len(itens) > 200:
            raise ValueError(grupo)
        limpos = []
        for i in itens:
            if not isinstance(i, dict):
                raise ValueError(grupo)
            if i.get("opaque") or "raw" in i:
                limpos.append({"raw": str(i.get("raw", "")), "opaque": True})
            elif grupo == "ports":
                if i.get("proto") not in ("tcp", "udp"):
                    raise ValueError("proto")
                limpos.append({"bind": str(i.get("bind") or ""), "host": int(i["host"]),
                               "container": int(i["container"]), "proto": i["proto"]})
            elif grupo == "volumes":
                limpos.append({"host": str(i["host"]), "container": str(i["container"]),
                               "label": str(i.get("label") or ""), "ro": bool(i.get("ro")),
                               "extra": [str(x) for x in (i.get("extra") or [])]})
            elif grupo == "env":
                limpos.append({"key": str(i["key"]), "value": str(i.get("value", ""))})
            elif grupo == "devices":
                limpos.append({"path": str(i["path"])})
            else:
                limpos.append({"name": str(i["name"]).upper().removeprefix("CAP_")})
        saida[grupo] = limpos
    restart = config.get("restart")
    if restart is not None and not isinstance(restart, str):
        raise ValueError("restart")
    lim = config.get("limits")
    if lim is not None:
        if not isinstance(lim, dict) or not all(isinstance(lim.get(k, ""), str) for k in ("memory", "cpus")):
            raise ValueError("limits")
        saida["limits"] = {"memory": lim.get("memory", ""), "cpus": lim.get("cpus", "")}
    return saida, (restart or None)


def pre_check(unit, unit_texto, texto):
    """quadlet_check for a unit that is not installed yet: a scratch tree with the rendered unit in it.

    The tree is the host's own (so units it names resolve) plus the repository's `.network` files,
    since the owner of a network may be installed in the same run."""
    import shutil
    with tempfile.TemporaryDirectory() as tmp:
        arvore = Path(tmp, "systemd")
        if systemd_dir().is_dir():
            shutil.copytree(systemd_dir(), arvore, ignore=shutil.ignore_patterns("*.tmp"))
        arvore.mkdir(exist_ok=True)
        for rede in I.APPS.glob("*/*.network"):
            if not any(arvore.rglob(rede.name)):
                shutil.copy(rede, arvore / rede.name)
        alvo = arvore / f"{unit}.container"
        alvo.write_text(unit_texto)
        return O.quadlet_check(arvore, alvo, texto)


def custom_plan(unit, config, pre=False):
    """{text, errors, warnings, generated, changed}: what saving would write, and whether it holds.

    The form's own rules first, then the host's Quadlet generator on a scratch copy —
    which knows the keys but not the values, so the first is not optional."""
    p, unit_texto, drop = unit_source(unit, pre)
    try:
        desejado, restart = clean_config(config)
    except (ValueError, KeyError, TypeError) as e:
        return {"text": None, "errors": [f"{loc('invalid form')}: {e}"], "warnings": [], "generated": "",
                "changed": False}
    base = O.base_of(unit_texto)
    ctx = custom_context(unit, O.merged(base, drop))
    texto, erros, avisos = O.validate_and_render(base, desejado, restart, ctx, propria=unit,
                                                 base_limits=O.limits_in(O.parse_sections(unit_texto)))
    gerado = ""
    if not erros:
        ok, mensagens, gerado = (O.quadlet_check(systemd_dir(), p, texto) if p is not None
                                 else pre_check(unit, unit_texto, texto))
        if ok is False:
            erros += mensagens
        elif ok is None:
            avisos.append(loc("no Quadlet generator here: only the form's own rules were checked"))
    return {"text": texto, "errors": erros, "warnings": avisos, "generated": gerado,
            "changed": texto is not None, "desired": desejado, "base_text": unit_texto}


def new_volume_dirs(unit_texto, plano):
    """The host folders of volumes the person ADDED, which apply_override creates.

    Only the ones the unit did not already carry; the validation has by now
    confirmed each sits inside a permitted root, so mkdir cannot reach elsewhere."""
    antigos = {O.canon("volumes", r) for r in O.base_of(unit_texto)[0]["volumes"]}
    casa = Path(PREFIX or Path.home())
    saida = []
    for item in plano["desired"].get("volumes", []):
        if item.get("opaque") or O.render_item("volumes", item) in antigos:
            continue
        real = O.resolve_host(item["host"], casa, I.manager_var)
        if real:
            saida.append(real)
    return saida


def systemctl(*args, tempo=300):
    r = subprocess.run(["systemctl", "--user", *args], capture_output=True, text=True, timeout=tempo)
    if r.returncode and (r.stdout or r.stderr).strip():
        print((r.stderr or r.stdout).strip())
    return r.returncode == 0


def apply_override(unit, texto, novos_volumes=()):
    """Writes (or removes) the drop-in, reloads, restarts — and goes back if the service does not come up.

    A volume that does not exist, a port the app refuses: the person would be left
    with a broken service and a form. Instead the previous state is restored and the
    reason is printed. Runs inside a job, so print() is the job's output."""
    p = installed_unit(unit)
    anterior = O.read_override(p)
    for pasta in novos_volumes:
        Path(pasta).mkdir(parents=True, exist_ok=True)
        print(f"  mkdir -p {pasta}")
    if texto is None:
        O.remove_override(p)
        print("  " + loc("customization removed"))
    else:
        O.write_override(p, texto)
        print(f"  {loc('written')}: {O.dropin_path(p)}")
    if PREFIX:
        print(f"  ({loc('sandbox, not executed')}: systemctl --user daemon-reload; try-restart {unit})")
        return True
    if systemctl("daemon-reload", tempo=60) and systemctl("try-restart", unit):
        print("  " + loc("restarted — it came up"))
        return True
    print("\n" + loc("The service did not come up with this customization. Going back to the previous one:"))
    log = subprocess.run(["journalctl", "--user", "-u", f"{unit}.service", "-n", "12", "--no-pager", "-o", "cat"],
                         capture_output=True, text=True).stdout
    print(log.rstrip())
    if anterior is None:
        O.remove_override(p)
    else:
        O.write_override(p, anterior)
    systemctl("daemon-reload", tempo=60)
    ok = systemctl("try-restart", unit)
    print("  " + (loc("back as it was, and running") if ok else loc("back as it was, but it still does not start")))
    return False


# -- the .env of a service ------------------------------------------------------

SENSIVEL = re.compile(r"PASS|SECRET|TOKEN|KEY|CREDENTIAL|AUTH", re.I)


def env_files(app):
    """The .env files this service reads that exist on the host, by name."""
    s = I.Service(app, PREFIX)
    return s, {Path(p).name: Path(p) for p in s.env_files() if Path(p).is_file()}


def env_view(app):
    """[{file, units, entries}]: what the form edits, from the installed files."""
    s, arquivos = env_files(app)
    saida = []
    for nome, f in arquivos.items():
        usam = [u.stem for u in s.units if u.suffix == ".container"
                and f in {Path(s._expand(v)) for k, v in I.directives_of(u) if k == "EnvironmentFile"}]
        entradas = I.parse_env(f.read_text())
        for e in entradas:
            e["sensitive"] = bool(SENSIVEL.search(e["key"])) or e["type"] == "password"
            if e["type"] == "bool":
                e["bool"] = list(qhui.bool_pair(e["value"]))     # what the checkbox writes: (on, off)
        saida.append({"file": nome, "units": usam, "entries": entradas})
    return saida


def env_check(app, nome, mudar, desligar):
    """The file to edit, or ValueError saying why the request is refused.

    Only keys the file already names (active or commented) are accepted: the
    form edits the app's settings, it does not add lines to a file the unit
    feeds straight into a container. Values are one line, because a newline
    would be a second setting.
    """
    f = env_files(app)[1].get(nome)
    if f is None:
        raise ValueError(loc("unknown file"))
    tipos = {e["key"]: e["type"] for e in I.parse_env(f.read_text())}
    conhecidas = set(tipos)
    for k, v in mudar.items():
        if k not in conhecidas or not isinstance(v, str) or "\n" in v or "\r" in v:
            raise ValueError(f"{k}: " + loc("not a setting of this file, or not a single line"))
        if qhui.env_value_problem(tipos[k], v):
            raise ValueError(f"{k}: " + loc("not a valid value for the type") + f" {tipos[k]}")
    for k in desligar:
        if k not in conhecidas:
            raise ValueError(f"{k}: " + loc("not a setting of this file, or not a single line"))
    return f


def env_save(app, nome, mudar, desligar):
    """Writes the form's changes into one .env, keeping a .bak of what it was."""
    f = env_check(app, nome, mudar, desligar)
    bak = f.with_name(f.name + ".bak")
    fd = os.open(bak, os.O_WRONLY | os.O_CREAT | os.O_TRUNC, 0o600)
    with os.fdopen(fd, "w") as fh:
        fh.write(f.read_text())
    for k, v in mudar.items():
        I.set_env_value(f, k, v)
        print(f"  {k}: " + loc("set"))
    for k in desligar:
        if k not in mudar:
            I.unset_env_value(f, k)
            print(f"  {k}: " + loc("turned off"))



# -- resources: CPU, memory, disk ------------------------------------------------

STATS = {"t": None, "raw": None, "result": None}
STATS_LOCK, DISK = threading.Lock(), {}
DISK_TTL = 600
NOMES = {}                  # container name -> unit, built once from the repository


def parse_cgroup(texto):
    """The cgroup v2 path in /proc/<pid>/cgroup (`0::/path`), or None (v1, or none)."""
    for linha in texto.splitlines():
        if linha.startswith("0::"):
            return linha[3:].strip() or None
    return None


def vm_rss(pid):
    """Resident memory of a process in bytes, 0 if it is gone or unreadable."""
    try:
        for linha in Path(f"/proc/{pid}/status").read_text().splitlines():
            if linha.startswith("VmRSS:"):
                return int(linha.split()[1]) * 1024
    except (OSError, ValueError):
        pass
    return 0


def cgroup_usage(caminho):
    """(resident bytes, cpu microseconds) of a cgroup and everything under it.

    Read from /proc and cgroupfs because `podman stats` answers 0B for memory
    here: rootless, the memory controller is not delegated to the user's
    cgroup. RSS counts a page shared between a container's processes once per
    process, so it can read high for a multi-process app; it is a size to
    compare, not an accounting.
    """
    base = Path("/sys/fs/cgroup") / caminho.lstrip("/")
    rss = 0
    for pasta, _, arquivos in os.walk(base):
        if "cgroup.procs" in arquivos:
            try:
                rss += sum(vm_rss(p) for p in Path(pasta, "cgroup.procs").read_text().split())
            except OSError:
                pass
    cpu = 0
    try:
        for linha in (base / "cpu.stat").read_text().splitlines():
            if linha.startswith("usage_usec"):
                cpu = int(linha.split()[1])
    except (OSError, ValueError):
        pass
    return rss, cpu


def container_units():
    if not NOMES:
        for u in I.APPS.glob("*/*.container"):
            NOMES[I.container_name(u)] = u.stem
    return NOMES


def sample():
    """{container name: (resident bytes, cpu usec)} for the containers running now."""
    lido = I.run_read(["podman", "ps", "--format", "json"])
    saida = {}
    try:
        containers = json.loads(lido or "[]")
    except ValueError:
        return saida
    for c in containers:
        try:
            cg = parse_cgroup(Path(f"/proc/{c['Pid']}/cgroup").read_text())
        except (OSError, KeyError):
            continue
        if cg and c.get("Names"):
            saida[c["Names"][0]] = cgroup_usage(cg)
    return saida


def stats():
    """{unit: {cpu, mem}}: CPU as percent of one core over the last interval, memory in bytes.

    CPU is a rate, so it takes two readings: the first call waits a second for
    the second one, and later calls reuse the reading the previous call left.
    A call within 3 seconds of the last gets the same answer — several open
    pages must not make the host read /proc for each of them.
    """
    if PREFIX:
        return {}
    with STATS_LOCK:
        agora = time.time()
        if STATS["result"] is not None and agora - STATS["t"] < 3:
            return STATS["result"]
        antes, ta = STATS["raw"], STATS["t"]
        if antes is None:
            antes, ta = sample(), time.time()
            time.sleep(1.0)
        raw, tb = sample(), time.time()
        nomes, resultado = container_units(), {}
        for nome, (rss, usec) in raw.items():
            unit = nomes.get(nome)
            if not unit:
                continue
            dt = max(tb - ta, 0.001)
            cpu = (usec - antes[nome][1]) / (dt * 1e6) * 100 if nome in antes else 0.0
            resultado[unit] = {"cpu": round(max(cpu, 0.0), 1), "mem": rss}
        STATS.update(t=tb, raw=raw, result=resultado)
        return resultado


def resources_survey():
    """Unused images, networks and volumes. A sandbox has no podman of its own, so it reports none
    (unless a stand-in is named in QH_PODMAN, which is how the tests exercise it)."""
    if PREFIX and "QH_PODMAN" not in os.environ:
        return {"images": [], "networks": [], "volumes": [], "reclaimable": 0}
    return resources.survey(Path(PREFIX or Path.home()))


# -- files: the folders of the apps ------------------------------------------------------------

def files_roots(app):
    """{name: absolute path} of the directories under .../volumes/ the app's units use, or None when it is not installed."""
    if not service_dir(app):
        return None
    sv = I.Service(app, PREFIX)
    return {Path(r).name: r for r in sv.volume_roots()} if sv.installed() else None


def files_user_roots():
    """{"@VAR": path}: the folders the person chose for what the apps share (the media root, the recordings), read
    from the systemd variables the installed apps' `Volume=` lines use. Only folders that exist."""
    saida = {}
    for p in sorted(I.APPS.iterdir()):
        if not p.is_dir() or files_roots(p.name) is None:
            continue
        for caminho, _ in I.Service(p.name, PREFIX).volumes():
            for nome in re.findall(r"\$\{([A-Za-z_][A-Za-z0-9_]*)\}", caminho):
                valor = I.manager_var(nome)
                proibido = os.path.realpath(Path(PREFIX or Path.home()) / FILES_NEVER)
                if valor and Path(valor).is_dir() and not (os.path.realpath(valor) + os.sep).startswith(proibido + os.sep) \
                        and not proibido.startswith(os.path.realpath(valor) + os.sep) and os.path.realpath(valor) != proibido:
                    saida["@" + nome] = valor
    return saida


FILES_RO = {"@systemd": ".config/containers/systemd", "@env": ".config/containers/env"}     # to look at, never to change
FILES_NEVER = ".config/containers/secrets"          # not reachable by any root: the secrets are one file each, in the clear


def files_fixed_roots():
    """{"@systemd": path, "@env": path}: the units and the .env files, read only. A root that is or holds `secrets/` is
    refused outright, whatever it is called."""
    base = Path(PREFIX or Path.home())
    proibido = os.path.realpath(base / FILES_NEVER)
    saida = {}
    for nome, rel in FILES_RO.items():
        caminho = base / rel
        real = os.path.realpath(caminho)
        if caminho.is_dir() and real != proibido and not real.startswith(proibido + os.sep) and not proibido.startswith(real + os.sep):
            saida[nome] = str(caminho)
    return saida


def files_writable(path):
    """False for the read-only roots; the panel and the server both ask."""
    partes = [x for x in (path or "").split("/") if x]
    return bool(partes) and partes[0] not in FILES_RO


def files_apps():
    """The installed apps that keep data under volumes/, then the folders of the person's own, by name."""
    return sorted(p.name for p in I.APPS.iterdir() if p.is_dir() and files_roots(p.name)) + sorted(files_user_roots()) + sorted(files_fixed_roots())


def files_split(path):
    """(app, root path, rest) for "app/volume/sub/dir"; (app, None, "") for "app"; (None, None, "") for the top.

    "@NAME" is a folder of the person's own (the media root): its path is the root, with no volume level.
    Raises hostctl.FsError for what does not exist."""
    partes = [x for x in (path or "").split("/") if x]
    if not partes:
        return None, None, ""
    if partes[0].startswith("@"):
        dono = files_fixed_roots().get(partes[0]) or files_user_roots().get(partes[0])
        if dono is None:
            raise hostctl.FsError(404, "unknown folder")
        return partes[0], dono, "/".join(partes[1:])
    roots = files_roots(partes[0])
    if roots is None:
        raise hostctl.FsError(404, "unknown app")
    if len(partes) == 1:
        return partes[0], None, ""
    if partes[1] not in roots:
        raise hostctl.FsError(404, "unknown volume")
    return partes[0], roots[partes[1]], "/".join(partes[2:])


def files_run(op, root, rel, *extra):
    """The operation of hostctl on `root`/`rel`: inside `podman unshare` on a host (a container's files belong to a
    subuid the user cannot read from outside), in this process in a sandbox. Returns (rc, stdout bytes, stderr)."""
    if PREFIX or not shutil.which("podman"):
        raise RuntimeError("direct")
    r = subprocess.run(["podman", "unshare", "python3", str(Path(hostctl.__file__).resolve()), op, root, rel, *map(str, extra)],
                       capture_output=True, timeout=600)
    return r.returncode, r.stdout, r.stderr.decode(errors="replace")


def files_exec(op, root, rel, *extra):
    """A change to a folder, by hostctl in `podman unshare` (or in this process in a sandbox): the answer dict."""
    try:
        rc, out, err = files_run(op, root, rel, *extra)
    except RuntimeError:
        fn = {"fs-mkdir": hostctl.fs_mkdir, "fs-rename": hostctl.fs_rename, "fs-delete": hostctl.fs_delete,
              "fs-copy": hostctl.fs_copy, "fs-move": hostctl.fs_move}[op]
        return fn(root, rel, *extra)
    d = json.loads(out or b"{}")
    if "error" in d:
        raise hostctl.FsError(d["code"], d["error"])
    return d


def files_change(d):
    """One change asked by the panel ({op, path, name | to}), refused when it leaves the app's folders."""
    op, path = d.get("op"), d.get("path", "")
    if not files_writable(path) or (op in ("copy", "move") and not files_writable(d.get("to", ""))):
        raise hostctl.FsError(403, "read only")
    _, root, rel = files_split(path)
    if root is None:
        raise hostctl.FsError(400, "choose a folder")
    if op == "mkdir":
        return files_exec("fs-mkdir", root, rel, str(d.get("name", "")))
    if op == "rename":
        return files_exec("fs-rename", root, rel, str(d.get("name", "")))
    if op == "delete":
        return files_exec("fs-delete", root, rel)
    if op in ("copy", "move"):
        _, droot, drel = files_split(d.get("to", ""))
        if droot is None:
            raise hostctl.FsError(400, "choose a folder")
        return files_exec("fs-" + op, root, rel, droot, drel)
    raise hostctl.FsError(400, "operation")


def files_list(path):
    app, root, rel = files_split(path)
    if app is None:
        return {"entries": [{"name": a, "type": "dir", "size": None, "mtime": None} for a in files_apps()], "truncated": False}
    if root is None:
        return {"entries": [{"name": n, "type": "dir", "size": None, "mtime": None} for n in sorted(files_roots(app))], "truncated": False}
    try:
        rc, out, err = files_run("fs-ls", root, rel)
    except RuntimeError:
        return hostctl.fs_list(root, rel)
    d = json.loads(out or b"{}")
    if "error" in d:
        raise hostctl.FsError(d["code"], d["error"])
    return d


def files_preview(path):
    app, root, rel = files_split(path)
    if root is None:
        raise hostctl.FsError(400, "not a file")
    try:
        rc, out, err = files_run("fs-preview", root, rel)
    except RuntimeError:
        return hostctl.fs_preview(root, rel)
    d = json.loads(out or b"{}")
    if "error" in d:
        raise hostctl.FsError(d["code"], d["error"])
    return d


# -- what Podman says: health, what really runs, the images -----------------------------------------------------

def inspect_unit(unit):
    """`podman inspect` of the container of `unit`, or None when there is none (not running, or a sandbox)."""
    if PREFIX and "QH_PODMAN" not in os.environ:
        return None
    caminho = next(I.APPS.glob(f"*/{unit}.container"), None)
    if caminho is None:
        return None
    rc, out, _ = ctrinfo.podman("inspect", I.container_name(caminho))
    if rc != 0:
        return None
    try:
        return (json.loads(out) or [None])[0]
    except ValueError:
        return None


def health_state(unit):
    raw = inspect_unit(unit)
    if raw is None:
        return {"status": "none", "streak": 0, "runs": [], "config": {}, "running": False}
    return ctrinfo.health_view(raw)


def health_run(unit):
    """Runs the probe now, as the container's own `podman healthcheck run`. (rc, state after) ; rc 0 is healthy."""
    caminho = next(I.APPS.glob(f"*/{unit}.container"), None)
    rc, out, err = ctrinfo.podman("healthcheck", "run", I.container_name(caminho), timeout=60)
    return rc, (out or err).strip(), health_state(unit)


def runtime_state(unit, reveal=False):
    raw = inspect_unit(unit)
    if raw is None:
        return None
    p = installed_unit(unit)
    texto = p.read_text() if p is not None else next(I.APPS.glob(f"*/{unit}.container")).read_text()
    return ctrinfo.runtime_view(raw, ctrinfo.secret_env_keys(texto), reveal)


def images_state():
    """Every image on the disk: size, which apps use it, build date, version labels, and whether it can go."""
    if PREFIX and "QH_PODMAN" not in os.environ:
        return []
    casa = Path(PREFIX or Path.home())
    nomes, digests = resources.wanted_images(casa)
    unidades = container_units()
    def de(nome):
        u = unidades.get(nome)
        return {"unit": u, "app": unit_pasta(u)} if u else None
    vistas = ctrinfo.image_views(resources.podman_json("images"), resources.podman_json("ps", "-a"), nomes, digests, resources.normalize,
                                 lambda n: (de(n) or {}).get("unit"))
    for im in vistas:
        for u in im["used_by"]:
            u["app"] = unit_pasta(u["unit"]) if u["unit"] else None
    return vistas


def image_history(iid):
    rc, out, err = ctrinfo.podman("image", "history", "--format", "json", iid)
    if rc != 0:
        raise LookupError(err.strip() or "history")
    return ctrinfo.history_view(json.loads(out or "[]"))


def image_remove(iid):
    """Removes one image that nothing uses and no installed unit asks for. Runs inside a job."""
    alvo = next((i for i in images_state() if i["id"] == iid), None)
    if alvo is None or not alvo["removable"]:
        print(loc("this image is in use or an installed unit asks for it: not removed"))
        return False
    rc, out, err = ctrinfo.podman("rmi", "--force", iid, timeout=120)
    print((out or err).strip())
    return rc == 0


def force_unit(unit, restart):
    """A container that does not answer to the stop: `podman kill` first, then the unit is stopped (stays so after a reboot, as
    the Stop button does) or restarted. Runs inside a job."""
    caminho = next(I.APPS.glob(f"*/{unit}.container"))
    nome = I.container_name(caminho)
    if PREFIX:
        print(f"({loc('sandbox, not executed')}: podman kill {nome}; systemctl --user {'restart' if restart else 'mask --now'} {unit})")
        return True
    rc, out, err = ctrinfo.podman("kill", nome)
    print((f"podman kill {nome}: " + ((out or err).strip() or "ok")))
    if restart:
        if I.unit_masked(Path.home(), unit):
            systemctl("unmask", unit)
        return systemctl("restart", unit)
    return systemctl("mask", "--now", unit)


USAGE, USAGE_LOCK, USAGE_TTL = {"at": 0.0, "apps": []}, threading.Lock(), 300


def disk_usage(refresh=False):
    """What each installed app's data takes on disk, largest first, kept five minutes (walking a library is slow).

    Only the directories under .../volumes/ the unit names: a shared root such as `${MEDIA_DATA_DIR}` is the
    person's own folder, not the app's."""
    with USAGE_LOCK:
        if not refresh and USAGE["at"] and time.time() - USAGE["at"] < USAGE_TTL:
            return USAGE
        roots = {}
        for p in sorted(I.APPS.iterdir()):
            if p.is_dir():
                s = I.Service(p.name, PREFIX)
                if s.installed() and s.volume_roots():
                    roots[p.name] = s.volume_roots()
        USAGE.update(at=time.time(), apps=hostctl.usage(roots, unshare=False if PREFIX else None))
        return USAGE


class _SandboxSystemd:
    """The part of systemd a scheduled power action needs, for a sandbox that must not touch the machine."""

    def __init__(self, base):
        self.base = base

    def __call__(self, cmd, **kw):
        class R:
            stdout, returncode = "", 0
        r = R()
        if cmd[:3] == ["systemctl", "--user", "is-active"]:
            r.stdout = "active\n" if hostctl.state_file(self.base).exists() else "inactive\n"
        return r


def power_run():
    return _SandboxSystemd(PREFIX) if PREFIX else hostctl._run


HOST_PREV, HOST_LOCK = {}, threading.Lock()       # the last reading of CPU and network, for the rates
VIRTUAL_NICS = ("lo", "veth", "podman", "cni", "br-", "docker", "tailscale", "virbr")


def host_summary(proc="/proc", sys_="/sys", disk_path=None, prev=None, now=time.monotonic):
    """Load, CPU, memory, disk, network, temperature and uptime of the host: a few small file reads.

    `cpu.pct` and the network rates are between this reading and the previous one (kept in `prev`), so the
    first call after a start says None for them; a second call under a second later reuses the last answer.
    Each field is None when the host does not say (no sensor in a VM, say)."""
    prev = HOST_PREV if prev is None else prev
    def ler(caminho):
        try:
            return Path(caminho).read_text()
        except OSError:
            return ""
    r = {"cpus": os.cpu_count() or 1, "load": None, "mem": None, "temp": None, "uptime": None,
         "cpu": None, "disk": None, "net": None}
    t0 = now()
    if prev.get("at") is not None and t0 - prev["at"] < 1 and prev.get("out"):
        return prev["out"]
    try:
        r["load"] = float(ler(f"{proc}/loadavg").split()[0])
    except (ValueError, IndexError):
        pass
    mem = dict(re.findall(r"^(\w+):\s+(\d+)", ler(f"{proc}/meminfo"), re.M))
    if mem.get("MemTotal") and mem.get("MemAvailable"):
        total = int(mem["MemTotal"])
        r["mem"] = {"total": total * 1024, "used": (total - int(mem["MemAvailable"])) * 1024}
    temps = []
    for f in Path(sys_, "class/thermal").glob("thermal_zone*/temp"):
        try:
            temps.append(int(ler(f).strip()) / 1000)
        except ValueError:
            pass
    if not temps:
        for f in Path(sys_, "class/hwmon").glob("hwmon*/temp*_input"):
            try:
                temps.append(int(ler(f).strip()) / 1000)
            except ValueError:
                pass
    temps = [x for x in temps if 0 < x < 130]
    r["temp"] = round(max(temps), 1) if temps else None
    try:
        r["uptime"] = int(float(ler(f"{proc}/uptime").split()[0]))
    except (ValueError, IndexError):
        pass
    # CPU: busy share between two readings of the first line of /proc/stat
    try:
        n = [int(x) for x in ler(f"{proc}/stat").splitlines()[0].split()[1:9]]
        total, idle = sum(n), n[3] + n[4]
        pct = None
        if "cpu" in prev and total > prev["cpu"][0]:
            pct = round(100 * (1 - (idle - prev["cpu"][1]) / (total - prev["cpu"][0])), 1)
        prev["cpu"] = (total, idle)
        r["cpu"] = {"pct": pct, "cpus": r["cpus"], "load": r["load"]}
    except (ValueError, IndexError):
        pass
    # disk: the filesystem the apps' data lives on
    try:
        u = shutil.disk_usage(disk_path or (PREFIX or Path.home()))
        r["disk"] = {"total": u.total, "used": u.used}
    except OSError:
        pass
    # network: bytes through the real interfaces (not the container bridges, nor the tailnet's copy of the same traffic)
    rx = tx = 0
    visto = False
    for l in ler(f"{proc}/net/dev").splitlines()[2:]:
        nome, _, resto = l.partition(":")
        campos = resto.split()
        if len(campos) >= 9 and not nome.strip().startswith(VIRTUAL_NICS):
            rx, tx, visto = rx + int(campos[0]), tx + int(campos[8]), True
    if visto:
        taxa = (None, None)
        if "net" in prev and t0 > prev["net"][0]:
            dt = t0 - prev["net"][0]
            taxa = (max(0, round((rx - prev["net"][1]) / dt)), max(0, round((tx - prev["net"][2]) / dt)))
        prev["net"] = (t0, rx, tx)
        r["net"] = {"rx": rx, "tx": tx, "rx_rate": taxa[0], "tx_rate": taxa[1]}
    prev["at"], prev["out"] = t0, r
    return r


def disk(app):
    """{bytes, paths: [{name, bytes}]} for the data volumes this service owns, or bytes None.

    Through `podman unshare`, because rootless the files belong to subuids the
    plain user cannot read. The same set `qh --backup` packs: a service's own
    volumes, not a shared media root. Cached, since a big library can take a
    while to walk and the number does not need to be fresh.
    """
    if PREFIX:
        return {"bytes": None, "paths": []}
    guardado = DISK.get(app)
    if guardado and time.time() - guardado[0] < DISK_TTL:
        return guardado[1]
    s = I.Service(app)
    proprios = s.exclusive_volumes()
    raizes = [r for r in (proprios if proprios is not None else s.volume_roots()) if Path(r).exists()]
    saida = {"bytes": 0, "paths": []}
    if raizes:
        try:
            r = subprocess.run(["podman", "unshare", "du", "-sk", *raizes],
                               capture_output=True, text=True, timeout=120)
        except (OSError, subprocess.TimeoutExpired):
            return {"bytes": None, "paths": []}
        for linha in r.stdout.splitlines():
            kb, _, caminho = linha.partition("\t")
            if kb.isdigit():
                saida["paths"].append({"name": Path(caminho).name, "bytes": int(kb) * 1024})
        saida["bytes"] = sum(x["bytes"] for x in saida["paths"])
    DISK[app] = (time.time(), saida)
    return saida


# -- architecture ----------------------------------------------------------------

ARCH_TTL = 7 * 24 * 3600     # a pinned tag does not change what it is built for
ARCH_NOMES = {"x86_64": "amd64", "amd64": "amd64", "aarch64": "arm64", "arm64": "arm64",
              "armv7l": "arm", "armv6l": "arm"}


def host_arch():
    return ARCH_NOMES.get(platform.machine(), platform.machine())


def arch_report(units, host, lookup):
    """What each unit's image is built for, and whether it runs on `host`.

    `units` is [(unit, image)]; `lookup(image)` gives a set like
    {"linux/amd64"} or None when the registry would not say. `ok` is None for
    an unknown answer: not knowing is not a warning.
    """
    saida = []
    for unit, imagem in units:
        plataformas = lookup(imagem)
        linux = sorted(p.split("/", 1)[1] for p in (plataformas or ()) if p.startswith("linux/"))
        saida.append({"unit": unit, "image": imagem, "platforms": linux or None,
                      "ok": None if not plataformas else f"linux/{host}" in plataformas})
    return saida


def arch_cache_file():
    return Path(PREFIX or Path.home()) / ".cache/quadlet-homelab/store-arch.json"


def arch(app):
    """{host, units: [{unit, image, platforms, ok}], runs: [common platforms]} for a service."""
    s = I.Service(app, PREFIX)
    units = [(u.stem, next((v for k, v in I.directives_of(u) if k == "Image"), ""))
             for u in s.units if u.suffix == ".container"]
    host = host_arch()
    if PREFIX:             # a sandbox must not reach the network
        return {"host": host, "units": arch_report(units, host, lambda _i: None), "runs": None}
    try:
        guardado = json.loads(arch_cache_file().read_text())
    except (OSError, ValueError):
        guardado = {}
    agora = time.time()
    faltam = sorted({i for _, i in units if i and not (
        i in guardado and agora - guardado[i]["at"] < ARCH_TTL)})
    if faltam:
        with ThreadPoolExecutor(max_workers=8) as pool:
            for imagem, plataformas in zip(faltam, pool.map(U.architectures, faltam)):
                if plataformas is not None:      # a failed lookup is asked again next time
                    guardado[imagem] = {"at": agora, "platforms": sorted(plataformas)}
        arch_cache_file().parent.mkdir(parents=True, exist_ok=True)
        arch_cache_file().write_text(json.dumps(guardado))
    relatorio = arch_report(units, host, lambda i: set(guardado.get(i, {}).get("platforms", [])) or None)
    conjuntos = [set(x["platforms"]) for x in relatorio if x["platforms"]]
    return {"host": host, "units": relatorio,
            "runs": sorted(set.intersection(*conjuntos)) if conjuntos else None}


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


def control_cmds(app, verbo, estados=None):
    """(commands, history action) for play/pause/stop of a whole service, or ([], None) when there is nothing to do.

    `estados` is {container: podman Status}; read from podman when not given (tests give it)."""
    s = I.Service(app, PREFIX)
    instaladas = [u for u in s.installed() if u.suffix == ".container"]
    if not instaladas:
        return [], None
    if estados is None:
        estados = {} if PREFIX else I.host_state()[1]
    por_estado = {u.stem: I.estado_do_container(estados.get(I.container_name(u), "—")) for u in instaladas}
    nomes = {u.stem: I.container_name(u) for u in instaladas}
    mascaradas = [u.stem for u in instaladas if I.unit_masked(s.home, u.stem)]
    parados = [x for x, e in por_estado.items() if e == "paused"]
    rodando = [x for x, e in por_estado.items() if e in ("up", "healthy", "unhealthy")]
    if verbo == "pause":
        return ([["podman", "pause", *(nomes[x] for x in rodando)]], "pause") if rodando else ([], None)
    if verbo == "stop":
        if len(mascaradas) == len(instaladas):
            return [], None
        # Masked, not just stopped: a plain stop is undone by the next boot, which starts every
        # unit wanted by default.target. Mask is what survives it; play lifts it. A frozen
        # container does not stop on SIGTERM, so it is thawed first.
        return ([["podman", "unpause", *(nomes[x] for x in parados)]] if parados else []) \
            + [["systemctl", "--user", "mask", "--now", *(u.stem for u in instaladas)]], "stop"
    # play: thaw what is frozen, start what is not running
    cmds = [["podman", "unpause", *(nomes[x] for x in parados)]] if parados else []
    faltam = [u for u in instaladas if por_estado[u.stem] not in ("up", "healthy", "unhealthy", "paused")]
    if mascaradas:
        cmds.append(["systemctl", "--user", "unmask", *mascaradas])
    if faltam:
        cmds.append(["systemctl", "--user", "start", *(u.stem for u in faltam)])
    return cmds, ("resume" if parados and not faltam else "start") if cmds else None


PODMAN = os.environ.get("QH_PODMAN", "podman")                      # tests point it at a stand-in
SHELLS = threading.BoundedSemaphore(4)                               # each console is a thread, a pty and a process


def same_origin(origin, host):
    """Whether a browser's Origin header names this very server. A WebSocket carries no custom header
    for the page to prove itself with, so this is what stops another site from opening a console."""
    return bool(origin) and bool(host) and urlparse(origin).netloc == host and urlparse(origin).scheme in ("http", "https")


JOURNALCTL = os.environ.get("QH_JOURNALCTL", "journalctl")      # tests point it at a stand-in
STREAMS = threading.BoundedSemaphore(8)                              # a log stream is a thread and a process each
HEARTBEAT = 15


def sse_frame(linha):
    """One Server-Sent Events message for one log line (a line holds no newline, but be sure)."""
    return ("data: " + linha.replace("\r", "").replace("\n", " ") + "\n\n").encode()


def manifest_tipo(nome):
    return IMAGENS[Path(nome).suffix.lower()]


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


def install_refusal(app, lang="en"):
    """Why an install of `app` is refused, or None: it, or a service it would bring, is marked
    deprecated and not installed yet. What is already installed is never refused — it
    can still be managed, and removing it is the likeliest next thing a person wants."""
    for x in chain(app):
        s = I.Service(x, PREFIX)
        razao = I.deprecation(s.ini)
        if razao and not s.installed():
            return f"{x}: " + loc("marked deprecated, no install:") + " " + razao["pt" if lang == "pt" else "en"]
    return None


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
        erro = I.var_problem(s, nome, valor)
        if erro:
            print(f"  {nome}: {erro}")
            return False
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

    def __init__(self, app, action, origem="", unit=""):
        self.id = secrets.token_hex(8)
        self.app, self.action, self.origem, self.unit = app, action, origem, unit
        self.started = time.time()
        self.out, self.rc = [], None

    def write(self, texto):           # a file, for redirect_stdout
        if texto:
            self.out.append(texto)

    def flush(self):
        pass


def start_job(app, action, cmd, lang, prepare=None, entrada=None, refrescar=None, origem="",
              unit="", depois=None, continuar=False):
    """The job, running in the background — or None when another one still is.

    One at a time: two `qh --apply` racing each other over the same
    systemd/ tree is the one thing the terminal never does.
    """
    if not JOB_LOCK.acquire(blocking=False):
        return None
    job = Job(app, action, origem, unit)
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
            rc, falhou = 0, 0
            # One command, or several in order (an upgrade is a bump, then an
            # update): each runs only if the one before it succeeded.
            for i, uno in enumerate(cmd if cmd and isinstance(cmd[0], list) else [cmd] if cmd else []):
                if i:
                    job.write("\n" + "─" * 60 + "\n")
                if PREFIX and uno[0] in ("systemctl", "podman"):
                    job.write(f"({loc('sandbox, not executed')}: {' '.join(uno)})\n")
                    continue
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
                    falhou = rc
                    if not continuar:
                        break
            if continuar and falhou:
                rc = falhou          # `continuar`: every command ran; the job still says one of them failed
            # What has to follow a successful run: the customization chosen before an install, which is
            # written into the unit's drop-in only once the unit exists.
            if rc == 0 and depois:
                with contextlib.redirect_stdout(job):
                    if depois() is False:
                        rc = 1
            # Refreshed BEFORE the exit code is published: the page asks for
            # the comparison as soon as it sees the job end, and it got the
            # pre-update answer — 26.11.0 installed, "new version 26.11.0".
            if action in MUDA_VERSAO:
                for x in (refrescar or [app]):
                    refresh_updates(x)
            job.rc = rc
            if action == "backup" and rc:
                try:
                    alert_backup_failed(job)
                except Exception:
                    pass
        except Exception as e:        # the page must learn the job ended
            job.write(f"\n{type(e).__name__}: {e}\n")
            job.rc = 1
        finally:
            try:
                history_add(job)
            except Exception:     # the record of a job must never be what breaks it
                pass
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

    def _shell(self, unit):
        """A console in the unit's container: `podman exec -it` on a pty, over a WebSocket.

        Whoever holds the token already controls every service, so a console adds no power, only
        convenience — but it is a shell, so the browser's Origin must be this server's own, the
        session is limited in number and time, and each one is written to the history."""
        if not same_origin(self.headers.get("Origin", ""), self.headers.get("Host", "")):
            return self._json(403, {"error": "origin"})
        chave = self.headers.get("Sec-WebSocket-Key", "")
        if ("websocket" not in self.headers.get("Upgrade", "").lower() or self.headers.get("Sec-WebSocket-Version") != "13"
                or not chave):
            return self._json(400, {"error": loc("this address takes a WebSocket")})
        if PREFIX and "QH_PODMAN" not in os.environ:
            return self._json(400, {"error": loc("a sandbox has no containers to enter")})
        if not SHELLS.acquire(blocking=False):
            return self._json(429, {"error": loc("too many consoles open")})
        job = None
        try:
            caminho = next(I.APPS.glob(f"*/{unit}.container"))
            nome = I.container_name(caminho)
            job = Job(caminho.parent.name, "shell", self.client_address[0], unit)
            self.send_response(101, "Switching Protocols")
            self.send_header("Upgrade", "websocket")
            self.send_header("Connection", "Upgrade")
            self.send_header("Sec-WebSocket-Accept", wsterm.accept_key(chave))
            self.end_headers()
            self.wfile.flush()
            marca = secrets.token_hex(8)

            def limpar():          # the shell on the container's side outlives our `podman exec`
                subprocess.run([PODMAN, "exec", nome, "sh", "-c", wsterm.reap_cmd(marca)],
                               capture_output=True, timeout=15)
            motivo = wsterm.serve(self.connection, [PODMAN, "exec", "-it", "-e", "TERM=dumb", "-e", f"QH_CONSOLE={marca}",
                                                    nome, "sh", "-c", wsterm.SHELL_CMD], limpar=limpar)
            job.write(f"console in {nome}: {motivo}, {round(time.time() - job.started)}s\n")
            job.rc = 0
        except Exception as e:                       # the connection is gone either way
            if job:
                job.write(f"console failed: {type(e).__name__}: {e}\n")
                job.rc = 1
        finally:
            SHELLS.release()
            self.close_connection = True
            if job:
                try:
                    history_add(job)
                except Exception:
                    pass

    def _stream_logs(self, unit):
        """`journalctl -f` for one unit as Server-Sent Events: the last 200 lines, then the new ones.

        Ends when the browser goes away. An idle journal writes nothing, so a comment line goes out
        every HEARTBEAT seconds — that write is what notices a closed tab and frees the process."""
        import select
        if PREFIX and "QH_JOURNALCTL" not in os.environ:
            return self._json(200, {"output": ""})          # a sandbox has no journal of its own
        if not STREAMS.acquire(blocking=False):
            return self._json(429, {"error": loc("too many log streams open")})
        proc = None
        try:
            self.send_response(200)
            self.send_header("Content-Type", "text/event-stream")
            self.send_header("Cache-Control", "no-cache")
            self.send_header("X-Accel-Buffering", "no")        # a proxy in front must not hold the lines back
            self.send_header("Content-Security-Policy", CSP)
            self.send_header("X-Content-Type-Options", "nosniff")
            self.end_headers()
            proc = subprocess.Popen([JOURNALCTL, "--user", "-u", f"{unit}.service", "-n", "200", "-f",
                                     "--no-pager", "-o", "short-iso"],
                                    stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, bufsize=1)
            while True:
                pronto, _, _ = select.select([proc.stdout], [], [], HEARTBEAT)
                if pronto:
                    linha = proc.stdout.readline()
                    if not linha:
                        break                                  # journalctl ended
                    self.wfile.write(sse_frame(linha.rstrip("\n")))
                else:
                    self.wfile.write(b": ping\n\n")
                self.wfile.flush()
        except (BrokenPipeError, ConnectionResetError, OSError):
            pass                                               # the page closed
        finally:
            if proc is not None:
                proc.kill()
                proc.wait()
            STREAMS.release()
            self.close_connection = True

    def _redirect(self, where, headers=()):
        self._send(303, b"", "text/plain", [("Location", where), *headers])

    def _logged(self):
        jar = cookies.SimpleCookie(self.headers.get("Cookie", ""))
        valor = jar[COOKIE].value if COOKIE in jar else ""
        return hmac.compare_digest(valor.encode(), cookie_for(self.token).encode())

    def _body(self, limite=65536):
        n = int(self.headers.get("Content-Length") or 0)
        if n > limite:
            raise ValueError("body too large")
        return self.rfile.read(n) if n else b""

    def _file_upload(self, q):
        """A file sent from the browser into a folder of an app: streamed into hostctl, which writes it beside its final name
        and renames it only when whole. Announced length and written length must agree, so a cut upload is not kept."""
        if not files_writable(q.get("path", [""])[0]):
            raise hostctl.FsError(403, "read only")
        _, root, rel = files_split(q.get("path", [""])[0])
        if root is None:
            raise hostctl.FsError(400, "choose a folder")
        nome, ow = q.get("name", [""])[0], q.get("overwrite", ["0"])[0] == "1"
        n = int(self.headers.get("Content-Length") or -1)
        if n < 0:
            raise hostctl.FsError(411, "length")
        hostctl.clean_name(nome)
        if PREFIX or not shutil.which("podman"):
            class Lido:
                def __init__(s, f, restante):
                    s.f, s.rest = f, restante
                def read(s, k=-1):
                    k = s.rest if k is None or k < 0 else min(k, s.rest)
                    dados = s.f.read(k)
                    s.rest -= len(dados)
                    return dados
            return self._json(200, hostctl.fs_write(root, rel, nome, Lido(self.rfile, n), ow, n))
        proc = subprocess.Popen(["podman", "unshare", "python3", str(Path(hostctl.__file__).resolve()), "fs-write", root, rel, nome,
                                 "1" if ow else "0", str(n)], stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        try:
            restante = n
            while restante:
                dados = self.rfile.read(min(restante, 1 << 20))
                if not dados:
                    break
                proc.stdin.write(dados)
                restante -= len(dados)
            proc.stdin.close()
            out = proc.stdout.read()
            proc.wait(timeout=60)
        except (BrokenPipeError, OSError):
            proc.kill()
            raise hostctl.FsError(502, "write")
        finally:
            if proc.poll() is None:
                proc.kill()
        d = json.loads(out or b"{}")
        if "error" in d:
            raise hostctl.FsError(d["code"], d["error"])
        return self._json(200, d)

    def _file_download(self, path, inline=False):
        """A file of an app's folder, streamed as a download. Refused paths answer before a byte is sent."""
        app, root, rel = files_split(path)
        if root is None:
            raise hostctl.FsError(400, "not a file")
        nome = (rel.rsplit("/", 1)[-1] or "file")
        # `inline` shows an image in the panel; only these types, so a page of a container's making is never rendered
        tipo = IMAGE_TYPES.get(nome.rsplit(".", 1)[-1].lower()) if inline else None
        cab = lambda tam: ([("Content-Type", tipo or "application/octet-stream"), ("X-Content-Type-Options", "nosniff"),   # noqa: E731
                            ("Cache-Control", "no-store"),
                            ("Content-Disposition", ("inline" if tipo else "attachment") + "; filename*=UTF-8''" + urllib.parse.quote(nome))]
                           + ([("Content-Length", str(tam))] if tam is not None else []))
        if PREFIX or not shutil.which("podman"):
            f, tam = hostctl.fs_open(root, rel)
            with f:
                self.send_response(200)
                for k, v in cab(tam):
                    self.send_header(k, v)
                self.end_headers()
                shutil.copyfileobj(f, self.wfile, 1 << 20)
            return
        proc = subprocess.Popen(["podman", "unshare", "python3", str(Path(hostctl.__file__).resolve()), "fs-cat", root, rel],
                                stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        try:
            primeiro = proc.stdout.read(1 << 16)
            if not primeiro and proc.wait() != 0:
                erro = json.loads(proc.stderr.read() or b"{}")
                raise hostctl.FsError(erro.get("code", 400), erro.get("error", "read"))
            self.send_response(200)
            for k, v in cab(None):
                self.send_header(k, v)
            self.end_headers()
            self.wfile.write(primeiro)
            shutil.copyfileobj(proc.stdout, self.wfile, 1 << 20)
        finally:
            proc.kill()
            proc.wait()

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

    def _asset(self, app, nome):
        """The logo or a screenshot of an app, from its own folder: nothing outside it, nothing but images.

        An SVG is served with a policy that lets it draw and nothing else, so opening one in a tab runs no script."""
        base = (I.APPS / app).resolve()
        arquivo = (base / nome).resolve()
        if not base.is_dir() or base not in arquivo.parents or arquivo.suffix.lower() not in IMAGENS or not arquivo.is_file():
            return self._json(404, {"error": "not found"})
        corpo = arquivo.read_bytes()
        self.send_response(200)
        self.send_header("Content-Type", IMAGENS[arquivo.suffix.lower()])
        self.send_header("Content-Length", str(len(corpo)))
        self.send_header("Cache-Control", "private, max-age=3600")
        self.send_header("X-Content-Type-Options", "nosniff")
        self.send_header("Content-Security-Policy", "default-src 'none'; style-src 'unsafe-inline'; sandbox")
        self.end_headers()
        self.wfile.write(corpo)

    def _static(self, nome):
        f = STATIC / nome
        self._send(200, f.read_bytes(), TIPOS[f.suffix])

    # GET ---------------------------------------------------------------------

    def do_GET(self):
        url = urlparse(self.path)
        q = {k: v[0] for k, v in parse_qs(url.query).items()}
        if url.path == "/login":
            # A refused token comes back as ?e=1. The page cannot read its own
            # query (no inline script, by the CSP), so the notice is put in the
            # HTML here — a fixed text, nothing from the request is echoed.
            html = (STATIC / ARQUIVOS["/login"]).read_text()
            aviso = '<p class="erro" role="alert">Token inválido / Invalid token</p>' if q.get("e") == "1" else ""
            return self._send(200, html.replace("<!--error-->", aviso).encode(), TIPOS[".html"])
        if url.path in ("/style.css", "/fonts/jakarta.woff2"):         # the login page draws with both
            return self._static(ARQUIVOS[url.path])
        if not self._logged():
            if url.path.startswith("/api/"):
                return self._json(401, {"error": "login"})
            return self._redirect("/login")
        if url.path in ARQUIVOS:
            return self._static(ARQUIVOS[url.path])
        m = ASSET.match(url.path)
        if m:
            return self._asset(m.group(1), m.group(2))
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
            recusa = install_refusal(app, lang) if action == "install" else None
            if recusa:
                return self._json(400, {"error": recusa})
            algum, todos = pinning(app) if action == "upgrade" else (False, False)
            if action == "upgrade" and PREFIX and not todos:
                return self._json(400, {"error": loc("an upgrade edits the repository, "
                                                     "which a sandbox does not have")})
            if action == "upgrade":
                # What leaves its version to the host is moved there; the rest is a bump in the repository.
                cmds = ([] if todos else [bump_cmd(app, False)]) + ([qh(app, "--update", "--latest")] if algum else [])
            else:
                cmds = [qh(app, *extra, *(["--purge"] if action == "remove" and q.get("purge") == "1" else []))]
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
            vazio = (em_dia(saida) if todos else bump_vazio(saida) and (not algum or em_dia(saida))) if action == "upgrade" else em_dia(saida)
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
        if url.path == "/api/resources":
            try:
                return self._json(200, resources_survey())
            except (RuntimeError, OSError, subprocess.TimeoutExpired, ValueError) as e:
                return self._json(502, {"error": f"podman: {e}"})
        if url.path.startswith("/api/files"):
            try:
                if url.path == "/api/files":
                    return self._json(200, {"path": q.get("path", ""), **files_list(q.get("path", ""))})
                if url.path == "/api/files/preview":
                    return self._json(200, files_preview(q.get("path", "")))
                if url.path == "/api/files/download":
                    return self._file_download(q.get("path", ""), q.get("inline") == "1")
            except hostctl.FsError as e:
                return self._json(e.code, {"error": str(e)})
            except (OSError, subprocess.TimeoutExpired, ValueError) as e:
                return self._json(502, {"error": str(e)})
        if url.path in ("/api/health", "/api/runtime"):
            unit = q.get("unit", "")
            if not unit_exists(unit):
                return self._json(400, {"error": loc("unknown unit")})
            if url.path == "/api/health":
                return self._json(200, health_state(unit))
            vista = runtime_state(unit, q.get("reveal") == "1")
            return self._json(200, vista) if vista else self._json(404, {"error": loc("not installed")})
        if url.path == "/api/images":
            try:
                return self._json(200, {"images": images_state()})
            except (RuntimeError, OSError, subprocess.TimeoutExpired, ValueError) as e:
                return self._json(502, {"error": f"podman: {e}"})
        if url.path == "/api/images/history":
            iid = q.get("id", "")
            if not re.fullmatch(r"[0-9a-f]{12,64}", iid):
                return self._json(400, {"error": "id"})
            try:
                return self._json(200, {"layers": image_history(iid)})
            except (LookupError, ValueError, OSError, subprocess.TimeoutExpired) as e:
                return self._json(404, {"error": str(e)})
        if url.path == "/api/usage":
            u = disk_usage(q.get("refresh") == "1")
            return self._json(200, {"apps": u["apps"], "at": int(u["at"])})
        if url.path == "/api/power":
            return self._json(200, {"scheduled": hostctl.state(Path(PREFIX or Path.home()), power_run())})
        if url.path == "/api/host":
            with HOST_LOCK:
                return self._json(200, host_summary())
        if url.path == "/api/links":
            app = q.get("app", "")
            if not service_dir(app):
                return self._json(400, {"error": loc("unknown service")})
            return self._json(200, {"links": links(app)})
        if url.path == "/api/settings":
            return self._json(200, settings())
        if url.path == "/api/network":
            return self._json(200, N.state(I.network_ctx(Path(PREFIX) if PREFIX else Path.home(), PREFIX)))
        if url.path == "/api/ui":
            return self._json(200, ui_settings())
        if url.path == "/api/svc":
            return self._json(200, {"apps": svc_state(force=q.get("refresh") == "1")})
        if url.path == "/api/monitor":
            return self._json(200, {"apps": monitor()})
        if url.path == "/ui/background":
            f = ui_background()
            if not f:
                return self._json(404, {"error": "not found"})
            corpo = f.read_bytes()
            self.send_response(200)
            self.send_header("Content-Type", BG_TYPES[f.suffix])
            self.send_header("Content-Length", str(len(corpo)))
            self.send_header("Cache-Control", "private, max-age=86400")
            self.send_header("X-Content-Type-Options", "nosniff")
            self.end_headers()
            self.wfile.write(corpo)
            return
        if url.path == "/api/alerts":
            return self._json(200, {"config": A.public(A.load(alert_home())), "kinds": list(A.KINDS),
                                    "sent": len(alerts_state())})
        if url.path == "/api/dirs":
            try:
                return self._json(200, list_dirs(q.get("path", "")))
            except ValueError as e:
                return self._json(400, {"error": str(e)})
        if url.path == "/api/custom":
            unit = q.get("unit", "")
            if not unit_exists(unit):
                return self._json(400, {"error": loc("unknown unit")})
            try:
                return self._json(200, custom_state(unit, pre=q.get("pre") == "1"))
            except LookupError as e:
                return self._json(404, {"error": str(e)})
        if url.path == "/api/drift":
            unit = q.get("unit", "")
            if not unit_exists(unit):
                return self._json(400, {"error": loc("unknown unit")})
            try:
                return self._json(200, unit_drift_diff(unit))
            except LookupError as e:
                return self._json(404, {"error": str(e)})
        if url.path in ("/api/env", "/api/disk", "/api/arch"):
            app = q.get("app", "")
            if not service_dir(app):
                return self._json(400, {"error": loc("unknown service")})
            if url.path == "/api/env":
                return self._json(200, {"files": env_view(app)})
            if url.path == "/api/disk":
                return self._json(200, disk(app))
            return self._json(200, arch(app))
        if url.path == "/api/history":
            try:
                limite = max(1, min(500, int(q.get("limit", "100"))))
            except ValueError:
                limite = 100
            return self._json(200, {"entries": history_read(q.get("app") or None, limite)})
        if url.path.startswith("/api/history/"):
            e = history_get(url.path.rsplit("/", 1)[1])
            return self._json(200, e) if e else self._json(404, {"error": "history"})
        if url.path == "/api/stats":
            return self._json(200, {"stats": stats()})
        if url.path == "/api/notes":
            unit = q.get("unit", "")
            if not unit_exists(unit):
                return self._json(400, {"error": loc("unknown unit")})
            return self._json(200, notes(unit))
        if url.path == "/api/jobs/active":
            # What is running now, so a window closed (or a page reloaded) can pick the job up again.
            vivo = next((j for j in reversed(list(JOBS.values())) if j.rc is None), None)
            return self._json(200, {"job": {"id": vivo.id, "app": vivo.app, "action": vivo.action} if vivo else None})
        if url.path.startswith("/api/job/"):
            job = JOBS.get(url.path.rsplit("/", 1)[1])
            if not job:
                return self._json(404, {"error": "job"})
            desde = int(q.get("from", "0") or 0)
            return self._json(200, {"app": job.app, "action": job.action, "rc": job.rc,
                                    "next": len(job.out), "output": "".join(job.out[desde:])})
        if url.path == "/api/shell":
            unit = q.get("unit", "")
            if not unit_exists(unit):
                return self._json(400, {"error": loc("unknown unit")})
            return self._shell(unit)
        if url.path == "/api/logs/stream":
            unit = q.get("unit", "")
            if not unit_exists(unit):
                return self._json(400, {"error": loc("unknown unit")})
            return self._stream_logs(unit)
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
            if dado and hmac.compare_digest(dado.encode(), self.token.encode()):
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
        if url.path == "/api/ui/background":
            try:
                dados = self._body(BG_MAX)
            except ValueError:
                return self._json(413, {"error": "the image is over 8 MB"})
            erro = ui_set_background(dados)
            return self._json(400, {"error": erro}) if erro else self._json(200, ui_settings())
        if url.path.startswith("/api/files/"):
            try:
                if url.path == "/api/files/upload":
                    return self._file_upload(parse_qs(url.query))
                if url.path == "/api/files/op":
                    d0 = json.loads(self._body() or b"{}")
                    return self._json(200, files_change(d0 if isinstance(d0, dict) else {}))
            except hostctl.FsError as e:
                return self._json(e.code, {"error": str(e)})
            except (OSError, subprocess.TimeoutExpired, ValueError) as e:
                return self._json(502, {"error": str(e)})
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

        if url.path in ("/api/custom/preview", "/api/custom/apply", "/api/custom/reset"):
            unit = d.get("unit", "")
            if not unit_exists(unit):
                return self._json(400, {"error": loc("unknown unit")})
            # Only a preview may look at a unit that is not installed yet (the form before an install).
            pre = bool(d.get("pre")) and url.path.endswith("/preview")
            if installed_unit(unit) is None and not pre:
                return self._json(404, {"error": loc("not installed")})
            reverter = url.path.endswith("/reset")
            try:
                plano = custom_plan(unit, {} if reverter else d.get("config") or {}, pre=pre)
            except LookupError as e:
                return self._json(404, {"error": str(e)})
            if url.path.endswith("/preview"):
                return self._json(200, {k: v for k, v in plano.items() if k not in ("desired", "base_text")})
            if plano["errors"] and not reverter:
                return self._json(400, {"error": "; ".join(plano["errors"]), "errors": plano["errors"]})
            novos = [] if reverter else new_volume_dirs(plano["base_text"], plano)
            texto = None if reverter else plano["text"]
            pasta = next(I.APPS.glob(f"*/{unit}.container")).parent.name
            job = start_job(pasta, "revert" if reverter else "customize", [], lang,
                            lambda: apply_override(unit, texto, novos), origem=self.client_address[0], unit=unit)
            if job is None:
                return self._json(409, {"error": loc("another job is running")})
            return self._json(202, {"job": job.id})

        if url.path in ("/api/custom/unit-check", "/api/custom/unit-save", "/api/custom/unit-reset"):
            unit = d.get("unit", "")
            if not unit_exists(unit):
                return self._json(400, {"error": loc("unknown unit")})
            app = unit_pasta(unit)
            if url.path.endswith("-check"):
                return self._json(200, unit_review(unit, d.get("text")))
            if installed_unit(unit) is None:
                return self._json(404, {"error": loc("not installed")})
            texto = None
            if url.path.endswith("-save"):
                texto = d.get("text")
                rev = unit_review(unit, texto)
                if rev["errors"]:
                    return self._json(400, {"error": "; ".join(rev["errors"]), **rev})
                if rev["warnings"] and d.get("ack") is not True:
                    return self._json(400, {"error": loc("confirm the warnings to go on"), "need_ack": True, **rev})
                if not rev["changed"]:
                    texto = None                       # the same as the repository's: nothing is custom
            job = start_job(app, "custom-unit", [], lang, lambda: apply_custom_unit(app, unit, texto),
                            origem=self.client_address[0], unit=unit)
            if job is None:
                return self._json(409, {"error": loc("another job is running")})
            return self._json(202, {"job": job.id})

        if url.path == "/api/env/save":
            app = d.get("app", "")
            if not service_dir(app):
                return self._json(400, {"error": loc("unknown service")})
            mudar, desligar = d.get("set") or {}, d.get("off") or []
            if not (isinstance(mudar, dict) and isinstance(desligar, list)
                    and all(isinstance(k, str) for k in [*mudar, *desligar])):
                return self._json(400, {"error": "set/off"})
            nome = d.get("file", "")
            try:                                   # refused here, before any job exists
                env_check(app, nome, mudar, desligar)
            except ValueError as e:
                return self._json(400, {"error": str(e)})
            principal = I.Service(app, PREFIX).main_unit()
            usam = next((x["units"] for x in env_view(app) if x["file"] == nome), []) \
                or ([principal.stem] if principal else [])
            # try-restart: a stopped service is not started by editing its settings.
            cmd = [["systemctl", "--user", "try-restart", u] for u in usam]
            job = start_job(app, "env", cmd, lang, lambda: env_save(app, nome, mudar, desligar),
                            origem=self.client_address[0])
            if job is None:
                return self._json(409, {"error": loc("another job is running")})
            return self._json(202, {"job": job.id})

        if url.path == "/api/svc/config":
            app, slot = d.get("app", ""), d.get("slot", "")
            valores = d.get("values") or {}
            if not service_dir(app) or not isinstance(valores, dict):
                return self._json(400, {"error": loc("unknown service")})
            erro = svc_config(app, slot, valores)
            return self._json(400, {"error": erro}) if erro else self._json(200, {"apps": svc_state(force=True)})
        if url.path == "/api/ui":
            erros = ui_save({k: v for k, v in d.items() if k != "lang"}) if isinstance(d, dict) else ["an object"]
            return self._json(400, {"error": "; ".join(erros)}) if erros else self._json(200, ui_settings())
        if url.path == "/api/alerts":
            atual = A.load(alert_home())
            if d.get("clear_token"):
                atual["token"] = ""
            novo = {**atual, **{k: v for k, v in d.items() if k in A.DEFAULTS and k != "token"}}
            if d.get("token"):
                novo["token"] = d["token"]
            cfg, erros = A.clean(novo)
            if erros:
                return self._json(400, {"error": "; ".join(erros)})
            A.save(cfg, alert_home())
            return self._json(200, {"config": A.public(cfg)})
        if url.path == "/api/alerts/test":
            cfg = A.load(alert_home())
            if not (cfg["server"] and cfg["topic"]):
                return self._json(400, {"error": "set the server and the topic first"})
            erro = A.push(cfg, {"kind": "test", "title": "Quadlet store: test", "message": "Alerts are working."})
            return self._json(200 if not erro else 502, {"ok": not erro, **({"error": erro} if erro else {})})
        if url.path == "/api/network":
            modo = d.get("mode", "")
            url_h, nome = str(d.get("server_url") or "").strip(), str(d.get("tailnet") or "").strip()
            erros = N.check(modo, url_h, nome)
            if erros:
                return self._json(400, {"error": "; ".join(erros)})
            args = ["--network", modo, *(["--tailnet", nome] if nome else []), *(["--login-server", url_h] if modo == "headscale" and url_h else []), "--apply"]
            job = start_job("_host", "network", [qh(*args)], lang, origem=self.client_address[0], continuar=True)
            if job is None:
                return self._json(409, {"error": loc("another job is running")})
            return self._json(202, {"job": job.id})
        if url.path == "/api/health/run":
            unit = d.get("unit", "")
            if not unit_exists(unit):
                return self._json(400, {"error": loc("unknown unit")})
            if PREFIX and "QH_PODMAN" not in os.environ:
                return self._json(409, {"error": loc("not running")})
            if not (inspect_unit(unit) or {}).get("State", {}).get("Running"):
                return self._json(409, {"error": loc("not running")})
            rc, saida, estado = health_run(unit)
            return self._json(200, {"rc": rc, "output": saida, "health": estado})
        if url.path == "/api/images/rm":
            iid = d.get("id", "")
            if not isinstance(iid, str) or not re.fullmatch(r"[0-9a-f]{12,64}", iid):
                return self._json(400, {"error": "id"})
            alvo = next((i for i in images_state() if i["id"] == iid), None)
            if alvo is None:
                return self._json(404, {"error": loc("unknown action")})
            if not alvo["removable"]:
                return self._json(400, {"error": loc("this image is in use or an installed unit asks for it: not removed")})
            job = start_job("_host", "image-rm", [], lang, lambda: image_remove(iid), origem=self.client_address[0])
            if job is None:
                return self._json(409, {"error": loc("another job is running")})
            return self._json(202, {"job": job.id})
        if url.path == "/api/migrate":
            # An install made under an app the repository split (media-stack): moved to the apps that replaced it.
            velho = d.get("from", "")
            if velho not in migrate.MIGRATIONS:
                return self._json(400, {"error": loc("unknown action")})
            casa = Path(PREFIX) if PREFIX else Path.home()
            achados = [x for x in migrate.legacy(casa) if x["from"] == velho]
            if not achados:
                return self._json(404, {"error": loc("nothing to do")})
            novos = [u["new"] for u in achados[0]["units"]]
            job = start_job("_host", "migrate", [qh("--migrate", velho, "--apply")], lang, origem=self.client_address[0], refrescar=novos)
            if job is None:
                return self._json(409, {"error": loc("another job is running")})
            return self._json(202, {"job": job.id, "apps": novos})
        if url.path == "/api/power":
            # Reboot or power off the machine, now or later (polkit lets the logged-in user do it). Not while a job
            # runs: a restart in the middle of an update leaves a half-written unit. The answer goes out first.
            base, rodar = Path(PREFIX or Path.home()), power_run()
            if d.get("action") == "cancel":
                hostctl.cancel(base, rodar)
                return self._json(200, {"scheduled": None})
            verbo = {"reboot": "reboot", "poweroff": "poweroff"}.get(d.get("action", ""))
            if not verbo:
                return self._json(400, {"error": loc("unknown action")})
            if "minutes" in d or "at" in d:
                try:
                    espera = hostctl.delay_of(d.get("minutes"), d.get("at"))
                except ValueError:
                    return self._json(400, {"error": loc("pick a time between a minute and a week from now")})
                feito = hostctl.schedule(base, verbo, espera, rodar)
                if feito is None:
                    return self._json(502, {"error": "systemd-run"})
                return self._json(202, {"scheduled": feito})
            if JOB_LOCK.locked():
                return self._json(409, {"error": loc("another job is running")})
            if not PREFIX:                  # a sandbox does not touch the machine
                threading.Timer(2.0, lambda: subprocess.run(["systemctl", verbo], check=False)).start()
            return self._json(202, {"action": verbo})

        if url.path == "/api/settings":
            modo = d.get("access", "")
            if modo not in I.ACCESS_MODES:
                return self._json(400, {"error": loc("unknown action")})
            cmds = [qh("--set-access", modo)]
            if d.get("apply"):
                # Bring the services that do not follow the new rule in line: an update each, which restarts it.
                cmds += [qh(x, "--update", "--apply") for x in I.access_drift(modo, PREFIX)]
            job = start_job("_host", "settings", cmds, lang, origem=self.client_address[0], continuar=True)
            if job is None:
                return self._json(409, {"error": loc("another job is running")})
            return self._json(202, {"job": job.id})

        if url.path == "/api/update-all":
            # Every installed service with something to take, one after the other: a failure does not stop
            # the rest, and the job says at the end that one did. Backups are not taken here; the box next
            # to a single Update does that, and an update of everything is the sum of those.
            quais = apps_with_update(lang)
            if not quais:
                return self._json(400, {"error": loc("nothing to update")})
            # A header before each service says which one is being updated now.
            cmds = [c for i, (app, tipo) in enumerate(quais, 1) for c in
                    [["echo", f"\n=== [{i}/{len(quais)}] {app} ==="],
                     *(upgrade_cmds(app) if tipo == "upgrade" else [qh(app, "--update", "--apply")])]]
            job = start_job("_host", "update-all", cmds, lang, refrescar=[a for a, _ in quais],
                            origem=self.client_address[0], continuar=True)
            if job is None:
                return self._json(409, {"error": loc("another job is running")})
            return self._json(202, {"job": job.id, "apps": [a for a, _ in quais]})

        if url.path == "/api/run":
            app, action = d.get("app", ""), d.get("action", "")
            if not service_dir(app):
                return self._json(400, {"error": loc("unknown service")})
            extra = flags(app, action, d.get("file", ""))
            if extra is None:
                return self._json(400, {"error": loc("unknown action") if action not in ACOES
                                        else loc("no such backup of this service")})
            recusa = install_refusal(app, lang) if action == "install" else None
            if recusa:
                return self._json(400, {"error": recusa})
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

            # What the manifest's `ask` says about each answer (length, format, a number's range).
            for dono, valores in ((dono_s, segredos), (dono_v, variaveis)):
                for n, v in valores.items():
                    campo = (manifest.load(service_dir(dono[n])).get("ask") or {}).get(n)
                    erro = manifest.check_value(campo, v.strip(), lang) if campo else None
                    if erro:
                        return self._json(400, {"error": f"{n}: {erro}"})

            def prepare():
                for x in cadeia:
                    if provision(x, {n: v for n, v in segredos.items() if dono_s[n] == x},
                                 {n: v for n, v in variaveis.items() if dono_v[n] == x}) is False:
                        return False
                return True
            if action != "install" or not (segredos or variaveis):
                prepare = None
            entrada = None
            if action == "remove" and d.get("purge"):
                # Deleting the data: the service's name typed, the way a restore asks for it, and qh asks it
                # again on its own stdin. Nothing but a typed name reaches `--purge`.
                entrada = d.get("confirm", "")
                if not isinstance(entrada, str) or entrada.strip() != app:
                    return self._json(400, {"error": loc("this deletes the data, secrets and .env: "
                                                         "type the service name to confirm")})
                extra = [*extra, "--purge"]
            if action == "restore":
                # The same guard the terminal has: the name, typed by the person.
                entrada = d.get("confirm", "")
                if not isinstance(entrada, str) or entrada.strip() != app:
                    return self._json(400, {"error": loc("a restore overwrites the data: "
                                                         "type the service name to confirm")})
            nova = d.get("instance")
            if nova:
                base = I.APPS / app
                if (action != "install" or not isinstance(nova, str) or not base.is_dir() or I.instances.is_instance(base)
                        or I.instances.name_problem(app, nova, I.taken_names(Path(PREFIX) if PREFIX else Path.home()))):
                    return self._json(400, {"error": loc("unknown action")})
                extra = [*extra, f"--instance={nova}"]
            escolhas = d.get("options") or {}
            if escolhas:
                ops = (manifest.load(I.APPS / app).get("options") or {})
                if (action != "install" or not isinstance(escolhas, dict)
                        or any(k not in ops or v not in ops[k]["values"] for k, v in escolhas.items())):
                    return self._json(400, {"error": loc("unknown action")})
                extra = [*extra, *(f"--option={k}={v}" for k, v in escolhas.items())]
            cmd = qh(app, *extra, "--apply")
            custom = d.get("custom") or {}
            depois = None
            if custom:
                # A customization made before the install: validated now, against the unit as it will be
                # written, and applied once the install has put the unit there.
                if action != "install" or not isinstance(custom, dict):
                    return self._json(400, {"error": loc("unknown action")})
                planos = {}
                for nome, cfg in custom.items():
                    caminho = next(I.APPS.glob(f"*/{nome}.container"), None) if unit_exists(nome) else None
                    if caminho is None or caminho.parent.name != app:
                        return self._json(400, {"error": loc("unknown unit")})
                    plano = custom_plan(nome, cfg, pre=True)
                    if plano["errors"]:
                        return self._json(400, {"error": f"{nome}: " + "; ".join(plano["errors"]), "errors": plano["errors"]})
                    if plano["text"] is not None:
                        planos[nome] = plano

                def depois(planos=planos):
                    feito = True
                    for nome, plano in planos.items():
                        print(f"\n{loc('applying the customization of')} {nome}:")
                        feito = apply_override(nome, plano["text"], new_volume_dirs(plano["base_text"], plano)) and feito
                    return feito
                if not planos:
                    depois = None
            unidades_proprias = d.get("custom_units") or {}
            if unidades_proprias:
                # The person's own `.container` for a unit of this service, chosen before the install: reviewed now
                # (blocking errors; warnings only with `ack`), written beside the store's settings, and the install
                # then reads it in place of the repository's file.
                if action != "install" or not isinstance(unidades_proprias, dict):
                    return self._json(400, {"error": loc("unknown action")})
                escritos = {}
                for nome, texto in unidades_proprias.items():
                    if not unit_exists(nome) or unit_pasta(nome) != app:
                        return self._json(400, {"error": loc("unknown unit")})
                    rev = unit_review(nome, texto)
                    if rev["errors"]:
                        return self._json(400, {"error": f"{nome}: " + "; ".join(rev["errors"]), **rev})
                    if rev["warnings"] and d.get("ack") is not True:
                        return self._json(400, {"error": loc("confirm the warnings to go on"), "need_ack": True, **rev})
                    if rev["changed"]:
                        escritos[nome] = texto
                if escritos:
                    previo = prepare

                    def prepare(previo=previo, escritos=escritos):
                        for nome, texto in escritos.items():
                            arq = unit_custom_file(nome)
                            arq.parent.mkdir(parents=True, exist_ok=True)
                            arq.write_text(texto)
                            print(f"  {loc('your own .container saved')}: {nome}")
                        return previo() if previo else True
            quando = d.get("trial")
            if quando:
                # Install to try it: qh removes it by itself, by a timer. Only the service asked
                # for — what it pulled in along stays, as it may be somebody else's.
                if action != "install":
                    return self._json(400, {"error": loc("unknown action")})
                try:
                    trials.parse_duration(quando)
                except (ValueError, TypeError) as e:
                    return self._json(400, {"error": str(e)})
                cmd = qh(app, "--apply", "--trial", quando, *(["--trial-purge"] if d.get("trial_purge") else []))
            if action == "upgrade":
                # The version is taken in the repository first — it stays the
                # source, and the change is there to review and commit — then
                # brought to the host by the same --update as always.
                algum, todos = pinning(app)
                if PREFIX and not todos:
                    return self._json(400, {"error": loc("an upgrade edits the repository, "
                                                         "which a sandbox does not have")})
                cmd = upgrade_cmds(app)
            if d.get("backup_first"):
                # Opt-in safety net: the same cold backup the Backups screen makes, then the update.
                # Chained, so a backup that fails stops the update before it touches anything.
                if action not in ("update", "upgrade"):
                    return self._json(400, {"error": loc("unknown action")})
                if not I.Service(app, PREFIX).volume_roots():
                    return self._json(400, {"error": loc("this service keeps no data to back up")})
                antes = qh(app, *flags(app, "backup"), "--apply")
                cmd = [antes, *(cmd if cmd and isinstance(cmd[0], list) else [cmd])]
            if action == "install" and len(cadeia) > 1:
                cmd = [qh(x, "--apply") for x in cadeia[:-1]] + [cmd] if quando else [qh(x, "--apply") for x in cadeia]
            if action == "access":
                # An exception for this service, then the update that writes it
                # into the unit. `default` drops it, back to the rule.
                modo = d.get("mode", "")
                if modo not in I.ACCESS_MODES + ("default",):
                    return self._json(400, {"error": loc("unknown action")})
                cmd = [qh("--set-access", modo, app)]
                if I.Service(app, PREFIX).installed():
                    cmd.append(qh(app, "--update", "--apply"))
            job = start_job(app, action, cmd, lang, prepare, entrada, refrescar=cadeia,
                            origem=self.client_address[0], depois=depois)
        elif url.path == "/api/prune":
            tipo = d.get("kind", "")
            if tipo not in resources.KINDS:
                return self._json(400, {"error": loc("unknown action")})
            if PREFIX and "QH_PODMAN" not in os.environ:
                return self._json(400, {"error": loc("a sandbox has no podman images to prune")})
            # Volumes are data: the word typed, like a restore's service name. The CLI is told it was asked.
            if tipo == "volumes" and d.get("confirm") != "volumes":
                return self._json(400, {"error": loc("removing volumes deletes data: type `volumes` to confirm")})
            cmd = [sys.executable, str(ROOT / "resources.py"), "prune", tipo, "--apply", "--confirmed"]
            if PREFIX:
                cmd += ["--prefix", PREFIX]
            job = start_job("_host", "prune", cmd, lang, origem=self.client_address[0])
        elif url.path == "/api/control":
            # Play, pause and stop for the whole service. Play also lifts a pause; pause freezes the
            # running containers (`podman pause`) and leaves the units active; stop stops every unit
            # of the service together, so no dependency is left writing.
            app, verbo = d.get("app", ""), d.get("verb", "")
            if not service_dir(app):
                return self._json(400, {"error": loc("unknown service")})
            if verbo not in ("play", "pause", "stop"):
                return self._json(400, {"error": loc("unknown action")})
            cmd, acao = control_cmds(app, verbo)
            if not cmd:
                return self._json(400, {"error": loc("nothing to do: it is not installed, or already in that state")})
            job = start_job(app, acao, cmd, lang, origem=self.client_address[0])
        elif url.path == "/api/unit":
            unit, verbo = d.get("unit", ""), d.get("verb", "")
            if not unit_exists(unit):
                return self._json(400, {"error": loc("unknown unit")})
            if verbo not in VERBOS:
                return self._json(400, {"error": loc("unknown action")})
            # The verbs Quadlet units take (rule 4): never enable/disable.
            # Recorded under the service, with the unit beside it, so a service's
            # history holds its restarts as well as its installs.
            pasta = next(I.APPS.glob(f"*/{unit}.container")).parent.name
            if verbo in ("force-stop", "force-restart"):
                job = start_job(pasta, verbo, [], lang, lambda: force_unit(unit, verbo == "force-restart"),
                                origem=self.client_address[0], unit=unit)
                if job is None:
                    return self._json(409, {"error": loc("another job is running")})
                return self._json(202, {"job": job.id})
            cmd_unit = ["systemctl", "--user", verbo, unit]
            if verbo == "stop":
                cmd_unit = ["systemctl", "--user", "mask", "--now", unit]    # stays stopped after a reboot
            if verbo in ("start", "restart") and I.unit_masked(PREFIX or Path.home(), unit):
                cmd_unit = [["systemctl", "--user", "unmask", unit], cmd_unit]     # it was stopped on purpose
            job = start_job(pasta, verbo, cmd_unit, lang,
                            origem=self.client_address[0], unit=unit)
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
            _, _, pagina = pedir("/login?e=1")
            assert b"Token inv\xc3\xa1lido" in pagina and b'role="alert"' in pagina, "a refused token says so"
            _, _, limpa = pedir("/login")
            assert b"erro" not in limpa and b"<!--error-->" not in limpa, "and the plain page does not"
            _, _, tentativa = pedir("/login?e=1%3Cscript%3E")
            assert b"<script>" not in tentativa, "nothing from the query is echoed"
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
            for caminho in ("/api/plan?app=immich&action=upgrade", None):
                if caminho:
                    st, _, _ = pedir(caminho, headers=ok)
                else:
                    st, _, _ = pedir("/api/run", json.dumps(
                        {"app": "immich", "action": "upgrade"}).encode(), api)
                assert st == 400, ("a sandbox never bumps the real repository (immich keeps a pinned sidecar)", st)
            # A service that leaves its version to the host can be upgraded in a sandbox: it edits no repository.
            assert pinning("homebox") == (True, True) and pinning("immich")[0] and not pinning("immich")[1]
            tpl = imagepin.templates(I.Service("homebox", PREFIX).ini)["homebox"]
            os.environ["QH_FAKE_LATEST"] = json.dumps({"homebox": "v9.9.9"})
            try:
                st, _, corpo = pedir("/api/run", json.dumps({"app": "homebox", "action": "upgrade"}).encode(), api)
                assert st == 202, (st, corpo)
                job = json.loads(corpo)["job"]
                for _ in range(300):
                    estado = json.loads(pedir(f"/api/job/{job}", headers=ok)[2])
                    if estado["rc"] is not None:
                        break
                    time.sleep(0.5)
                assert estado["rc"] == 0, estado["output"]
                pino = imagepin.read_pin(Path(tmp, ".config/containers/systemd/homebox.container"))
                assert pino and pino["image"].endswith(":" + imagepin.fill(tpl, "v9.9.9")), pino
            finally:
                os.environ.pop("QH_FAKE_LATEST", None)
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

            # backup before updating: opt-in, only for an update, and the archive is made before the update runs
            assert pedir("/api/run", json.dumps({"app": "homebox", "action": "install", "backup_first": True}).encode(), api)[0] == 400
            antes_n = len(json.loads(pedir("/api/backups?app=homebox", headers=ok)[2])["backups"])
            time.sleep(1.1)          # the archive is named by the second
            st, _, corpo = pedir("/api/run", json.dumps({"app": "homebox", "action": "update", "backup_first": True}).encode(), api)
            assert st == 202, (st, corpo)
            estado = esperar(corpo)
            assert estado["rc"] == 0 and estado["output"].index("tar czf") < estado["output"].index("restart"), estado["output"][:400]
            assert len(json.loads(pedir("/api/backups?app=homebox", headers=ok)[2])["backups"]) == antes_n + 1, "the update made a backup first"

            # play / pause / stop of a whole service, from the state podman reports
            arriba, congelado, parado = {"homebox": "Up 3 hours (healthy)"}, {"homebox": "Up 3 hours (Paused)"}, {}
            assert I.estado_do_container("Up 3 hours (Paused)") == "paused" and I.estado_do_container("Paused") == "paused"
            assert control_cmds("homebox", "pause", arriba) == ([["podman", "pause", "homebox"]], "pause")
            assert control_cmds("homebox", "pause", congelado) == ([], None), "pausing what is paused is nothing to do"
            assert control_cmds("homebox", "play", arriba) == ([], None), "playing what runs is nothing to do"
            assert control_cmds("homebox", "play", congelado) == ([["podman", "unpause", "homebox"]], "resume")
            cmds, acao = control_cmds("homebox", "play", parado)
            assert acao == "start" and cmds == [["systemctl", "--user", "start", "homebox"]], cmds
            cmds, _ = control_cmds("homebox", "stop", congelado)
            assert cmds[0] == ["podman", "unpause", "homebox"] and cmds[-1][:4] == ["systemctl", "--user", "mask", "--now"], "a frozen one is thawed before it is stopped, and masked so a reboot keeps it so"
            cmds, _ = control_cmds("homebox", "stop", parado)
            assert cmds == [["systemctl", "--user", "mask", "--now", "homebox"]], "a stopped one is masked too: it would come back at the next boot"
            masc = Path(tmp, ".config/systemd/user/homebox.service")
            masc.parent.mkdir(parents=True, exist_ok=True)
            masc.symlink_to("/dev/null")
            assert control_cmds("homebox", "stop", parado) == ([], None), "masked already: nothing to do"
            assert control_cmds("homebox", "play", parado)[0] == [["systemctl", "--user", "unmask", "homebox"],
                                                                 ["systemctl", "--user", "start", "homebox"]], "play lifts the mask, then starts"
            masc.unlink()
            assert pedir("/api/control", json.dumps({"app": "homebox", "verb": "dance"}).encode(), api)[0] == 400
            assert pedir("/api/control", json.dumps({"app": "nope", "verb": "stop"}).encode(), api)[0] == 400
            assert pedir("/api/control", json.dumps({"app": "homebox", "verb": "pause"}).encode(), api)[0] == 400, "nothing is running in the sandbox"

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

            # the .env form: only keys the file names, one line, a .bak of what was there
            st, _, corpo = pedir("/api/env?app=homebox", headers=ok)
            arquivos = json.loads(corpo)["files"]
            assert st == 200 and arquivos and arquivos[0]["entries"], corpo
            nome_env, chave = arquivos[0]["file"], arquivos[0]["entries"][0]["key"]
            alvo = Path(tmp, ".config/containers/env", nome_env)
            modo = oct(alvo.stat().st_mode)[-3:]

            def salvar(corpo_json, esperado):
                st, _, resp = pedir("/api/env/save", json.dumps(corpo_json).encode(), api)
                assert st == esperado, (corpo_json, st, resp)
                return resp
            salvar({"app": "homebox", "file": nome_env, "set": {"NAO_EXISTE": "1"}}, 400)
            salvar({"app": "homebox", "file": nome_env, "set": {chave: "a\nB=2"}}, 400)
            salvar({"app": "homebox", "file": "../x.env", "set": {chave: "1"}}, 400)
            salvar({"app": "homebox", "file": nome_env, "off": ["NAO_EXISTE"]}, 400)
            st, _, _ = pedir("/api/env/save", json.dumps({}).encode(), ok)
            assert st == 403, "the form needs the X-QH-Store header too"
            estado = esperar(salvar({"app": "homebox", "file": nome_env, "set": {chave: "valor-novo"}}, 202))
            assert estado["rc"] == 0, estado["output"]
            assert f"{chave}=valor-novo" in alvo.read_text()
            assert oct(alvo.stat().st_mode)[-3:] == modo, "the file keeps its permissions"
            bak = alvo.with_name(alvo.name + ".bak")
            assert bak.is_file() and oct(bak.stat().st_mode)[-3:] == "600", "a private .bak is kept"
            assert f"{chave}=valor-novo" not in bak.read_text(), "and it holds what the file was before"
            estado = esperar(salvar({"app": "homebox", "file": nome_env, "off": [chave]}, 202))
            assert estado["rc"] == 0 and f"# {chave}=valor-novo" in alvo.read_text()
            entrada = next(e for e in json.loads(pedir("/api/env?app=homebox", headers=ok)[2])["files"][0]["entries"]
                           if e["key"] == chave)
            assert not entrada["active"], "a key turned off shows as optional"
            # typed settings: a `# type:` hint gives the box and refuses a value that is not one
            alvo.write_text("# type: number\nCORES=2\n# type: bool\nFLAG=Y\nPLAIN=x\n")
            tip = {e["key"]: e for e in json.loads(pedir("/api/env?app=homebox", headers=ok)[2])["files"][0]["entries"]}
            assert tip["CORES"]["type"] == "number" and tip["PLAIN"]["type"] == "text" and tip["FLAG"]["bool"] == ["Y", "N"], tip
            salvar({"app": "homebox", "file": nome_env, "set": {"CORES": "four"}}, 400)
            assert "CORES=2" in alvo.read_text(), "a refused value changes nothing"
            salvar({"app": "homebox", "file": nome_env, "set": {"FLAG": "maybe"}}, 400)
            esperar(salvar({"app": "homebox", "file": nome_env, "set": {"CORES": "4", "FLAG": "N"}}, 202))
            assert "CORES=4" in alvo.read_text() and "FLAG=N" in alvo.read_text()

            # resources: a sandbox has no host to measure, and no network to ask
            assert json.loads(pedir("/api/stats", headers=ok)[2]) == {"stats": {}}
            assert json.loads(pedir("/api/disk?app=homebox", headers=ok)[2]) == {"bytes": None, "paths": []}
            a = json.loads(pedir("/api/arch?app=homebox", headers=ok)[2])
            assert a["host"] == host_arch() and a["runs"] is None and a["units"][0]["ok"] is None, a

            # links: this repo's recipe for it, and the project where one is known
            lk = {x["kind"]: x["url"] for x in json.loads(pedir("/api/links?app=vaultwarden", headers=ok)[2])["links"]}
            assert lk["repo"] == "https://github.com/dani-garcia/vaultwarden", lk
            assert lk["issues"] == "https://github.com/dani-garcia/vaultwarden/issues" and lk["docs"].startswith("https://"), lk
            assert lk["releases"].endswith("/releases") and lk["image"].startswith("https://hub.docker.com/")
            st, _, _ = pedir("/api/links?app=../x", headers=ok)
            assert st == 400, st

            # customize: a drop-in beside the unit, with rules for what is new
            unidade = Path(tmp, ".config/containers/systemd/homebox.container")
            est = json.loads(pedir("/api/custom?unit=homebox", headers=ok)[2])
            assert est["override"] is False and est["roots"] and est["restart"] == "always", est
            assert "SYS_ADMIN" not in est["caps_ok"] and set(est["limits"]) == {"memory", "cpu"}
            for ruim in ("../x", "nao-existe"):
                assert pedir(f"/api/custom?unit={ruim}", headers=ok)[0] == 400, ruim
            assert pedir("/api/custom?unit=memos", headers=ok)[0] == 404, "a unit that is not installed"

            def cfg(**mudar):
                efet = est["effective"]
                return {"ports": efet["ports"], "volumes": efet["volumes"], "env": efet["env"],
                        "devices": efet["devices"], "caps": efet["caps"], **mudar}

            def previa(c, rota="preview"):
                st, _, corpo = pedir(f"/api/custom/{rota}", json.dumps({"unit": "homebox", "config": c}).encode(), api)
                return st, json.loads(corpo)
            boa = cfg(ports=est["effective"]["ports"] + [{"bind": "", "host": 8123, "container": 7745, "proto": "tcp"}],
                      volumes=est["effective"]["volumes"] + [{"host": "%h/.config/containers/volumes/extra",
                                                               "container": "/extra", "label": "Z", "ro": False, "extra": []}],
                      env=est["effective"]["env"] + [{"key": "NOVA", "value": 'a b $x 100%'}],
                      caps=est["effective"]["caps"] + [{"name": "NET_RAW"}], restart="on-failure")
            st, pre = previa(boa)
            assert st == 200 and not pre["errors"] and pre["changed"], pre
            assert "PublishPort=8123:7745" in pre["text"] and "Restart=on-failure" in pre["text"] and "AddCapability=NET_RAW" in pre["text"]
            assert 'NOVA="a b $$x 100%%"' in pre["text"], pre["text"]
            assert any("rede local" in w for w in pre["warnings"]), "a new published port says it opens the LAN"
            if O.quadlet_binary():
                assert "--publish 8123:7745" in pre["generated"], pre["generated"]
            assert not O.dropin_path(unidade).exists(), "a preview writes nothing"
            texto_boa = pre["text"]

            for ruim, parte in ((cfg(volumes=est["effective"]["volumes"] + [{"host": "/etc", "container": "/e", "label": "Z", "ro": False, "extra": []}]), "fora das pastas"),
                                (cfg(caps=[{"name": "SYS_ADMIN"}]), "lista permitida"),
                                (cfg(ports=[{"bind": "", "host": 80, "container": 80, "proto": "tcp"}]), "a partir da"),
                                (cfg(env=[{"key": "1X", "value": "a"}]), "variável"),
                                (cfg(devices=[{"path": "/dev/nao-existe"}]), "não existe"),
                                (cfg(ports=[{"raw": "8080", "opaque": True}]), "não vem da unit"),
                                (dict(cfg(), restart="sempre"), "reinício")):
                st, pre = previa(ruim)
                assert pre["errors"] and any(parte in e for e in pre["errors"]), (parte, pre["errors"])
                st, rec = previa(ruim, "apply")
                assert st == 400 and not O.dropin_path(unidade).exists(), ("apply refuses what preview refused", parte)
            assert previa({"ports": "nao-lista"})[1]["errors"], "a malformed payload is an error, not a crash"
            st, _, _ = pedir("/api/custom/apply", json.dumps({"unit": "homebox", "config": boa}).encode(), ok)
            assert st == 403, "and it needs the X-QH-Store header like every write"

            st, aplicado = previa(boa, "apply")
            assert st == 202, aplicado
            estado = esperar(json.dumps(aplicado).encode())
            assert estado["rc"] == 0 and "extra" in estado["output"], estado["output"]
            assert O.read_override(unidade) == texto_boa and oct(O.dropin_path(unidade).stat().st_mode)[-3:] == "600"
            assert Path(tmp, ".config/containers/volumes/extra").is_dir(), "the new volume's folder is created"
            est = json.loads(pedir("/api/custom?unit=homebox", headers=ok)[2])
            assert est["override"] and any(i.get("host") == 8123 for i in est["effective"]["ports"]), est["effective"]["ports"]
            assert est["effective"]["env"][-1] == {"key": "NOVA", "value": "a b $x 100%"}, "the value reads back unescaped"
            assert est["restart"] == "on-failure" and est["base_changed"] is False
            hb2 = next(a for a in json.loads(pedir("/api/catalog", headers=ok)[2])["apps"] if a["id"] == "homebox")
            assert hb2["units"][0]["override"] is True, "the catalog says it is customized"
            # saving what the form already shows again is not a conflict with itself
            st, de_novo = previa(cfg(ports=est["effective"]["ports"], volumes=est["effective"]["volumes"],
                                     env=est["effective"]["env"], caps=est["effective"]["caps"], restart="on-failure"))
            assert not de_novo["errors"], de_novo["errors"]

            # the unit moved under the customization: flagged
            antes = O.read_override(unidade)
            O.write_override(unidade, antes.replace(O.recorded_base(antes), "0" * 16))
            assert json.loads(pedir("/api/custom?unit=homebox", headers=ok)[2])["base_changed"] is True
            O.write_override(unidade, antes)

            st, rev = pedir("/api/custom/reset", json.dumps({"unit": "homebox"}).encode(), api)[0:3:2]
            assert st == 202, rev
            assert esperar(rev)["rc"] == 0 and O.read_override(unidade) is None, "revert removes the file"
            assert json.loads(pedir("/api/custom?unit=homebox", headers=ok)[2])["override"] is False

            # limits: offered only where the user's systemd delegates the controllers (a stand-in file says so)
            with tempfile.TemporaryDirectory() as cg:
                falso_cg = Path(cg, "cgroup.controllers")
                lim = {"memory": "512m", "cpus": "1.5"}

                def com_limites(cfg_base):
                    return {**cfg_base, "limits": lim}
                falso_cg.write_text("pids\n")
                os.environ["QH_CGROUP_CONTROLLERS"] = str(falso_cg)
                try:
                    assert json.loads(pedir("/api/custom?unit=homebox", headers=ok)[2])["limits"] == {"memory": False, "cpu": False}
                    st, pre = previa(com_limites(cfg()))
                    assert pre["errors"] and "não delega o controlador memory" in pre["errors"][0], pre
                    assert previa(cfg())[1]["errors"] == [], "a form without limits is not affected"
                    falso_cg.write_text("cpuset cpu io memory pids\n")
                    assert json.loads(pedir("/api/custom?unit=homebox", headers=ok)[2])["limits"] == {"memory": True, "cpu": True}
                    st, pre = previa(com_limites(cfg()))
                    assert not pre["errors"] and "Memory=512m" in pre["text"] and "PodmanArgs=--cpus=1.5" in pre["text"], pre
                    assert "--memory 512m" in pre["generated"] and "--cpus=1.5" in pre["generated"], pre["generated"]
                    st, ap = pedir("/api/custom/apply", json.dumps({"unit": "homebox", "config": com_limites(cfg())}).encode(), api)[0:3:2]
                    assert st == 202 and esperar(ap)["rc"] == 0, ap
                    est2 = json.loads(pedir("/api/custom?unit=homebox", headers=ok)[2])
                    assert est2["limit_values"] == {"memory": "512m", "cpus": "1.5"} and est2["override"], est2
                    st, rev = pedir("/api/custom/reset", json.dumps({"unit": "homebox"}).encode(), api)[0:3:2]
                    assert st == 202 and esperar(rev)["rc"] == 0 and O.read_override(unidade) is None
                finally:
                    os.environ.pop("QH_CGROUP_CONTROLLERS", None)

            # logos and screenshots: served from the app's own folder, behind the login, and nothing else
            logo = manifest.icon_file(I.APPS / "memos")
            assert pedir(f"/assets/memos/{logo}")[0] == 303, "the assets need the login too (redirected to /login)"
            st, h, corpo = pedir(f"/assets/memos/{logo}", headers=ok)
            assert st == 200 and h["Content-Type"] == manifest_tipo(logo) and len(corpo) > 80, (st, h)
            assert "sandbox" in h["Content-Security-Policy"] and "private" in h["Cache-Control"]
            first = sorted((I.APPS / "memos" / "screenshots").glob("1.*"))
            if first:
                assert pedir(f"/assets/memos/screenshots/{first[0].name}", headers=ok)[0] == 200
            for ruim in ("/assets/memos/../../install.py", "/assets/nope/icon.svg", "/assets/memos/app.json",
                         "/assets/memos/screenshots/../app.json", "/assets/memos/memos.container", "/assets/memos/icon.exe"):
                assert pedir(ruim, headers=ok)[0] == 404, ruim
            cat_icone = json.loads(pedir("/api/catalog", headers=ok)[2])["apps"][0]["icon"]
            assert cat_icone.startswith("/assets/"), "the catalog points at the store's own assets"

            # folder picker: only inside the permitted roots, by real path, no symlink out, no hidden, no files
            raiz_v = Path(tmp, ".config/containers/volumes")
            (raiz_v / "meus/dados").mkdir(parents=True, exist_ok=True)
            (raiz_v / ".oculta").mkdir(exist_ok=True)
            (raiz_v / "arquivo.txt").write_text("x")
            with tempfile.TemporaryDirectory() as fora:
                if not (raiz_v / "fuga").exists():
                    (raiz_v / "fuga").symlink_to(fora)
                lr = json.loads(pedir("/api/dirs", headers=ok)[2])
                assert [d["path"] for d in lr["dirs"]] == [os.path.realpath(raiz_v)] and lr["parent"] is None, lr
                lv = json.loads(pedir("/api/dirs?path=" + urllib.parse.quote(lr["dirs"][0]["path"]), headers=ok)[2])
                nomes = [d["name"] for d in lv["dirs"]]
                assert "meus" in nomes and not {".oculta", "arquivo.txt", "fuga"} & set(nomes), lv   # no file, no hidden, no symlink
                assert lv["parent"] is None and lv["at_root"] is True and lv["value"].startswith(("%h", str(tmp))), lv
                sub = json.loads(pedir("/api/dirs?path=" + urllib.parse.quote(next(d["path"] for d in lv["dirs"] if d["name"] == "meus")), headers=ok)[2])
                assert [d["name"] for d in sub["dirs"]] == ["dados"] and sub["parent"] == lv["path"], sub
                assert pedir("/api/dirs?path=" + urllib.parse.quote(lv["path"] + "/../.."), headers=ok)[0] == 400, "no .. out of the root"
                assert pedir("/api/dirs?path=" + urllib.parse.quote(fora), headers=ok)[0] == 400, "a folder outside the roots"
                assert pedir("/api/dirs?path=" + urllib.parse.quote(lv["path"] + "/fuga"), headers=ok)[0] == 400, "a symlink that leads out"
                assert pedir("/api/dirs?path=%25h/.config/containers/volumes/meus", headers=ok)[0] == 200, "%h is understood"
                assert pedir("/api/dirs?path=/etc", headers=ok)[0] == 400
            assert pedir("/api/dirs")[0] == 401, "the picker needs the login too"

            # customize BEFORE the install: the form works on the unit as it will be written; the install
            # applies it once the unit exists; and a preview is the only thing allowed on what is not installed
            assert installed_unit("mailpit") is None
            assert pedir("/api/custom?unit=mailpit", headers=ok)[0] == 404, "without `pre`, an uninstalled unit is still not there"
            pre = json.loads(pedir("/api/custom?unit=mailpit&pre=1", headers=ok)[2])
            assert pre["pre"] is True and pre["override"] is False and pre["effective"]["env"] is not None, pre
            assert pedir("/api/custom/apply", json.dumps({"unit": "mailpit", "pre": True, "config": {}}).encode(), api)[0] == 404, \
                "apply never works on an uninstalled unit"
            cfg_pre = {"ports": pre["effective"]["ports"], "volumes": pre["effective"]["volumes"],
                       "env": pre["effective"]["env"] + [{"key": "PRE_NOVA", "value": "antes"}],
                       "devices": pre["effective"]["devices"], "caps": pre["effective"]["caps"], "restart": "on-failure"}
            st, corpo = pedir("/api/custom/preview", json.dumps({"unit": "mailpit", "pre": True, "config": cfg_pre}).encode(), api)[0:3:2]
            vis = json.loads(corpo)
            assert st == 200 and not vis["errors"] and "PRE_NOVA=antes" in vis["text"] and "base_text" not in vis, vis
            ruim_pre = {**cfg_pre, "env": [{"key": "1ruim", "value": "x"}]}
            st, _, corpo = pedir("/api/run", json.dumps({"app": "mailpit", "action": "install", "custom": {"mailpit": ruim_pre}}).encode(), api)
            assert st == 400 and "variável" in json.loads(corpo)["error"], "a bad customization refuses the install before it starts"
            st, _, corpo = pedir("/api/run", json.dumps({"app": "mailpit", "action": "install", "custom": {"homebox": cfg_pre}}).encode(), api)
            assert st == 400, "a customization of another app's unit does not ride on this install"
            st, _, corpo = pedir("/api/run", json.dumps({"app": "mailpit", "action": "update", "custom": {"mailpit": cfg_pre}}).encode(), api)
            assert st == 400, "only an install takes one"
            proprio = unit_repo_text("mailpit").replace("[Container]", "[Container]\nLabel=qh.meu=sim", 1)
            perigo = proprio.replace("[Container]", "[Container]\nPodmanArgs=--privileged", 1)
            for ruim_u, esperado in (({"homebox": proprio}, 400), ({"mailpit": ""}, 400), ({"mailpit": "[Service]\nRestart=no\n"}, 400), ({"mailpit": perigo}, 400)):
                st, _, corpo = pedir("/api/run", json.dumps({"app": "mailpit", "action": "install", "custom_units": ruim_u}).encode(), api)
                assert st == esperado, (ruim_u, st, corpo)
            assert json.loads(pedir("/api/run", json.dumps({"app": "mailpit", "action": "install", "custom_units": {"mailpit": perigo}}).encode(), api)[2])["need_ack"] is True
            assert pedir("/api/run", json.dumps({"app": "mailpit", "action": "update", "custom_units": {"mailpit": proprio}}).encode(), api)[0] == 400, "only an install takes one"
            assert not unit_custom_file("mailpit").is_file(), "a refused install writes nothing"
            st, _, corpo = pedir("/api/run", json.dumps({"app": "mailpit", "action": "install", "custom": {"mailpit": cfg_pre},
                                                         "custom_units": {"mailpit": proprio}}).encode(), api)
            assert st == 202, (st, corpo)
            job = json.loads(corpo)["job"]
            for _ in range(600):
                estado = json.loads(pedir(f"/api/job/{job}", headers=ok)[2])
                if estado["rc"] is not None:
                    break
                time.sleep(0.5)
            assert estado["rc"] == 0 and "mailpit" in estado["output"], estado["output"][-400:]
            gravado = O.read_override(installed_unit("mailpit"))
            assert gravado and "PRE_NOVA=antes" in gravado and "Restart=on-failure" in gravado, gravado
            assert unit_custom_file("mailpit").read_text() == proprio and "qh.meu=sim" in installed_unit("mailpit").read_text(), "the install used the person's own unit"
            assert json.loads(pedir("/api/catalog", headers=ok)[2])["apps"] and I.Service("mailpit", PREFIX).has_custom_unit("mailpit.container")

            # the panel on its own: settings (the access rule), update everything, delete the data with a typed name
            def espera_job(corpo_json):
                job = json.loads(corpo_json)["job"]
                for _ in range(600):
                    est = json.loads(pedir(f"/api/job/{job}", headers=ok)[2])
                    if est["rc"] is not None:
                        return est
                    time.sleep(0.5)
            cfg0 = json.loads(pedir("/api/settings", headers=ok)[2])
            assert cfg0["access"] == "tailnet" and cfg0["modes"] == ["local", "tailnet", "both"] and cfg0["tailnet"] is False, cfg0
            assert pedir("/api/settings", json.dumps({"access": "lan"}).encode(), api)[0] == 400
            st, _, corpo = pedir("/api/settings", json.dumps({"access": "both"}).encode(), api)
            assert st == 202 and espera_job(corpo)["rc"] == 0
            cfg1 = json.loads(pedir("/api/settings", headers=ok)[2])
            assert cfg1["access"] == "both" and cfg1["default"] is False, cfg1
            st, _, corpo = pedir("/api/settings", json.dumps({"access": "tailnet"}).encode(), api)
            assert espera_job(corpo)["rc"] == 0
            # network: the state is readable, a bad choice is refused, and a good one starts the qh job
            n0 = json.loads(pedir("/api/network", headers=ok)[2])
            assert n0["mode"] == "tailscale" and n0["chosen"] is False and n0["tailscale"]["installed"] in (True, False) and "commands" in n0, n0
            assert pedir("/api/network", json.dumps({"mode": "wireguard"}).encode(), api)[0] == 400
            assert pedir("/api/network", json.dumps({"mode": "headscale", "tailnet": ""}).encode(), api)[0] == 400, "Headscale needs a name"
            assert pedir("/api/network", json.dumps({"mode": "headscale", "tailnet": "casa", "server_url": "ftp://x"}).encode(), api)[0] == 400
            st, _, c = pedir("/api/network", json.dumps({"mode": "local"}).encode(), api)
            assert st == 202, c
            jn = json.loads(c)["job"]
            for _ in range(200):
                est = json.loads(pedir(f"/api/job/{jn}", headers=ok)[2])
                if est["rc"] is not None:
                    break
                time.sleep(0.2)
            assert est["rc"] == 0 and "network: local" in est["output"], est["output"][-300:]
            assert N.load(Path(tmp))["mode"] == "local" and json.loads(pedir("/api/network", headers=ok)[2])["mode"] == "local"
            N.save(Path(tmp), {"mode": "tailscale", "server_url": "", "tailnet": ""})
            pedir("/api/settings", json.dumps({"access": "tailnet"}).encode(), api)

            # service widgets: the address from the catalog, the credential from the panel, never sent back
            falso_cat = [{"id": "immich", "main_unit": "immich", "web": [{"unit": "immich", "local": "http://x:2283", "tailnet": None}],
                          "units": [{"unit": "immich", "installed": True}]},
                         {"id": "sonarr", "main_unit": "sonarr", "web": [{"unit": "sonarr", "local": "http://x:8989", "tailnet": "https://sonarr.t"}],
                          "units": [{"unit": "sonarr", "installed": True}]}]
            pedidos = []
            def api_falsa(u, h=None):
                pedidos.append((u, h))
                return {"photos": 3, "videos": 1, "usage": 10} if "statistics" in u else {"totalRecords": 4} if "pageSize" in u else [{}]
            st0 = svc_state(apps=falso_cat, get=api_falsa)
            assert [x["type"] for x in st0["immich"]] == ["immich"] and [x["type"] for x in st0["sonarr"]] == ["sonarr"], "the widgets of an installed app"
            assert st0["immich"][0]["configured"] is False and "fields" not in st0["immich"][0] and not pedidos, "nothing is asked without a key"
            antes_cat = catalog
            globals()["catalog"] = lambda lang="en": {"apps": falso_cat}
            try:
                assert pedir("/api/svc/config", json.dumps({"app": "immich", "slot": "immich", "values": {"password": "x"}}).encode(), api)[0] == 400, "only the fields the type takes"
                assert pedir("/api/svc/config", json.dumps({"app": "immich", "slot": "nope", "values": {"key": "x"}}).encode(), api)[0] == 400
                assert pedir("/api/svc/config", json.dumps({"app": "immich", "slot": "immich", "values": {"url": "ftp://x"}}).encode(), api)[0] == 400
                st, _, c = pedir("/api/svc/config", json.dumps({"app": "immich", "slot": "immich", "values": {"key": "segredo-123"}}).encode(), api)
                assert st == 200 and b"segredo-123" not in c, "the key never comes back"
                assert W.load(Path(tmp))["immich"] == {"key": "segredo-123"}
                pedir("/api/svc/config", json.dumps({"app": "sonarr", "slot": "sonarr", "values": {"key": "k2"}}).encode(), api)
                lido = svc_state(apps=falso_cat, get=api_falsa)
                assert {x["key"]: x["value"] for x in lido["immich"][0]["fields"]} == {"photos": 3, "videos": 1, "storage": 10}, lido
                assert pedidos[0] == ("http://x:2283/api/server/statistics", {"x-api-key": "segredo-123"})
                assert any(u.startswith("https://sonarr.t/api/v3/") for u, _ in pedidos), "the tailnet address first, when there is one"
                pedir("/api/svc/config", json.dumps({"app": "immich", "slot": "immich", "values": {"key": ""}}).encode(), api)
                assert W.load(Path(tmp))["immich"] == {"key": "segredo-123"}, "an empty box keeps the key"
                pedir("/api/svc/config", json.dumps({"app": "immich", "slot": "immich", "values": {"clear": True}}).encode(), api)
                assert W.load(Path(tmp))["immich"] == {}, "clear forgets it"
            finally:
                globals()["catalog"] = antes_cat

            # site monitor: up when it answers below a 500 (a 401 login page is up), down when nothing answers
            class Site(BaseHTTPRequestHandler):
                def do_HEAD(self):
                    codigo = {"/up": 200, "/login": 401, "/nohead": 405, "/broken": 502}[self.path]
                    self.send_response(codigo); self.end_headers()
                def do_GET(self):
                    self.send_response(200); self.end_headers()
                def log_message(self, *a): pass
            site = ThreadingHTTPServer(("127.0.0.1", 0), Site)
            threading.Thread(target=site.serve_forever, daemon=True).start()
            raiz = f"http://127.0.0.1:{site.server_address[1]}"
            assert probe(raiz + "/up")["ok"] and probe(raiz + "/login")["ok"], "answering, even with a login page, is up"
            sem_head = probe(raiz + "/nohead")
            assert sem_head["ok"] is True and sem_head["status"] == 200, "a refused HEAD falls back to GET"
            assert probe(raiz + "/broken")["ok"] is False and probe(raiz + "/broken")["status"] == 502
            assert probe("http://127.0.0.1:1/")["ok"] is False and probe("http://127.0.0.1:1/")["status"] is None, "nothing listening is down"
            site.shutdown()
            assert json.loads(pedir("/api/monitor", headers=ok)[2]) == {"apps": {}}, "a sandbox monitors nothing"

            # appearance: validated, kept on the server; the background is sniffed by its bytes, served only after login
            u0 = json.loads(pedir("/api/ui", headers=ok)[2])
            assert u0["theme"] == "system" and u0["accent"] == "blue" and u0["icon_size"] == "medium" and u0["depth"] == "flat" and u0["background"] is False, u0
            assert pedir("/api/ui", json.dumps({"theme": "neon"}).encode(), api)[0] == 400
            assert pedir("/api/ui", json.dumps({"bg_blur": 99}).encode(), api)[0] == 400
            assert pedir("/api/ui", json.dumps({"icon_size": "huge"}).encode(), api)[0] == 400 and pedir("/api/ui", json.dumps({"depth": "x"}).encode(), api)[0] == 400
            assert pedir("/style.css")[0] == 200 and pedir("/fonts/jakarta.woff2")[2][:4] == b"wOF2", "the login page draws with the stylesheet and the font, signed out"
            assert pedir("/api/ui", json.dumps({"nope": 1}).encode(), api)[0] == 400
            st, _, c = pedir("/api/ui", json.dumps({"theme": "dark", "accent": "teal", "density": "compact", "lang": "pt"}).encode(), api)
            assert st == 200 and json.loads(c)["accent"] == "teal" and json.loads(pedir("/api/ui", headers=ok)[2])["density"] == "compact"
            png = b"\x89PNG\r\n\x1a\n" + b"\0" * 64
            assert pedir("/api/ui/background", b"<svg onload=alert(1)>", api)[0] == 400, "only PNG, JPEG or WebP, by their bytes"
            st, _, c = pedir("/api/ui/background", png, api)
            assert st == 200 and json.loads(c)["background"] is True
            assert pedir("/ui/background")[0] in (303, 401), "the background needs the login too"
            st, cab, c = pedir("/ui/background", headers=ok)
            assert st == 200 and c == png and cab.get("Content-Type") == "image/png", (st, cab)
            assert json.loads(pedir("/api/ui/background", b"", api)[2])["background"] is False, "an empty body removes it"
            pedir("/api/ui", json.dumps({"theme": "system", "accent": "blue", "density": "comfortable"}).encode(), api)

            # alerts: opt-in, validated, the token never comes back, a test message reaches the ntfy topic
            recebido = []
            class Ntfy(BaseHTTPRequestHandler):
                def do_POST(self):
                    recebido.append((self.path, self.headers.get("Authorization"), self.rfile.read(int(self.headers["Content-Length"]))))
                    self.send_response(200); self.end_headers()
                def log_message(self, *a): pass
            ntfy = ThreadingHTTPServer(("127.0.0.1", 0), Ntfy)
            threading.Thread(target=ntfy.serve_forever, daemon=True).start()
            al0 = json.loads(pedir("/api/alerts", headers=ok)[2])
            assert al0["config"]["enabled"] is False and "token" not in al0["config"], al0
            assert pedir("/api/alerts", json.dumps({"enabled": True}).encode(), api)[0] == 400, "on needs a server and a topic"
            assert pedir("/api/alerts/test", b"{}", api)[0] == 400
            corpo_al = {"enabled": True, "server": f"http://127.0.0.1:{ntfy.server_address[1]}", "topic": "lab", "token": "tk_abc"}
            st, _, c = pedir("/api/alerts", json.dumps(corpo_al).encode(), api)
            assert st == 200 and json.loads(c)["config"]["has_token"] is True and b"tk_abc" not in c, c
            assert b"tk_abc" not in pedir("/api/alerts", headers=ok)[2]
            st, _, c = pedir("/api/alerts", json.dumps({"disk_percent": 80}).encode(), api)
            assert st == 200 and A.load(Path(tmp))["token"] == "tk_abc" and A.load(Path(tmp))["disk_percent"] == 80, "the token stays when the form leaves it blank"
            assert pedir("/api/alerts/test", b"{}", api)[0] == 200
            assert recebido and recebido[0][0] == "/lab" and recebido[0][1] == "Bearer tk_abc", recebido
            ntfy.shutdown()
            pedir("/api/alerts", json.dumps({"enabled": False}).encode(), api)
            assert pedir("/api/update-all", b"{}", api)[0] == 400, "nothing to update in the sandbox"
            antes_apps, apps_with_update_orig = None, apps_with_update
            try:
                globals()["apps_with_update"] = lambda lang="en": [("homebox", "update")]
                st, _, corpo = pedir("/api/update-all", b"{}", api)
                assert st == 202 and json.loads(corpo)["apps"] == ["homebox"], corpo
                est = espera_job(corpo)
                assert est["rc"] == 0 and "=== [1/1] homebox ===" in est["output"], est["output"][-300:]
            finally:
                globals()["apps_with_update"] = apps_with_update_orig
            # ask: a value that breaks the manifest's rule is refused before anything is installed
            st, _, corpo = pedir("/api/run", json.dumps({"app": "vaultwarden", "action": "install",
                                                        "secrets": {"vaultwarden-admin-token": "plain"}, "vars": {}}).encode(), api)
            assert st == 400 and "vaultwarden-admin-token" in json.loads(corpo)["error"] and "argon2" in json.loads(corpo)["error"].lower(), corpo
            cat_v = next(a for a in json.loads(pedir("/api/catalog", headers=ok)[2])["apps"] if a["id"] == "vaultwarden")
            assert cat_v["asks"]["secrets"][0]["field"]["required"] is True, "the catalog carries the ask entry"

            # power: only the two known verbs, and not while a job runs (a sandbox never touches the machine)
            assert pedir("/api/power", json.dumps({"action": "halt"}).encode(), api)[0] == 400
            assert pedir("/api/power", json.dumps({"action": "reboot"}).encode(), api)[0] == 202
            JOB_LOCK.acquire()
            try:
                assert pedir("/api/power", json.dumps({"action": "poweroff"}).encode(), api)[0] == 409, "busy: no power action"
            finally:
                JOB_LOCK.release()
            # scheduled power: armed, listed, replaced and cancelled; bad times refused (a sandbox never calls systemd)
            assert json.loads(pedir("/api/power", headers=ok)[2]) == {"scheduled": None}
            st, _, corpo = pedir("/api/power", json.dumps({"action": "reboot", "minutes": 30}).encode(), api)
            assert st == 202 and json.loads(corpo)["scheduled"]["action"] == "reboot", corpo
            assert json.loads(pedir("/api/power", headers=ok)[2])["scheduled"]["action"] == "reboot"
            assert pedir("/api/power", json.dumps({"action": "poweroff", "at": "03:30"}).encode(), api)[0] == 202
            assert json.loads(pedir("/api/power", headers=ok)[2])["scheduled"]["action"] == "poweroff", "the new one replaces the old"
            assert pedir("/api/power", json.dumps({"action": "reboot", "minutes": 0}).encode(), api)[0] == 400
            assert pedir("/api/power", json.dumps({"action": "reboot", "at": "25:00"}).encode(), api)[0] == 400
            assert pedir("/api/power", json.dumps({"action": "cancel"}).encode(), api)[0] == 200
            assert json.loads(pedir("/api/power", headers=ok)[2]) == {"scheduled": None}
            # files: the app's volume folders, listed, previewed and downloaded; nothing outside them, no links
            apps_f = json.loads(pedir("/api/files", headers=ok)[2])["entries"]
            assert apps_f and all(e["type"] == "dir" for e in apps_f), apps_f
            dono = apps_f[0]["name"]
            raizes = json.loads(pedir(f"/api/files?path={dono}", headers=ok)[2])["entries"]
            assert raizes and raizes[0]["type"] == "dir", raizes
            vol = Path(tmp, ".config/containers/volumes", raizes[0]["name"])
            (vol / "sub").mkdir(parents=True, exist_ok=True)
            (vol / "sub/a.txt").write_text("olá\n"); (vol / "sub/b.bin").write_bytes(b"\x00\x01")
            os.symlink("/etc/passwd", vol / "sub/pw")
            base_f = f"{dono}/{raizes[0]['name']}"
            lista = json.loads(pedir(f"/api/files?path={urllib.parse.quote(base_f + '/sub')}", headers=ok)[2])
            assert [e["name"] for e in lista["entries"]] == ["a.txt", "b.bin", "pw"] and lista["entries"][2]["type"] == "link", lista
            pv = json.loads(pedir(f"/api/files/preview?path={urllib.parse.quote(base_f + '/sub/a.txt')}", headers=ok)[2])
            assert pv["text"] == "olá\n", pv
            assert pedir(f"/api/files/preview?path={urllib.parse.quote(base_f + '/sub/b.bin')}", headers=ok)[0] == 415
            st, h, corpo = pedir(f"/api/files/download?path={urllib.parse.quote(base_f + '/sub/a.txt')}", headers=ok)
            assert st == 200 and corpo == "olá\n".encode() and "attachment" in h["Content-Disposition"], (st, corpo)
            (vol / "sub/p.png").write_bytes(b"\x89PNG")
            st, h, c = pedir(f"/api/files/download?path={urllib.parse.quote(base_f + '/sub/p.png')}&inline=1", headers=ok)
            assert st == 200 and h["Content-Type"] == "image/png" and h["Content-Disposition"].startswith("inline"), dict(h)
            st, h, c = pedir(f"/api/files/download?path={urllib.parse.quote(base_f + '/sub/a.txt')}&inline=1", headers=ok)
            assert h["Content-Type"] == "application/octet-stream" and h["Content-Disposition"].startswith("attachment"), "only images are shown inline"
            for ruim in (base_f + "/sub/pw", base_f + "/../x", dono + "/nope", "nope", base_f + "/sub/missing"):
                assert pedir(f"/api/files?path={urllib.parse.quote(ruim)}", headers=ok)[0] in (400, 404), ruim
                assert pedir(f"/api/files/download?path={urllib.parse.quote(ruim)}", headers=ok)[0] in (400, 404), ruim
            assert pedir("/api/files/download?path=" + urllib.parse.quote(base_f), headers=ok)[0] == 400, "a folder is not a download"
            cat_p = json.loads(pedir("/api/catalog", headers=ok)[2])
            assert cat_p["podman_recommended"] == I.RECOMMENDED_PODMAN and isinstance(cat_p["podman_outdated"], bool), "the catalog says which Podman it was verified on"
            # migrate: an install made under media-stack is found, offered and moved to the apps that replaced it
            assert json.loads(pedir("/api/catalog", headers=ok)[2])["legacy"] == [], "no old install here"
            assert pedir("/api/migrate", json.dumps({"from": "nope"}).encode(), api)[0] == 400
            assert pedir("/api/migrate", json.dumps({"from": "media-stack"}).encode(), api)[0] == 404, "nothing to move"
            velho_d = Path(tmp, ".config/containers/systemd/media-stack"); velho_d.mkdir(parents=True)
            (velho_d / "media-stack-sonarr.container").write_text("[Container]\nImage=x\nVolume=%h/.config/containers/volumes/media-stack/sonarr/config:/config:Z\n")
            Path(tmp, ".config/containers/volumes/media-stack/sonarr/config").mkdir(parents=True)
            Path(tmp, ".config/containers/volumes/media-stack/sonarr/config/db").write_text("data")
            lg = json.loads(pedir("/api/catalog", headers=ok)[2])["legacy"]
            assert lg and lg[0]["from"] == "media-stack" and [u["new"] for u in lg[0]["units"]] == ["sonarr"], lg
            st, _, c = pedir("/api/migrate", json.dumps({"from": "media-stack"}).encode(), api)
            assert st == 202 and json.loads(c)["apps"] == ["sonarr"], c
            est_m = espera_job(c)
            assert est_m["rc"] == 0, est_m["output"][-500:]
            assert Path(tmp, ".config/containers/volumes/sonarr/config/db").read_text() == "data" and installed_unit("sonarr") is not None
            assert json.loads(pedir("/api/catalog", headers=ok)[2])["legacy"] == [], "moved: nothing old is left"
            assert pedir("/api/migrate", json.dumps({"from": "media-stack"}).encode(), ok)[0] == 403, "needs the CSRF header"
            # drift: what the repository changed since the install, as a diff the panel shows before the update
            d_ok = json.loads(pedir("/api/drift?unit=homebox", headers=ok)[2])
            assert d_ok["changed"] is False and d_ok["diff"] == "", d_ok
            inst_h = installed_unit("homebox"); texto_h = inst_h.read_text()
            inst_h.write_text(texto_h.replace("[Container]", "[Container]\nLabel=stale=1", 1))
            d_ch = json.loads(pedir("/api/drift?unit=homebox", headers=ok)[2])
            inst_h.write_text(texto_h)
            assert d_ch["changed"] is True and "-Label=stale=1" in d_ch["diff"] and d_ch["diff"].startswith("--- installed"), d_ch
            assert pedir("/api/drift?unit=memos", headers=ok)[0] == 404 and pedir("/api/drift?unit=nope", headers=ok)[0] == 400
            # the unit as text: reviewed, saved as the person's own, applied by qh, and put back
            rep = json.loads(pedir("/api/custom?unit=homebox", headers=ok)[2])
            assert rep["custom_unit"] is False and rep["unit_source"] == rep["repo_text"] and "[Container]" in rep["repo_text"], rep.keys()
            def rev(texto, caminho="unit-check", **extra):
                return pedir(f"/api/custom/{caminho}", json.dumps({"unit": "homebox", "text": texto, **extra}).encode(), api)
            st, _, c = rev(rep["repo_text"])
            assert st == 200 and json.loads(c) == {"errors": [], "warnings": [], "changed": False}, c
            st, _, c = rev(rep["repo_text"] + "\n# a note\n")
            assert json.loads(c)["changed"] is True and not json.loads(c)["errors"] and not json.loads(c)["warnings"], c
            assert json.loads(rev("")[2])["errors"] and json.loads(rev("[Service]\nRestart=always\n")[2])["errors"], "no Image: refused"
            risco = rep["repo_text"].replace("[Container]", "[Container]\nPodmanArgs=--privileged\nAddCapability=SYS_ADMIN", 1)
            avisos = json.loads(rev(risco)[2])["warnings"]
            assert any("--privileged" in a for a in avisos) and any("SYS_ADMIN" in a for a in avisos), avisos
            assert any("ExecStartPre" in a for a in json.loads(rev(rep["repo_text"] + "\n[Service]\nExecStartPre=/bin/true\n")[2])["warnings"])
            st, _, c = rev(risco, "unit-save")
            assert st == 400 and json.loads(c)["need_ack"] is True and not unit_custom_file("homebox").is_file(), "warnings need a yes"
            assert rev("", "unit-save")[0] == 400
            st, _, c = rev(risco, "unit-save", ack=True)
            assert st == 202, c
            est_u = espera_job(c)
            assert est_u["rc"] == 0, est_u["output"][-600:]
            assert unit_custom_file("homebox").read_text() == risco and "--privileged" in installed_unit("homebox").read_text(), "qh wrote the unit from it"
            rep2 = json.loads(pedir("/api/custom?unit=homebox", headers=ok)[2])
            assert rep2["custom_unit"] is True and rep2["unit_source"] == risco and rep2["repo_text"] == rep["repo_text"]
            st, _, c = rev(rep["repo_text"], "unit-save")
            assert st == 202 and espera_job(c)["rc"] == 0 and not unit_custom_file("homebox").is_file(), "the repository's own text is not custom"
            assert "--privileged" not in installed_unit("homebox").read_text()
            assert espera_job(rev(risco, "unit-save", ack=True)[2])["rc"] == 0 and unit_custom_file("homebox").is_file()
            st, _, c = pedir("/api/custom/unit-reset", json.dumps({"unit": "homebox"}).encode(), api)
            assert st == 202 and espera_job(c)["rc"] == 0 and not unit_custom_file("homebox").is_file(), "reset goes back to the repository's"
            assert pedir("/api/custom/unit-save", json.dumps({"unit": "memos", "text": "x"}).encode(), api)[0] in (400, 404)
            assert pedir("/api/custom/unit-save", json.dumps({"unit": "homebox", "text": risco}).encode(), ok)[0] == 403, "needs the CSRF header"
            # files, changing them: create, upload (whole or cut), rename, copy, move and delete; nothing leaves the volume
            Q = urllib.parse.quote
            def op(**d):
                return pedir("/api/files/op", json.dumps(d).encode(), api)
            assert op(op="mkdir", path=base_f, name="docs")[0] == 200 and (vol / "docs").is_dir()
            assert op(op="mkdir", path=base_f, name="docs")[0] == 409
            assert op(op="mkdir", path=base_f, name="../x")[0] == 400
            assert op(op="mkdir", path=dono, name="x")[0] == 400, "no folder is chosen above the volumes"
            assert pedir("/api/files/op", json.dumps({"op": "mkdir", "path": base_f, "name": "z"}).encode(), ok)[0] == 403, "the CSRF header is needed"
            st, _, c = pedir(f"/api/files/upload?path={Q(base_f + '/docs')}&name=r.txt", b"12345", api)
            assert st == 200 and json.loads(c) == {"name": "r.txt"} and (vol / "docs/r.txt").read_bytes() == b"12345", (st, c)
            st, _, c = pedir(f"/api/files/upload?path={Q(base_f + '/docs')}&name=r.txt", b"67", api)
            assert json.loads(c) == {"name": "r (1).txt"}, "a taken name is not overwritten"
            st, _, c = pedir(f"/api/files/upload?path={Q(base_f + '/docs')}&name=r.txt&overwrite=1", b"new", api)
            assert (vol / "docs/r.txt").read_bytes() == b"new"
            assert pedir(f"/api/files/upload?path={Q(base_f + '/docs')}&name=..%2Fx", b"1", api)[0] == 400
            assert pedir(f"/api/files/upload?path={Q(base_f + '/sub/pw')}&name=x", b"1", api)[0] == 400, "not into a link"
            assert pedir(f"/api/files/upload?path={Q(dono)}&name=x", b"1", api)[0] == 400
            assert op(op="rename", path=base_f + "/docs/r.txt", name="s.txt")[0] == 200 and (vol / "docs/s.txt").exists()
            assert op(op="copy", path=base_f + "/docs/s.txt", to=base_f + "/sub")[0] == 200 and (vol / "sub/s.txt").exists()
            assert op(op="move", path=base_f + "/docs", to=base_f + "/sub")[0] == 200 and (vol / "sub/docs/s.txt").exists() and not (vol / "docs").exists()
            assert op(op="move", path=base_f + "/sub", to=base_f + "/sub/docs")[0] == 400, "a folder does not go into itself"
            assert op(op="delete", path=base_f + "/sub/docs")[0] == 200 and not (vol / "sub/docs").exists()
            assert op(op="delete", path=base_f)[0] == 400, "the volume itself is not deleted"
            assert op(op="delete", path=base_f + "/sub/pw")[0] == 200 and not os.path.lexists(vol / "sub/pw") and Path("/etc/passwd").exists(), "a link goes, its target stays"
            assert op(op="delete", path=base_f + "/nope")[0] == 404
            assert op(op="wat", path=base_f)[0] == 400
            # read-only roots: the units and the .env files can be looked at, never changed; the secrets are not reachable
            Path(tmp, ".config/containers/env").mkdir(parents=True, exist_ok=True)
            Path(tmp, ".config/containers/env/x.env").write_text("A=1\n")
            Path(tmp, ".config/containers/secrets/x").mkdir(parents=True, exist_ok=True)
            Path(tmp, ".config/containers/secrets/x/token.txt").write_text("SECRET")
            topo = [e["name"] for e in json.loads(pedir("/api/files", headers=ok)[2])["entries"]]
            assert "@systemd" in topo and "@env" in topo and not any("secret" in n for n in topo), topo
            lista_env = [e["name"] for e in json.loads(pedir("/api/files?path=%40env", headers=ok)[2])["entries"]]
            assert "x.env" in lista_env, lista_env
            assert json.loads(pedir("/api/files/preview?path=%40env%2Fx.env", headers=ok)[2])["text"] == "A=1\n"
            assert pedir("/api/files/download?path=%40env%2Fx.env", headers=ok)[2] == b"A=1\n"
            for corpo_ro in ({"op": "mkdir", "path": "@env", "name": "n"}, {"op": "delete", "path": "@env/x.env"},
                             {"op": "rename", "path": "@env/x.env", "name": "y"}, {"op": "copy", "path": base_f + "/sub/a.txt", "to": "@env"},
                             {"op": "move", "path": "@systemd/nope", "to": base_f}):
                assert pedir("/api/files/op", json.dumps(corpo_ro).encode(), api)[0] == 403, corpo_ro
            assert pedir("/api/files/upload?path=%40env&name=n", b"1", api)[0] == 403
            assert Path(tmp, ".config/containers/env/x.env").read_text() == "A=1\n" and not Path(tmp, ".config/containers/env/n").exists()
            for fora in ("@secrets", "@secrets/x", "@env/../secrets/x/token.txt"):
                assert pedir(f"/api/files?path={urllib.parse.quote(fora)}", headers=ok)[0] in (400, 404), fora
            os.symlink(Path(tmp, ".config/containers/secrets"), Path(tmp, ".config/containers/env/linked"))
            assert pedir("/api/files?path=%40env%2Flinked", headers=ok)[0] == 400, "a link into the secrets is not followed"
            assert pedir("/api/files/download?path=%40env%2Flinked%2Fx%2Ftoken.txt", headers=ok)[0] == 400
            os.unlink(Path(tmp, ".config/containers/env/linked"))
            # disk usage: the volumes of an installed app, summed
            uso = json.loads(pedir("/api/usage?refresh=1", headers=ok)[2])
            assert all(set(x) == {"app", "bytes"} for x in uso["apps"]) and uso["at"] > 0, uso
            # the running job can be found again after its window was closed
            assert json.loads(pedir("/api/jobs/active", headers=ok)[2]) == {"job": None}, "nothing running"
            lento = start_job("_host", "update-all", [["sleep", "1"]], "en")
            vivo = json.loads(pedir("/api/jobs/active", headers=ok)[2])["job"]
            assert vivo and vivo["id"] == lento.id and vivo["action"] == "update-all", vivo
            for _ in range(100):
                if lento.rc is not None:
                    break
                time.sleep(0.1)
            assert json.loads(pedir("/api/jobs/active", headers=ok)[2]) == {"job": None}, "finished is not running"
            # a failing command does not stop the ones after it, and the job still ends as failed
            j = start_job("_host", "update-all", [["sh", "-c", "echo first; exit 3"], ["echo", "second"]], "en", continuar=True)
            for _ in range(100):
                if j.rc is not None:
                    break
                time.sleep(0.1)
            assert j.rc == 3 and "first" in "".join(j.out) and "second" in "".join(j.out), (j.rc, j.out)
            # delete the data: the name typed, twice (here and in qh), and only for an installed service
            assert installed_unit("mailpit") is not None
            for confirma in (None, "outro", ""):
                corpo_p = {"app": "mailpit", "action": "remove", "purge": True, **({"confirm": confirma} if confirma is not None else {})}
                assert pedir("/api/run", json.dumps(corpo_p).encode(), api)[0] == 400, confirma
            assert installed_unit("mailpit") is not None, "a refused purge touches nothing"
            plano_p = json.loads(pedir("/api/plan?app=mailpit&action=remove&purge=1", headers=ok)[2])
            assert "DELETE DATA" in plano_p["output"] or "APAGA" in plano_p["output"].upper(), plano_p["output"][:200]
            st, _, corpo = pedir("/api/run", json.dumps({"app": "mailpit", "action": "remove", "purge": True, "confirm": "mailpit"}).encode(), api)
            assert st == 202, (st, corpo)
            assert espera_job(corpo)["rc"] == 0 and installed_unit("mailpit") is None, "the typed name deletes it"
            assert not Path(tmp, ".config/containers/volumes/mailpit").exists(), "and its data"

            # deprecated: a service marked in app.json is not offered for install, but stays manageable
            with tempfile.TemporaryDirectory() as dep:
                copia = Path(dep, "apps")
                shutil.copytree(I.APPS, copia, ignore_dangling_symlinks=True)
                for nome in ("memos", "homebox"):
                    dados = manifest.load(copia / nome)
                    dados["deprecated"] = "Archived upstream."
                    manifest.path_of(copia / nome).write_text(manifest.dump(dados))
                original, I.APPS = I.APPS, copia
                try:
                    st, _, corpo = pedir("/api/run", json.dumps({"app": "memos", "action": "install"}).encode(), api)
                    assert st == 400 and "Archived upstream." in json.loads(corpo)["error"], (st, corpo)
                    st, _, corpo = pedir("/api/run", json.dumps({"app": "memos", "action": "install", "lang": "pt"}).encode(), api)
                    assert st == 400 and "Archived upstream." in json.loads(corpo)["error"], "the reason is the same on the Portuguese page"
                    st, _, corpo = pedir("/api/plan?app=memos&action=install", headers=ok)
                    assert st == 400 and "memos" in json.loads(corpo)["error"], "the plan of an install is refused too"
                    assert pedir("/api/plan?app=memos&action=update", headers=ok)[0] == 200, "only the install is refused"
                    assert install_refusal("homebox") is None, "one that is already installed is never refused"
                    assert install_refusal("gitea") is None, "and an unmarked one is not"
                finally:
                    I.APPS = original

            # resources: a sandbox without a stand-in podman reports nothing; with one, the page can list and prune
            assert json.loads(pedir("/api/resources", headers=ok)[2])["images"] == [], "a sandbox touches no real podman"
            assert pedir("/api/prune", json.dumps({"kind": "images"}).encode(), api)[0] == 400
            with tempfile.TemporaryDirectory() as fk:
                falso = Path(fk, "podman")
                falso.write_text("""#!/bin/sh
case "$*" in
  "images --format json") echo '[{"Id":"i9","Names":["docker.io/o/old:1"],"Size":500,"Containers":0}]';;
  "ps -a --format json") echo '[]';;
  "network ls --format json") echo '[{"name":"podman"}]';;
  "volume ls --filter dangling=true --format json") echo '[{"Name":"vf"}]';;
  "ps -a -q --filter ancestor=i9") ;;
  "rmi --force i9"|"volume rm vf") echo gone;;
  *) echo "unexpected: $*" >&2; exit 1;;
esac
""")
                falso.chmod(0o755)
                os.environ["QH_PODMAN"], resources.PODMAN = str(falso), str(falso)
                try:
                    r = json.loads(pedir("/api/resources", headers=ok)[2])
                    assert [i["id"] for i in r["images"]] == ["i9"] and r["reclaimable"] == 500 and r["volumes"][0]["name"] == "vf", r
                    assert pedir("/api/prune", json.dumps({"kind": "bogus"}).encode(), api)[0] == 400
                    assert pedir("/api/prune", json.dumps({"kind": "volumes"}).encode(), api)[0] == 400, "volumes need the word typed"
                    st, _, corpo = pedir("/api/prune", json.dumps({"kind": "images"}).encode(), api)
                    assert st == 202 and esperar(corpo)["rc"] == 0
                    st, _, corpo = pedir("/api/prune", json.dumps({"kind": "volumes", "confirm": "volumes"}).encode(), api)
                    assert st == 202 and esperar(corpo)["rc"] == 0
                    assert json.loads(pedir("/api/history?app=_host", headers=ok)[2])["entries"][0]["action"] == "prune"
                finally:
                    os.environ.pop("QH_PODMAN", None)
                    resources.PODMAN = "podman"

            # what Podman says: health with the last runs, what really runs (values masked), the images, and the force verbs
            with tempfile.TemporaryDirectory() as fk2:
                nome_h = I.container_name(next(I.APPS.glob("*/homebox.container")))
                alvo_secret = next(iter(ctrinfo.secret_env_keys(installed_unit("homebox").read_text())), "ADMIN_TOKEN")
                inspecao = {"Id": "f" * 64, "Name": nome_h, "ImageName": "docker.io/x/homebox:1", "Image": "a" * 64, "Created": "2026-11-18T00:00:00Z",
                            "Path": "/app", "Args": ["serve"], "RestartCount": 1,
                            "State": {"Status": "running", "Running": True, "StartedAt": "2026-11-18T00:00:01Z",
                                      "Health": {"Status": "unhealthy", "FailingStreak": 3, "Log": [
                                          {"Start": "t1", "End": "t1", "ExitCode": 0, "Output": ""}, {"Start": "t2", "End": "t2", "ExitCode": 1, "Output": "boom"}]}},
                            "Config": {"Env": [f"{alvo_secret}=hunter2", "TZ=UTC"], "Healthcheck": {"Test": ["CMD-SHELL", "true"], "Interval": 30 * 10 ** 9, "Retries": 3},
                                       "HealthcheckOnFailureAction": "none"},
                            "HostConfig": {"ReadonlyRootfs": True, "PidsLimit": 256}, "Mounts": [], "NetworkSettings": {"Networks": {}, "Ports": {}}}
                imagens_j = [{"Id": "1" * 12 + "aa", "Names": ["docker.io/x/old:1"], "Size": 900, "Containers": 0, "CreatedAt": "2026-01-01T00:00:00Z",
                              "Labels": {"org.opencontainers.image.version": "1.0"}},
                             {"Id": "2" * 12 + "bb", "Names": ["docker.io/x/homebox:1"], "Size": 500, "Containers": 1, "CreatedAt": "2026-02-01T00:00:00Z"}]
                ctrs_j = [{"Names": [nome_h], "ImageID": "2" * 12 + "bb", "State": "running"}]
                falso2 = Path(fk2, "podman")
                falso2.write_text(f"""#!/bin/sh
case "$*" in
  "inspect {nome_h}") echo '{json.dumps([inspecao])}';;
  "healthcheck run {nome_h}") echo healthy; exit 0;;
  "images --format json") echo '{json.dumps(imagens_j)}';;
  "ps -a --format json") echo '{json.dumps(ctrs_j)}';;
  "image history --format json {'1' * 12 + 'aa'}") echo '[{{"created":"t","CreatedBy":"/bin/sh -c #(nop) CMD x","size":3}}]';;
  "rmi --force {'1' * 12 + 'aa'}") echo removed;;
  *) echo "unexpected: $*" >&2; exit 1;;
esac
""")
                falso2.chmod(0o755)
                os.environ["QH_PODMAN"], resources.PODMAN, ctrinfo.PODMAN = str(falso2), str(falso2), str(falso2)
                try:
                    h = json.loads(pedir("/api/health?unit=homebox", headers=ok)[2])
                    assert h["status"] == "unhealthy" and h["streak"] == 3 and [x["exit"] for x in h["runs"]] == [1, 0] and h["runs"][0]["output"] == "boom", h
                    assert h["config"]["test"] == "true" and h["config"]["interval"] == 30.0 and h["config"]["on_failure"] is None
                    assert pedir("/api/health?unit=nope", headers=ok)[0] == 400
                    st, _, c = pedir("/api/health/run", json.dumps({"unit": "homebox"}).encode(), api)
                    assert st == 200 and json.loads(c)["rc"] == 0 and json.loads(c)["output"] == "healthy" and json.loads(c)["health"]["status"] == "unhealthy", c
                    assert pedir("/api/health/run", json.dumps({"unit": "homebox"}).encode(), ok)[0] == 403
                    rt = json.loads(pedir("/api/runtime?unit=homebox", headers=ok)[2])
                    assert all(e["value"] != "hunter2" for e in rt["env"]) and rt["revealed"] is False and rt["command"] == "/app serve", rt["env"]
                    assert any(e["key"] == alvo_secret and e["secret"] for e in rt["env"]) or alvo_secret == "ADMIN_TOKEN", "a Secret= variable is flagged"
                    rt2 = json.loads(pedir("/api/runtime?unit=homebox&reveal=1", headers=ok)[2])
                    assert {e["key"]: e["value"] for e in rt2["env"]}[alvo_secret] == "hunter2" and rt2["revealed"] is True
                    im = json.loads(pedir("/api/images", headers=ok)[2])["images"]
                    por = {i["id"]: i for i in im}
                    assert [i["id"] for i in im] == ["1" * 12 + "aa", "2" * 12 + "bb"] and por["1" * 12 + "aa"]["removable"] and por["1" * 12 + "aa"]["labels"] == {"version": "1.0"}
                    assert not por["2" * 12 + "bb"]["removable"] and por["2" * 12 + "bb"]["used_by"][0]["unit"] == "homebox" and por["2" * 12 + "bb"]["used_by"][0]["app"] == "homebox"
                    assert json.loads(pedir(f"/api/images/history?id={'1' * 12 + 'aa'}", headers=ok)[2])["layers"][0]["by"] == "CMD x"
                    assert pedir("/api/images/history?id=zz", headers=ok)[0] == 400
                    for ruim in ("zz", "2" * 12 + "bb", "3" * 12 + "cc"):
                        assert pedir("/api/images/rm", json.dumps({"id": ruim}).encode(), api)[0] in (400, 404), ruim
                    st, _, c = pedir("/api/images/rm", json.dumps({"id": "1" * 12 + "aa"}).encode(), api)
                    assert st == 202 and esperar(c)["rc"] == 0, c
                finally:
                    os.environ.pop("QH_PODMAN", None)
                    resources.PODMAN, ctrinfo.PODMAN = "podman", "podman"
            assert json.loads(pedir("/api/images", headers=ok)[2])["images"] == [] and pedir("/api/health/run", json.dumps({"unit": "homebox"}).encode(), api)[0] == 409, "a sandbox touches no real podman"
            for verbo_f in ("force-stop", "force-restart"):
                st, _, c = pedir("/api/unit", json.dumps({"unit": "homebox", "verb": verbo_f}).encode(), api)
                assert st == 202, (verbo_f, c)
                assert esperar(c)["rc"] == 0 and any(e["action"] == verbo_f for e in json.loads(pedir("/api/history?app=homebox", headers=ok)[2])["entries"]), verbo_f

            # console: a WebSocket to `podman exec -it`; refused unless it is this server's own page asking
            global PODMAN
            import socket as _s
            alvo = urlparse(base)
            origem_certa = f"{alvo.scheme}://{alvo.netloc}"

            def ws_abrir(unit, origin, extra=None):
                c = _s.create_connection((alvo.hostname, alvo.port), timeout=10)
                cab = [f"GET /api/shell?unit={unit} HTTP/1.1", f"Host: {alvo.netloc}", "Upgrade: websocket", "Connection: Upgrade",
                       "Sec-WebSocket-Key: dGhlIHNhbXBsZSBub25jZQ==", "Sec-WebSocket-Version: 13",
                       f"Cookie: {ok['Cookie']}"] + ([f"Origin: {origin}"] if origin else []) + (extra or [])
                c.sendall(("\r\n".join(cab) + "\r\n\r\n").encode())
                resp = b""
                while b"\r\n\r\n" not in resp:
                    resp += c.recv(4096)
                return c, resp
            assert pedir("/api/shell?unit=homebox")[0] == 401, "the console needs the login"
            for origin in (None, "http://evil.example", origem_certa + ".evil.example"):
                c, resp = ws_abrir("homebox", origin)
                assert resp.startswith(b"HTTP/1.0 403") or resp.startswith(b"HTTP/1.1 403"), (origin, resp[:40])
                c.close()
            st, _, _ = pedir("/api/shell?unit=homebox", headers={**ok, "Origin": origem_certa})
            assert st == 400, "a plain GET is not a WebSocket"
            assert ws_abrir("nope", origem_certa)[1][9:12] == b"400"
            c, resp = ws_abrir("homebox", origem_certa)
            assert resp[9:12] == b"400", "a sandbox has no containers"
            c.close()
            with tempfile.TemporaryDirectory() as fk:
                falso = Path(fk, "podman")
                falso.write_text("#!/bin/sh\nexec cat\n")
                falso.chmod(0o755)
                os.environ["QH_PODMAN"] = str(falso)
                antes_podman, PODMAN = PODMAN, str(falso)
                try:
                    c, resp = ws_abrir("homebox", origem_certa)
                    assert resp[9:12] == b"101" and b"s3pPLMBiTxaQ9kYGzzhZRbK+xOo=" in resp, resp[:200]
                    c.sendall(wsterm._mascarado(wsterm.OP_TEXT, json.dumps({"t": "in", "d": "console-ok\r"}).encode()))
                    c.settimeout(5)
                    recebido = resp.split(b"\r\n\r\n", 1)[1]
                    fim = time.time() + 5
                    while b"console-ok" not in recebido and time.time() < fim:
                        recebido += c.recv(4096)
                    assert b"console-ok" in recebido, recebido
                    c.sendall(wsterm._mascarado(wsterm.OP_CLOSE, b"\x03\xe8"))
                    time.sleep(0.5)
                    c.close()
                    hist = json.loads(pedir("/api/history?app=homebox&limit=5", headers=ok)[2])["entries"]
                    assert any(e["action"] == "shell" for e in hist), "a console leaves a line in the history"
                finally:
                    os.environ.pop("QH_PODMAN", None)
                    PODMAN = antes_podman
            assert SHELLS._value == 4, "every console gives its slot back"

            # live logs: Server-Sent Events from `journalctl -f`; a sandbox has no journal, a stand-in has lines
            assert pedir("/api/logs/stream?unit=homebox")[0] == 401, "the stream needs the login too"
            assert pedir("/api/logs/stream?unit=nope", headers=ok)[0] == 400
            assert sse_frame("a\r\nb") == b"data: a b\n\n"
            assert json.loads(pedir("/api/logs/stream?unit=homebox", headers=ok)[2]) == {"output": ""}, "a sandbox answers plainly"
            with tempfile.TemporaryDirectory() as fk:
                falso = Path(fk, "journalctl")
                falso.write_text("#!/bin/sh\necho 'nov 15 first line'\necho 'nov 15 second: erro'\nsleep 0.3\n")
                falso.chmod(0o755)
                os.environ["QH_JOURNALCTL"] = str(falso)
                global JOURNALCTL
                antes, JOURNALCTL = JOURNALCTL, str(falso)
                try:
                    st, h, corpo = pedir("/api/logs/stream?unit=homebox", headers=ok)
                    assert st == 200 and h["Content-Type"] == "text/event-stream" and h["Cache-Control"] == "no-cache", (st, h)
                    assert corpo == b"data: nov 15 first line\n\ndata: nov 15 second: erro\n\n", corpo
                finally:
                    os.environ.pop("QH_JOURNALCTL", None)
                    JOURNALCTL = antes
            assert STREAMS._value == 8, "every stream gives its slot back"

            # host summary: parsed from /proc and /sys, each field None when the host does not say
            with tempfile.TemporaryDirectory() as fk:
                Path(fk, "proc").mkdir()
                Path(fk, "proc/loadavg").write_text("2.00 1.00 0.5 1/100 99\n")
                Path(fk, "proc/meminfo").write_text("MemTotal: 1000 kB\nMemAvailable: 250 kB\n")
                Path(fk, "proc/uptime").write_text("7200.5 100.0\n")
                Path(fk, "sys/class/thermal/thermal_zone0").mkdir(parents=True)
                Path(fk, "sys/class/thermal/thermal_zone0/temp").write_text("48500\n")
                Path(fk, "proc/stat").write_text("cpu  100 0 100 700 100 0 0 0 0 0\n")
                Path(fk, "proc/net").mkdir()
                Path(fk, "proc/net/dev").write_text("Inter-|   Receive\n face |bytes\n  lo: 5 0 0 0 0 0 0 0 5 0 0 0 0 0 0 0\n"
                                                    " eth0: 1000 1 0 0 0 0 0 0 400 1 0 0 0 0 0 0\n veth1: 9999 1 0 0 0 0 0 0 9999 1 0 0 0 0 0 0\n")
                estado, relogio = {}, [100.0]
                r = host_summary(f"{fk}/proc", f"{fk}/sys", fk, estado, lambda: relogio[0])
                assert (r["load"], r["uptime"], r["temp"], r["mem"]["used"]) == (2.0, 7200, 48.5, 750 * 1024), r
                assert r["cpu"]["pct"] is None and r["net"]["rx_rate"] is None and r["net"]["rx"] == 1000 and r["net"]["tx"] == 400, "first reading: totals, no rates; bridges and lo are left out"
                assert r["disk"]["total"] > 0 and r["disk"]["used"] >= 0
                assert host_summary(f"{fk}/proc", f"{fk}/sys", fk, estado, lambda: relogio[0] + 0.5) is r, "a second reading under a second later reuses the answer"
                Path(fk, "proc/stat").write_text("cpu  200 0 200 800 200 0 0 0 0 0\n")        # +200 busy, +200 idle: 50%
                Path(fk, "proc/net/dev").write_text("Inter-|   Receive\n face |bytes\n eth0: 3000 1 0 0 0 0 0 0 900 1 0 0 0 0 0 0\n")
                relogio[0] = 102.0
                r = host_summary(f"{fk}/proc", f"{fk}/sys", fk, estado, lambda: relogio[0])
                assert r["cpu"]["pct"] == 50.0, r["cpu"]
                assert (r["net"]["rx_rate"], r["net"]["tx_rate"]) == (1000, 250), r["net"]
                assert host_summary(f"{fk}/none", f"{fk}/none", fk, {})["mem"] is None, "a host that says nothing gives None, not a crash"
            assert "uptime" in json.loads(pedir("/api/host", headers=ok)[2]), "/api/host answers"

            # trial: a duration that does not parse, or a trial on anything but an install, never starts a job
            for corpo in ({"app": "memos", "action": "install", "trial": "soon"},
                          {"app": "memos", "action": "install", "trial": "5m"},
                          {"app": "memos", "action": "update", "trial": "2h"}):
                assert pedir("/api/run", json.dumps(corpo).encode(), api)[0] == 400, corpo

            # history: every job is on disk, newest first, with who asked and how it ended
            lista = [e for e in json.loads(pedir("/api/history?app=homebox", headers=ok)[2])["entries"]
                     if e["action"] not in ("shell", "custom-unit", "force-stop", "force-restart")]     # a console and a rewritten .container are recorded too
            acoes = [e["action"] for e in lista]
            assert acoes[:2] == ["revert", "customize"], "the customization and its revert are in the history"
            assert "env" in acoes and "install" in acoes and "backup" in acoes, acoes
            assert all("output" not in e and e["from"] == "127.0.0.1" for e in lista)
            assert all(e["app"] == "homebox" for e in lista) and lista[0]["start"] <= lista[0]["end"]
            todos = json.loads(pedir("/api/history?limit=3", headers=ok)[2])["entries"]
            assert len(todos) == 3, "limit narrows it"
            det = json.loads(pedir(f"/api/history/{lista[-1]['id']}", headers=ok)[2])
            assert det["action"] == "install" and det["rc"] == 0 and "homebox" in det["output"]
            st, _, corpo = pedir("/api/unit", json.dumps({"unit": "homebox", "verb": "restart"}).encode(), api)
            assert st == 202, (st, corpo)
            assert esperar(corpo)["rc"] == 0
            ultima = json.loads(pedir("/api/history?app=homebox&limit=1", headers=ok)[2])["entries"][0]
            assert (ultima["action"], ultima["unit"]) == ("restart", "homebox"), ultima
            st, _, _ = pedir("/api/history/nao-existe", headers=ok)
            assert st == 404, st
            assert oct(history_file().stat().st_mode)[-3:] == "600", "the history is private"
            st, _, _ = pedir("/api/history", metodo="GET")
            assert st == 401, "and behind the login"

            # release notes: a unit that is not installed answers without the network
            st, _, corpo = pedir("/api/notes?unit=memos", headers=ok)
            assert st == 200 and json.loads(corpo)["releases"] == [], corpo
        finally:
            srv.shutdown()
    # links: the repository only from a source that can be trusted, never a guess
    assert repo_url("docker.io/vaultwarden/server:1.37.5-alpine", "dani-garcia/vaultwarden") == \
        "https://github.com/dani-garcia/vaultwarden"
    assert repo_url("docker.io/vaultwarden/server:1", None) is None, "a Docker Hub name is not a repository"
    assert repo_url("ghcr.io/hargata/lubelogger:v1.7.4", None) == "https://github.com/hargata/lubelogger"
    assert repo_url("lscr.io/linuxserver/jellyfin:10", None) == "https://github.com/linuxserver/docker-jellyfin"
    assert repo_url("registry.gitlab.com/fmd-foss/fmd-server:0.17", None) == "https://gitlab.com/fmd-foss/fmd-server"
    assert repo_url("docker.io/x/y:1", "-") is None, "no override and no mirror: no link"
    assert repo_url("registry.gitlab.com/fmd-foss/fmd-server:0.17", "registry:^[0-9]+$") == \
        "https://gitlab.com/fmd-foss/fmd-server", "`registry` says how to compare, not where it lives"
    assert repo_url("ghcr.io/a/b:1", "-") == "https://github.com/a/b"
    assert repo_url("ghcr.io/a/b:1", "compose:karakeep-app/karakeep:docker/docker-compose.yml") == \
        "https://github.com/karakeep-app/karakeep"
    assert repo_url("docker.io/x/y:1", "compose:https://example.org/c.yml") is None
    assert repo_url("docker.io/x/y:1", "not a repo") is None, "an override must look like owner/repo"
    assert image_page("docker.io/vaultwarden/server:1.37.5@sha256:" + "a" * 64) == \
        "https://hub.docker.com/r/vaultwarden/server"
    assert image_page("docker.io/library/nginx:1.29") == "https://hub.docker.com/_/nginx"
    assert image_page("ghcr.io/hargata/lubelogger:v1") == "https://github.com/hargata/lubelogger/pkgs/container/lubelogger"
    assert image_page("registry.fedoraproject.org/fedora-toolbox:44") is None
    assert remote_https("git@github.com:me/quadlet-homelab.git\n") == "https://github.com/me/quadlet-homelab"
    assert remote_https("https://github.com/me/quadlet-homelab") == "https://github.com/me/quadlet-homelab"
    assert remote_https("git@example.org:me/x.git") is None

    # links: the documentation is the one the README names, the issues come from the repository
    assert repo_from_field("owner/repo") == "https://github.com/owner/repo"
    assert repo_from_field("https://codeberg.org/o/r/") == "https://codeberg.org/o/r"
    assert repo_from_field("javascript:alert(1)") is None and repo_from_field("a b/c") is None and repo_from_field("") is None
    assert issues_url("https://github.com/o/r") == "https://github.com/o/r/issues"
    assert issues_url("https://gitlab.com/o/r") == "https://gitlab.com/o/r/-/issues"
    assert issues_url("https://codeberg.org/o/r") == "https://codeberg.org/o/r/issues"
    assert issues_url("https://example.org/o/r") is None, "a host whose issue tracker's address is not known gets no guess"
    assert same_page("https://github.com/o/r#readme", "https://github.com/o/r/") and not same_page("https://o.org/", "https://github.com/o/r")
    with tempfile.TemporaryDirectory() as dd:
        antes, I.APPS = I.APPS, Path(dd)
        try:
            (I.APPS / "demo").mkdir()
            manifest.path_of(I.APPS / "demo").write_text(manifest.dump({"docs": "https://docs.example.org/demo"}))
            assert docs_url("demo") == "https://docs.example.org/demo", "read from [store] docs"
            manifest.path_of(I.APPS / "demo").write_text(manifest.dump({"category": "Tools"}))
            assert docs_url("demo") is None and docs_url("nao-existe") is None
        finally:
            I.APPS = antes

    # what the history keeps of an output: no credential, only the tail, a bounded file
    assert redact("  user:     joe\n  password: s3cret\n  usuário:  ana\n  senha:    x\nok: y") == \
        "  user:     ***\n  password: ***\n  usuário:  ***\n  senha:    ***\nok: y"
    assert redact("a password: in prose") == "a password: in prose", "only a line that starts with the label"
    with tempfile.TemporaryDirectory() as tmp2:
        PREFIX = tmp2
        for i in range(130):
            falso = Job(f"app{i}", "install", "127.0.0.1")
            falso.out, falso.rc = [f"{i}:" + "x" * 30000], 0
            history_add(falso)
        assert history_file().stat().st_size <= HISTORY_CAP, "the file is compacted past its cap"
        linhas = history_file().read_text().splitlines()
        assert all(json.loads(x) for x in linhas) and json.loads(linhas[-1])["app"] == "app129"
        assert len(linhas) < 130 and json.loads(linhas[-1])["output"].startswith("…\n"), "newest kept, tail cut"
        assert oct(history_file().stat().st_mode)[-3:] == "600"
        PREFIX = tmp

    # CPU and memory are read from /proc and cgroupfs: the parsing is pure, the reading is real
    assert parse_cgroup("0::/user.slice/a.scope\n") == "/user.slice/a.scope"
    assert parse_cgroup("12:memory:/x\n11:cpu:/x\n") is None, "cgroup v1 has no unified path"
    assert vm_rss(os.getpid()) > 0 and vm_rss(2 ** 22 + 1) == 0

    # which platforms an image runs on, against the host's
    amd, dois = {"linux/amd64", "linux/unknown"}, {"linux/amd64", "linux/arm64"}
    r = arch_report([("a", "i/a"), ("b", "i/b"), ("c", "i/c")], "arm64",
                    {"i/a": amd, "i/b": dois, "i/c": None}.get)
    assert [x["ok"] for x in r] == [False, True, None], "an unknown answer is not a warning"
    assert r[0]["platforms"] == ["amd64", "unknown"] and r[2]["platforms"] is None
    assert ARCH_NOMES["x86_64"] == "amd64" and ARCH_NOMES["aarch64"] == "arm64"
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
    if not PREFIX:
        threading.Thread(target=alerts_loop, daemon=True).start()
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
