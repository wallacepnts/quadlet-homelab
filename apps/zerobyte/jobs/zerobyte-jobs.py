#!/usr/bin/env python3
"""Creates one Zerobyte backup job per installed service, wired to the hook.

Zerobyte backs up directories, and this repository puts one directory per
service under ~/.config/containers/volumes. So the unit of work is the folder,
not the unit: media-stack's twelve units share one directory and get one job.

What each job needs beyond the path is the mode its data requires, and that is
the part worth automating — it is the same decision the hook documents:

    sqlite   the folder holds SQLite; the hook copies each database with the
             online backup API before Restic runs, and the copy lands in
             <folder>/.dbbackup, which the same job then picks up
    stop     no online dump exists (any-sync-bundle's embedded Mongo), so the
             unit is stopped around the copy
    none     plain files; Restic copies them as they are

Detection covers sqlite and none. `stop` cannot be detected — a folder with a
Mongo in it looks like plain files — so it is declared in the app's
install.ini under [backup].

Stdlib only: it runs on the host, next to the hook.
"""
import argparse
import json
import os
import pathlib
import re
import sys
import urllib.error
import urllib.request

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent.parent.parent))

def raizes_do_repositorio():
    """The volume folder names this repository's apps actually use.

    Not the app names: actual-budget writes to volumes/actual, and twelve
    media-stack units share volumes/media-stack. `Service.volume_roots()`
    already answers this, so it is imported rather than guessed.
    """
    from install import APPS, Service
    return {pathlib.Path(r).name
            for d in APPS.iterdir() if d.is_dir()
            for r in Service(d.name).volume_roots()}


VOLUMES = pathlib.Path.home() / ".config/containers/volumes"
SECRETS = pathlib.Path.home() / ".config/containers/secrets"
UNITS = pathlib.Path.home() / ".config/containers/systemd"
APPS = pathlib.Path(__file__).resolve().parent.parent.parent  # apps/
CHAVE = pathlib.Path.home() / ".config/zerobyte/api-key"
TOKEN = pathlib.Path.home() / ".config/zerobyte-backup-hook/token"
BANCOS = (".db", ".sqlite", ".sqlite3")
COPIA = ".dbbackup"
# A database engine that has no online dump here leaves a fingerprint in its
# data directory. Finding one means `stop`, because copying it hot produces an
# archive that only fails on restore — and detecting it beats defaulting to
# `none`, which is what would silently happen otherwise.
MARCAS = {
    "PG_VERSION": "postgres",
    "ibdata1": "mysql/mariadb",
    "WiredTiger": "mongo",
}


def api(base, key, caminho, metodo="GET", corpo=None):
    req = urllib.request.Request(
        f"{base}/api/v1/{caminho}", method=metodo,
        data=json.dumps(corpo).encode() if corpo is not None else None,
        headers={"x-api-key": key, "Content-Type": "application/json"})
    try:
        with urllib.request.urlopen(req, timeout=60) as r:
            return json.loads(r.read() or "null")
    except urllib.error.HTTPError as e:
        detalhe = e.read().decode(errors="replace")[:400]
        raise SystemExit(f"{metodo} {caminho}: HTTP {e.code} — {detalhe}")


def modo(pasta):
    """The mode this folder's data needs: declared, or worked out by looking."""
    ini = APPS / pasta.name / "install.ini"
    if ini.is_file():
        m = re.search(r"(?ms)^\[backup\].*?^mode\s*=\s*(\w+)", ini.read_text())
        if m:
            return m.group(1).strip()
    sqlite = False
    opaco = []
    for raiz, dirs, arquivos in os.walk(pasta, onerror=opaco.append):
        if COPIA in dirs:
            dirs.remove(COPIA)
        for nome in arquivos:
            if nome in MARCAS:
                return "stop"
            if nome.endswith(BANCOS):
                sqlite = True
    if opaco:
        # A directory this user cannot read is a container's data owned by a
        # mapped uid — a Postgres or a Mongo, most of the time. We cannot look
        # inside to be sure, and guessing `none` would back it up hot, so the
        # answer is the safe one.
        return "stop"
    return "sqlite" if sqlite else "none"


def ganchos(nome, porta, token):
    base = f"http://host.containers.internal:{porta}/hooks/{nome}"
    cab = [f"X-Zerobyte-Hook-Secret: {token}"]
    return {"pre": {"url": f"{base}/pre-backup", "headers": cab},
            "post": {"url": f"{base}/post-backup", "headers": cab}}


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--url", default=os.environ.get("ZEROBYTE_URL"),
                    help="base URL of Zerobyte (or ZEROBYTE_URL)")
    ap.add_argument("--repository", help="repository shortId (default: the only one)")
    ap.add_argument("--cron", default="0 3 * * *", help="schedule (default: 03:00 daily)")
    ap.add_argument("--hook-port", default="8766")
    ap.add_argument("--apply", action="store_true", help="execute (without it, only show)")
    a = ap.parse_args()

    if not a.url:
        raise SystemExit("--url or ZEROBYTE_URL is required")
    if not CHAVE.is_file():
        raise SystemExit(f"no API key at {CHAVE} — create one in Settings -> API keys")
    key = CHAVE.read_text().strip()
    token = TOKEN.read_text().strip() if TOKEN.is_file() else None

    repos = api(a.url, key, "repositories")
    if a.repository:
        repo = a.repository
    elif len(repos) == 1:
        repo = repos[0]["shortId"]
    else:
        raise SystemExit(f"{len(repos)} repositories — pick one with --repository")

    # shortId by name, so a second run changes nothing
    volumes = {v["name"]: v["shortId"] for v in api(a.url, key, "volumes")}
    jobs = {b["name"] for b in api(a.url, key, "backups")}

    pastas = sorted(p for p in VOLUMES.iterdir() if p.is_dir()) if VOLUMES.is_dir() else []
    conhecidas = raizes_do_repositorio()
    allowlist, alheias = [], []
    for pasta in pastas:
        # Only this repository's services. A folder from somewhere else has no
        # install.ini to declare its mode and no unit this script can reason
        # about — the mode would be a guess, and a wrong guess here is a backup
        # that does not restore.
        if pasta.name not in conhecidas:
            alheias.append(pasta.name)
            continue
        nome, m = pasta.name, modo(pasta)
        if m != "none":
            allowlist.append(f"{nome}:{m}")
        if nome in jobs:
            print(f"  {nome:24} job já existe")
            continue
        if m != "none" and not token:
            print(f"  {nome:24} precisa do gancho ({m}), mas não há token — pulando")
            continue
        if m == "stop" and not any(UNITS.rglob(f"{nome}.container")):
            # `stop` is `systemctl stop <name>`, so the folder name has to BE a
            # unit. media-stack is the case that is not: twelve units share the
            # directory, and one of them (dispatcharr) carries a Postgres. No
            # single hook call is right there, so this asks instead of guessing.
            print(f"  {nome:24} precisa de stop, mas não há unit `{nome}` — "
                  f"declare o job à mão")
            continue
        alvo = f"/sources/volumes/{nome}"
        print(f"  {nome:24} volume {alvo}  |  modo {m}")
        if not a.apply:
            continue
        if nome not in volumes:
            api(a.url, key, "volumes", "POST",
                {"name": nome, "config": {"backend": "directory", "path": alvo}})
            # Read the shortId back from the list instead of the creation
            # response: the two endpoints do not wrap it the same way, and the
            # list is the shape this script already relies on.
            volumes = {v["name"]: v["shortId"] for v in api(a.url, key, "volumes")}
        vid = volumes[nome]
        corpo = {"name": nome, "volumeId": vid, "repositoryId": repo,
                 "enabled": True, "cronExpression": a.cron}
        if m != "none":
            corpo["backupWebhooks"] = ganchos(nome, a.hook_port, token)
        api(a.url, key, "backups", "POST", corpo)

    # The secrets, as one job. Restoring a data volume without them gives a
    # service that starts and does not work: vaultwarden's admin token no
    # longer matches, excalidash's JWT_SECRET logs everyone out. They are 72 KB
    # and they change almost never, so there is no reason to split them per app.
    if SECRETS.is_dir() and "secrets" not in jobs:
        print(f"  {'secrets':24} volume /sources/secrets  |  modo none")
        if a.apply:
            if "secrets" not in volumes:
                api(a.url, key, "volumes", "POST",
                    {"name": "secrets",
                     "config": {"backend": "directory", "path": "/sources/secrets"}})
                volumes = {v["name"]: v["shortId"] for v in api(a.url, key, "volumes")}
            api(a.url, key, "backups", "POST",
                {"name": "secrets", "volumeId": volumes["secrets"], "repositoryId": repo,
                 "enabled": True, "cronExpression": a.cron})
    elif "secrets" in jobs:
        print(f"  {'secrets':24} job já existe")

    if alheias:
        print(f"\nfora deste repositório, não tocadas: {', '.join(alheias)}")
    if allowlist:
        # A job whose hook is not in the allowlist gets a 404 on pre-backup,
        # and Zerobyte treats that as a failed backup. Printing the line beats
        # finding out at 03:00.
        print("\nZEROBYTE_HOOK_UNITS must include these, or the jobs fail:")
        print("  " + ",".join(sorted(allowlist)))
    if not a.apply:
        print("\nnothing was done. repeat with --apply")


if __name__ == "__main__":
    main()
