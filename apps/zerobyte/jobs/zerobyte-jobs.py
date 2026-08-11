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

Run it as `qh --zerobyte`: it reads which volume folders are this repository's
from install.py, so it only works from inside the repository.
"""
import argparse
import configparser
import json
import os
import pathlib
import re
import sys
import urllib.error
import urllib.request

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent.parent.parent))
import qhui
from qhui import translator

# Same shape as install.py's table: English in the source, Portuguese when the
# system asks for it. Longest first is translator()'s job.
PT = {
    "base URL of Zerobyte (default: BASE_URL from its .env)":
        "URL do Zerobyte (padrão: o BASE_URL do .env dele)",
    "where the backup runs (default: the only one)":
        "onde o backup roda (padrão: o único cadastrado)",
    "turn mirroring off: clears the mirrors on every job":
        "desliga o espelho: tira o espelho de todos os jobs",
    "schedule (default: 03:00 daily)": "agendamento (padrão: 03:00 todo dia)",
    "execute (without it, only show)": "executa (sem ele, só mostra)",
    "pass --url": "passe o --url",
    "no BASE_URL in": "sem BASE_URL em",
    "create one in Settings -> API keys": "crie uma em Settings -> API keys",
    "no API key at": "sem chave de API em",
    "say which one runs the backup with --repository "
    "(the others become mirrors)":
        "diga qual roda o backup com --repository (os outros viram espelho)",
    "repositories —": "repositórios —",
    "job already exists": "job já existe",
    "needs the hook": "precisa do gancho",
    "but there is no token — skipping": "mas não há token — pulando",
    "needs stop, but there is no unit": "precisa de stop, mas não há unit",
    "declare this job by hand": "declare o job à mão",
    "volume": "volume",
    "mode": "modo",
    "mirroring": "espelhando",
    "clearing the mirrors on every job": "tirando o espelho de todos os jobs",
    "first copy failed": "a primeira cópia falhou",
    "settings updated": "ajustes atualizados",
    "alerts wired": "avisos ligados",
    "alerting on failure": "avisando em falha, destinos",
    "no notification destination: create one in Settings -> Notifications":
        "nenhum destino de notificação: crie um em Settings -> Notifications",
    "repository(ies) on every job": "repositório(s) em cada job",
    "outside this repository, left alone": "fora deste repositório, não tocadas",
    "ZEROBYTE_HOOK_UNITS must include these, or the jobs fail:":
        "o ZEROBYTE_HOOK_UNITS precisa incluir estas, ou os jobs falham:",
    "nothing was done. repeat with --apply":
        "nada foi feito. repita com --apply",
}
loc = translator(PT)

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
ENV = pathlib.Path.home() / ".config/containers/env/zerobyte.env"
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
# Excluded from every job. Short on purpose: measured across the real volumes,
# the disposable directories add up to single-digit megabytes, so a long list
# of guessed patterns would only add ways to drop something that mattered. What
# an app knows about its own data goes in its install.ini, under [backup].
EXCLUIR = ["*.tmp", "*.partial", "lost+found", ".Trash-*"]
# restic's own convention: a directory carrying this file is a cache.
EXCLUIR_SE = ["CACHEDIR.TAG"]
# Kept on every job: a week of days, a month of weeks, half a year of months.
# No keepHourly — the schedule is daily, so it would never match anything. The
# keepLast is for the runs you trigger by hand on the same day as a scheduled
# one, which the daily rule alone would collapse into a single kept snapshot.
RETENCAO = {"keepLast": 3, "keepDaily": 7, "keepWeekly": 4, "keepMonthly": 6}
# PATCH takes the whole object, so an existing job is read back and sent again.
CAMPOS = ("name", "volumeId", "repositoryId", "enabled", "cronExpression",
          "excludePatterns", "excludeIfPresent", "backupWebhooks",
          "customResticParams", "maxRetries", "retryDelay", "oneFileSystem")


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


def excluir(nome):
    """This job's exclude patterns: the shared ones, plus the app's own."""
    ini = APPS / nome / "install.ini"
    if not ini.is_file():
        return list(EXCLUIR)
    # interpolation=None for the same reason install.py does it: the values
    # carry %h, a systemd specifier that configparser would try to expand.
    cp = configparser.ConfigParser(interpolation=None)
    cp.read(ini)
    bruto = cp.get("backup", "exclude", fallback="")
    return EXCLUIR + [l.strip() for l in bruto.splitlines() if l.strip()]


def ajusta_job(a, key, job, padroes):
    """Bring an existing job's excludes and retention up to date.

    A body with only the changed fields is refused (`expected string, path:
    repositoryId`), so the job is sent back whole with those replaced. The
    retention is compared key by key: the API answers with keys we never set.
    """
    guardado = job.get("retentionPolicy") or {}
    if (job.get("excludePatterns") == padroes
            and job.get("excludeIfPresent") == EXCLUIR_SE
            and all(guardado.get(k) == v for k, v in RETENCAO.items())):
        return ""
    if a.apply:
        corpo = {k: job[k] for k in CAMPOS if job.get(k) is not None}
        corpo["excludePatterns"] = padroes
        corpo["excludeIfPresent"] = list(EXCLUIR_SE)
        corpo["retentionPolicy"] = dict(RETENCAO)
        api(a.url, key, f"backups/{job['shortId']}", "PATCH", corpo)
    return "  |  " + loc("settings updated")


def ajusta_avisos(a, key, job, destinos):
    """Point every notification destination at this job.

    On failure and on warning only. Twelve "it worked" messages a night is
    noise you learn to skip past, and the one that failed goes with it — which
    is how a Mongo went a month reporting `warning` without anyone reading it.
    """
    atual = {(x["destinationId"], bool(x.get("notifyOnFailure")), bool(x.get("notifyOnWarning")))
             for x in (api(a.url, key, f"backups/{job['shortId']}/notifications") or [])}
    if atual == {(d, True, True) for d in destinos}:
        return ""
    if a.apply:
        api(a.url, key, f"backups/{job['shortId']}/notifications", "PUT",
            {"assignments": [{"destinationId": d, "notifyOnStart": False,
                              "notifyOnSuccess": False, "notifyOnWarning": True,
                              "notifyOnFailure": True} for d in destinos]})
    return "  |  " + loc("alerts wired")


def ganchos(nome, porta, token):
    base = f"http://host.containers.internal:{porta}/hooks/{nome}"
    cab = [f"X-Zerobyte-Hook-Secret: {token}"]
    return {"pre": {"url": f"{base}/pre-backup", "headers": cab},
            "post": {"url": f"{base}/post-backup", "headers": cab}}


def url_do_env():
    """The URL Zerobyte answers on, from its own env file.

    Not 127.0.0.1: under the tailnet access mode the unit publishes no port,
    and the only way in is through tsdproxy. BASE_URL is what Zerobyte itself
    builds its links from, so it is right in every access mode.
    """
    if not ENV.exists():
        return None
    m = re.search(r"(?m)^\s*BASE_URL\s*=\s*(\S+)", ENV.read_text())
    return m.group(1).strip("\"'") if m else None


def main():
    qhui.argparse_ptbr()
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--url", default=os.environ.get("ZEROBYTE_URL") or url_do_env(),
                    help=loc("base URL of Zerobyte (default: BASE_URL from its .env)"))
    ap.add_argument("--repository", help=loc("where the backup runs (default: the only one)"))
    ap.add_argument("--no-mirror", action="store_true",
                    help=loc("turn mirroring off: clears the mirrors on every job"))
    ap.add_argument("--cron", default="0 3 * * *", help=loc("schedule (default: 03:00 daily)"))
    ap.add_argument("--hook-port", default="8766")
    ap.add_argument("--apply", action="store_true", help=loc("execute (without it, only show)"))
    a = ap.parse_args()

    if not a.url:
        raise SystemExit(f"{loc('no BASE_URL in')} {ENV} — {loc('pass --url')}")
    if not CHAVE.is_file():
        raise SystemExit(f"{loc('no API key at')} {CHAVE} — {loc('create one in Settings -> API keys')}")
    key = CHAVE.read_text().strip()
    token = TOKEN.read_text().strip() if TOKEN.is_file() else None

    repos = api(a.url, key, "repositories")
    if a.repository:
        repo = a.repository
    elif len(repos) == 1:
        repo = repos[0]["shortId"]
    else:
        # With the ids listed: they are only visible in the URL of the
        # repository's page, so an error telling you to pass one without
        # saying where to find it is an error you cannot act on.
        raise SystemExit(
            f"{len(repos)} " + loc("repositories — say which one runs the backup "
                                   "with --repository (the others become mirrors)")
            + ":\n" + "\n".join(f"  --repository {r['shortId']:10} {r['name']}"
                                for r in repos))
    # Every other registered repository mirrors this one. A second job per
    # destination would run the backup twice: two stops of any-sync-bundle, two
    # SQLite copies, and two chances to differ. A mirror copies the snapshot
    # that was already made, so what lands remotely is what was verified here.
    espelhos = [r["shortId"] for r in repos if r["shortId"] != repo]

    # shortId by name, so a second run changes nothing
    volumes = {v["name"]: v["shortId"] for v in api(a.url, key, "volumes")}
    jobs = {b["name"]: b for b in api(a.url, key, "backups")}

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
            print(f"  {nome:24} " + loc("job already exists")
                  + ajusta_job(a, key, jobs[nome], excluir(nome)))
            continue
        if m != "none" and not token:
            print(f"  {nome:24} " + loc("needs the hook") + f" ({m}), " + loc("but there is no token — skipping"))
            continue
        if m == "stop" and not any(UNITS.rglob(f"{nome}.container")):
            # `stop` is `systemctl stop <name>`, so the folder name has to BE a
            # unit. media-stack is the case that is not: twelve units share the
            # directory, and one of them (dispatcharr) carries a Postgres. No
            # single hook call is right there, so this asks instead of guessing.
            print(f"  {nome:24} " + loc("needs stop, but there is no unit")
                  + f" `{nome}` — " + loc("declare this job by hand"))
            continue
        alvo = f"/sources/volumes/{nome}"
        print(f"  {nome:24} {loc('volume')} {alvo}  |  {loc('mode')} {m}")
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
                 "enabled": True, "cronExpression": a.cron,
                 "excludePatterns": excluir(nome), "excludeIfPresent": list(EXCLUIR_SE),
                 "retentionPolicy": dict(RETENCAO)}
        if m != "none":
            corpo["backupWebhooks"] = ganchos(nome, a.hook_port, token)
        api(a.url, key, "backups", "POST", corpo)

    # The secrets, as one job. Restoring a data volume without them gives a
    # service that starts and does not work: vaultwarden's admin token no
    # longer matches, excalidash's JWT_SECRET logs everyone out.
    #
    # One job and not one per app: a Zerobyte job covers a single directory —
    # includePaths and customResticParams are joined to the volume's path, they
    # do not reach outside — so the secrets cannot ride along in the app's own
    # job anyway. Restoring is selective, so one snapshot holding all of them
    # gives the same choice at the moment it matters.
    if SECRETS.is_dir() and "secrets" not in jobs:
        print(f"  {'secrets':24} {loc('volume')} /sources/secrets  |  {loc('mode')} none")
        if a.apply:
            if "secrets" not in volumes:
                api(a.url, key, "volumes", "POST",
                    {"name": "secrets",
                     "config": {"backend": "directory", "path": "/sources/secrets"}})
                volumes = {v["name"]: v["shortId"] for v in api(a.url, key, "volumes")}
            api(a.url, key, "backups", "POST",
                {"name": "secrets", "volumeId": volumes["secrets"], "repositoryId": repo,
                 "enabled": True, "cronExpression": a.cron,
                 "excludePatterns": list(EXCLUIR), "excludeIfPresent": list(EXCLUIR_SE),
                 "retentionPolicy": dict(RETENCAO)})
    elif "secrets" in jobs:
        print(f"  {'secrets':24} " + loc("job already exists")
              + ajusta_job(a, key, jobs["secrets"], list(EXCLUIR)))

    # --no-mirror writes an empty list rather than skipping the step: skipping
    # would leave yesterday's mirrors in place, so the flag would turn nothing
    # off — and turning them off by hand is job by job, through the interface.
    todos = api(a.url, key, "backups")
    destinos = [d["id"] for d in api(a.url, key, "notifications/destinations")]
    if destinos:
        mudou = sum(1 for b in todos if ajusta_avisos(a, key, b, destinos))
        print(f"\n{loc('alerting on failure')}: {len(destinos)} → {mudou} job(s)")
    else:
        # Without one, a failed job is only visible to whoever goes looking.
        print(f"\n{loc('no notification destination: create one in Settings -> Notifications')}")

    if espelhos or a.no_mirror:
        alvo = set() if a.no_mirror else set(espelhos)
        print(f"\n{loc('clearing the mirrors on every job')}" if a.no_mirror else
              f"\n{loc('mirroring')} {len(espelhos)} {loc('repository(ies) on every job')}")
        for b in todos:
            if not a.apply:
                continue
            atual = {m["repositoryId"]
                     for m in api(a.url, key, f"backups/{b['shortId']}/mirrors")}
            if atual == alvo:  # same rule as the jobs: a second run changes nothing
                continue
            api(a.url, key, f"backups/{b['shortId']}/mirrors", "PUT",
                {"mirrors": [{"repositoryId": r, "enabled": True} for r in sorted(alvo)]})
            # Enabling a mirror copies nothing: the first copy happens when the
            # job next runs. Without this the new repository stays empty until
            # 03:00, which reads as the command having done nothing at all. Only
            # for mirrors that were just added, and never fatal — the copy is a
            # convenience, while the list above is what has to land.
            for r in sorted(alvo - atual):
                try:
                    # The `{}` matters: the endpoint takes no arguments, but
                    # rejects a JSON content type with no body ("Malformed body").
                    api(a.url, key, f"backups/{b['shortId']}/mirrors/{r}/sync", "POST", {})
                except SystemExit as e:
                    print(f"  {b['name']:24} {loc('first copy failed')}: {e}")

    if alheias:
        print(f"\n{loc('outside this repository, left alone')}: {', '.join(alheias)}")
    if allowlist:
        # A job whose hook is not in the allowlist gets a 404 on pre-backup,
        # and Zerobyte treats that as a failed backup. Printing the line beats
        # finding out at 03:00.
        print(loc("\nZEROBYTE_HOOK_UNITS must include these, or the jobs fail:"))
        print("  " + ",".join(sorted(allowlist)))
    if not a.apply:
        print(loc("\nnothing was done. repeat with --apply"))


if __name__ == "__main__":
    main()
