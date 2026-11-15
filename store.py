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
import platform
import re
import secrets
import shutil
import subprocess
import sys
import threading
import time
from concurrent.futures import ThreadPoolExecutor
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
    "unknown file": "arquivo desconhecido",
    "not a setting of this file, or not a single line":
        "não é uma opção deste arquivo, ou não é uma linha só",
    "set": "definido", "turned off": "desligado",
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
                        "rc": job.rc, "from": job.origem, "output": saida},
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


def links(app):
    """[{kind, url}]: the project, its releases and image page, and this repo's recipe."""
    s = I.Service(app, PREFIX)
    principal = s.main_unit()
    saida = []
    if principal:
        imagem = next((v for k, v in I.directives_of(principal) if k == "Image"), "")
        override = s.ini.get("upstream", principal.stem, fallback=None) if s.ini.has_section("upstream") else None
        repo = repo_url(imagem, override)
        if repo:
            saida.append({"kind": "repo", "url": repo})
            if repo.startswith("https://github.com/"):
                saida.append({"kind": "releases", "url": repo + "/releases"})
        pagina = image_page(imagem)
        if pagina:
            saida.append({"kind": "image", "url": pagina})
    base = recipe_base()
    if base:
        saida.append({"kind": "recipe", "url": f"{base}/tree/main/apps/{app}"})
    return saida


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
            e["sensitive"] = bool(SENSIVEL.search(e["key"]))
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
    conhecidas = {e["key"] for e in I.parse_env(f.read_text())}
    for k, v in mudar.items():
        if k not in conhecidas or not isinstance(v, str) or "\n" in v or "\r" in v:
            raise ValueError(f"{k}: " + loc("not a setting of this file, or not a single line"))
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
              unit=""):
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
            rc = 0
            # One command, or several in order (an upgrade is a bump, then an
            # update): each runs only if the one before it succeeded.
            for i, uno in enumerate(cmd if cmd and isinstance(cmd[0], list) else [cmd] if cmd else []):
                if i:
                    job.write("\n" + "─" * 60 + "\n")
                if PREFIX and uno[0] == "systemctl":
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
        if url.path == "/login":
            # A refused token comes back as ?e=1. The page cannot read its own
            # query (no inline script, by the CSP), so the notice is put in the
            # HTML here — a fixed text, nothing from the request is echoed.
            html = (STATIC / ARQUIVOS["/login"]).read_text()
            aviso = '<p class="erro" role="alert">Token inválido / Invalid token</p>' if q.get("e") == "1" else ""
            return self._send(200, html.replace("<!--error-->", aviso).encode(), TIPOS[".html"])
        if url.path == "/style.css":
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
        if url.path == "/api/links":
            app = q.get("app", "")
            if not service_dir(app):
                return self._json(400, {"error": loc("unknown service")})
            return self._json(200, {"links": links(app)})
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
            job = start_job(app, action, cmd, lang, prepare, entrada, refrescar=cadeia,
                            origem=self.client_address[0])
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
            job = start_job(pasta, verbo, ["systemctl", "--user", verbo, unit], lang,
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

            # resources: a sandbox has no host to measure, and no network to ask
            assert json.loads(pedir("/api/stats", headers=ok)[2]) == {"stats": {}}
            assert json.loads(pedir("/api/disk?app=homebox", headers=ok)[2]) == {"bytes": None, "paths": []}
            a = json.loads(pedir("/api/arch?app=homebox", headers=ok)[2])
            assert a["host"] == host_arch() and a["runs"] is None and a["units"][0]["ok"] is None, a

            # links: this repo's recipe for it, and the project where one is known
            lk = {x["kind"]: x["url"] for x in json.loads(pedir("/api/links?app=vaultwarden", headers=ok)[2])["links"]}
            assert lk["repo"] == "https://github.com/dani-garcia/vaultwarden", lk
            assert lk["releases"].endswith("/releases") and lk["image"].startswith("https://hub.docker.com/")
            st, _, _ = pedir("/api/links?app=../x", headers=ok)
            assert st == 400, st

            # history: every job is on disk, newest first, with who asked and how it ended
            lista = json.loads(pedir("/api/history?app=homebox", headers=ok)[2])["entries"]
            acoes = [e["action"] for e in lista]
            assert acoes[0] == "env" and "install" in acoes and "backup" in acoes, acoes
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
