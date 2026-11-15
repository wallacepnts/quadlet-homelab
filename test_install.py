#!/usr/bin/env python3
"""Exercises install.py's lifecycle in a sandbox, the way it is actually used.

It calls the script as a subprocess instead of importing functions: what breaks
in practice is the command line, and that is where the defects showed up.

Runs without podman and without systemd — `--prefix` turns on sandbox mode,
which touches files only. That is the same reason this fits in a bare CI runner.

    python3 test_install.py
"""

import importlib.util
import shutil
import os
import subprocess
import sys
import tarfile
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent
_spec = importlib.util.spec_from_file_location("qh_install", ROOT / "install.py")
I = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(I)          # restart_order is pure: worth asserting directly
APP = "homebox"          # volume + secret + .env + User=: covers all four cases
STACK = "immich"         # 4 containers + a shared .network, in a subfolder

failures = []


def run(*args, stdin="", expected=0):
    # QH_LANG=en so the assertions do not depend on the machine's locale.
    env = {**os.environ, "QH_LANG": "en"}
    r = subprocess.run([sys.executable, str(ROOT / "install.py"), *args],
                       capture_output=True, text=True, input=stdin, cwd=ROOT, env=env)
    if r.returncode != expected:
        failures.append(f"`install.py {' '.join(args)}` exited {r.returncode}, "
                        f"expected {expected}\n{r.stdout}{r.stderr}")
    return r


def check(condition, description):
    if condition:
        print(f"  ok    {description}")
    else:
        print(f"  FAIL  {description}")
        failures.append(description)


def path(home, *parts):
    return Path(home, ".config/containers", *parts)


def scenario_install(home):
    run(APP, "--apply", "--prefix", home)
    check(path(home, "systemd", f"{APP}.container").is_file(), "install copies the unit")
    check(path(home, "volumes", APP, "data").is_dir(), "install creates the volume")
    check(path(home, "env", f"{APP}.env").is_file(), "install writes the .env")
    check(path(home, "secrets", APP).is_dir(), "install generates the secret")


def scenario_no_overwrite(home):
    env = path(home, "env", f"{APP}.env")
    env.write_text("EDITED_BY_THE_USER=1\n")
    again = run(APP, "--apply", "--prefix", home, expected=1)
    check("already installed" in again.stdout and "--reinstall" in again.stdout,
          "installing again refuses, naming the two ways out")
    check(env.read_text() == "EDITED_BY_THE_USER=1\n",
          "the refused install does NOT overwrite an edited .env")
    run(APP, "--reinstall", "--apply", "--prefix", home)
    check("EDITED_BY_THE_USER" not in env.read_text(),
          "--reinstall overwrites the .env")


def scenario_failure(home, tmp):
    """A plan that fails partway must not leave the service stopped, or lie.

    The stop that makes a backup cold is only safe if the start is guaranteed:
    a typo in `--out` used to stop the service, abort at `tar`, never reach the
    start, and still print `done: 1 backup`.
    """
    # Read-only, not missing: a missing --out is created now, and the point of
    # this scenario is a step that fails AFTER the stop, with a start to undo it.
    destino = Path(tmp, "so-leitura")
    destino.mkdir(exist_ok=True)
    destino.chmod(0o500)
    try:
        r = run(APP, "--backup", "--apply", "--prefix", home,
                "--out", str(destino), expected=1)
    finally:
        destino.chmod(0o700)
    saida = r.stdout + r.stderr
    check("FAILED at:" in saida, "a failed backup says where it failed")
    check("putting back what the failure stopped" in saida,
          "and runs the start the failure skipped")
    check("done:" not in saida, "a failed run does NOT print the green done line")
    check("Traceback" not in saida, "no traceback reaches the user")

    # An OSError is not a CalledProcessError: the loop used to let it through.
    # The target is the unit file, not its directory — a read-only directory
    # still allows overwriting a file that is already in it.
    alvo = path(home, "systemd", f"{APP}.container")
    modo = alvo.stat().st_mode
    alvo.chmod(0o400)
    try:
        r = run(APP, "--update", "--apply", "--prefix", home, expected=1)
        saida = r.stdout + r.stderr
        check("FAILED at:" in saida and "Traceback" not in saida,
              "a read-only unit file is reported, not raised")
    finally:
        alvo.chmod(modo)


def scenario_drift(home):
    """An edit made on the host has to survive being *named* before it is lost.

    The plan used to say only `cp unit -> target`, which reads as housekeeping;
    the line a hand had commented out to keep a port closed went with it and
    nothing said so.
    """
    unit = path(home, "systemd", f"{APP}.container")
    original = unit.read_text()
    unit.write_text(original.replace("[Container]",
                                     "[Container]\n# minha linha, escrita na mao"))
    seco = run(APP, "--update", "--prefix", home)
    check("differs" in seco.stdout and "minha linha" in seco.stdout,
          "--update names the host's own line before overwriting it")
    check("# minha linha" in unit.read_text(),
          "the dry run does not touch the file it warned about")
    run(APP, "--update", "--apply", "--prefix", home)
    check("# minha linha" not in unit.read_text(),
          "--apply does go through with the overwrite it announced")
    unit.write_text(original)
    limpo = run(APP, "--update", "--prefix", home)
    check("differs" not in limpo.stdout,
          "a unit matching the repository raises no drift warning")


def scenario_remove_safety(tmp):
    """A removal has to take the units, and only this unit's.

    Two ways it got that wrong. The flat layout — where a service sits whenever
    it gained a `.network` after being installed — left every file on disk
    while `--purge` deleted the data, and reported success: the next
    daemon-reload brought the whole stack back against an empty volume. And
    removing one unit of a stack took the shared `.network` with it, so the
    siblings stopped generating at all.
    """
    home = str(Path(tmp, "stack"))
    run(STACK, "--apply", "--prefix", home)
    sub = path(home, "systemd", STACK)
    check(sub.is_dir(), "the stack installs into its own subfolder")

    r = run(f"{STACK}-postgres", "--remove", "--apply", "--prefix", home)
    restantes = sorted(x.name for x in sub.iterdir())
    check(f"{STACK}-postgres.container" not in restantes,
          "removing one unit takes that unit")
    check(f"{STACK}-net.network" in restantes,
          "and leaves the .network its siblings still declare")
    check("data deleted" not in r.stdout,
          "a remove with no --purge does not claim data was deleted")

    # The flat layout: every unit loose in systemd/, which Service.installed()
    # and strays() both support and plan_remove used to walk straight past.
    plano = str(Path(tmp, "flat"))
    run(STACK, "--apply", "--prefix", plano)
    origem = path(plano, "systemd", STACK)
    for f in origem.iterdir():
        f.rename(path(plano, "systemd", f.name))
    origem.rmdir()
    run(STACK, "--remove", "--purge", "--apply", "--prefix", plano, stdin=f"{STACK}\n")
    sobraram = sorted(x.name for x in path(plano, "systemd").iterdir())
    check(not sobraram, f"a purge on the flat layout takes the units too ({sobraram})")
    check(not path(plano, "volumes", STACK).exists(),
          "and the data, which it already did")


def scenario_backup_restore(home, out):
    data = path(home, "volumes", APP, "data", "db.sqlite")
    data.write_text("backup-state")
    run(APP, "--backup", "--apply", "--prefix", home, "--out", out)
    tgz = next(Path(out).glob(f"{APP}-*.tar.gz"), None)
    check(tgz is not None, "backup produces the .tar.gz")
    if tgz is None:
        return None
    with tarfile.open(tgz) as t:
        inside = t.getnames()
    check(any(n.startswith("volumes/") for n in inside), "backup carries the volume")
    check(any(n.startswith("secrets/") for n in inside), "backup carries the secret")
    check(any(n.startswith("env/") for n in inside), "backup carries the .env")

    # The case the code review caught: in the sandbox the rm ran while the
    # extraction was only announced, so restoring deleted without putting back.
    data.write_text("changed-state")
    leftover = path(home, "volumes", APP, "data", "created-later.txt")
    leftover.write_text("should-not-survive")
    run(APP, "--restore", str(tgz), "--apply", "--prefix", home, stdin=f"{APP}\n")
    check(data.is_file() and data.read_text() == "backup-state",
          "restore puts the backup's content back")
    # And the other one: `tar x` on its own overwrites what is in the archive
    # and leaves the rest — with SQLite, an orphan -wal over an old .db corrupts.
    check(not leftover.exists(), "restore is a swap, not a mix (the new file is gone)")
    return tgz


def scenario_access(tmp):
    """The mode a unit was installed with has to survive reading it back.

    It was recovered by grepping for the comments the render leaves behind,
    which only exist on a unit carrying tsdproxy labels or a proxied port — so
    19 containers answered "both" however they were installed, `qh` reported 14
    services as permanently out of compliance, and `--href-local` was not
    representable at all. `unit_bytes` is pure, so the honest way to read the
    settings back is to render the combinations and see which one matches.
    """
    fonte = Path(ROOT, "apps", "memos", "memos.container")
    alvo = Path(tmp, "memos.container")
    for modo in I.ACCESS_MODES:
        alvo.write_bytes(I.unit_bytes(fonte, modo, False))
        lido = I.installed_access(alvo, fonte)
        check(lido[0] == modo, f"a unit written as --access {modo} reads back as {modo}")
    alvo.write_bytes(I.unit_bytes(fonte, "both", True))
    check(I.installed_access(alvo, fonte)[1] is True,
          "--href-local is representable, not invisible")

    # A unit the mode does not change says so, instead of guessing "both".
    sidecar = Path(ROOT, "apps", "immich", "immich-postgres.container")
    alvo.write_bytes(I.unit_bytes(sidecar, "local", False))
    check(I.installed_access(alvo, sidecar) == (None, None),
          "a unit with no tsdproxy label admits the mode cannot be told")

    # And the two paths that were silently reverting it.
    home = str(Path(tmp, "acc"))
    run(APP, "--apply", "--access", "local", "--prefix", home)
    unidade = path(home, "systemd", f"{APP}.container")
    antes = unidade.read_bytes()
    run(APP, "--reinstall", "--apply", "--prefix", home)
    check(unidade.read_bytes() == antes,
          "--reinstall keeps the mode the host already had")

    casa = str(Path(tmp, "acc2"))
    run(APP, "--apply", "--access", "both", "--href-local", "--prefix", casa)
    u2 = path(casa, "systemd", f"{APP}.container")
    href = [l for l in u2.read_text().splitlines() if "homepage.href" in l]
    os.utime(u2, (0, 0))
    run(APP, "--update", "--apply", "--prefix", casa)
    check([l for l in u2.read_text().splitlines() if "homepage.href" in l] == href,
          "and --update does not revert --href-local")

    # A per-service exception survives the update that follows the rule.
    casa3 = str(Path(tmp, "acc3"))
    run("--set-access", "tailnet", "--prefix", casa3)
    run(APP, "--apply", "--prefix", casa3)
    run("--set-access", "local", APP, "--prefix", casa3)
    u3 = path(casa3, "systemd", f"{APP}.container")
    os.utime(u3, (0, 0))
    # Read by the comment `--access local` leaves, not by installed_access: this
    # process renders in the machine's language and the runs above in English.
    local = lambda: "# disabled by --access local: Label=tsdproxy.enable" in u3.read_text()
    run(APP, "--update", "--apply", "--prefix", casa3)
    check(local(), "--set-access MODE APP makes that service local while the rule stays tailnet")
    # exit 1: every service the sandbox never installed is "nothing to do"
    run("--all", "--update", "--apply", "--prefix", casa3, expected=1)
    check(local(), "and `--all --update` does not write it back to the rule")
    run("--set-access", "default", "--prefix", casa3, expected=2)


def scenario_answers(tmp):
    """Six answers the tool gave wrong, each on its own.

    The sharpest: `"unhealthy" in c` was tested before `"unhealthy"`, and
    "unhealthy" contains "healthy" — so a failing container printed green,
    never counted as needing attention, and `--status` exited 0.
    """
    # The real function, not a copy of its logic here: asserting a
    # reimplementation is how the restart-order test passed while the call site
    # was still wrong.
    check(I.estado_do_container("Up 2 hours (unhealthy)") == "unhealthy",
          "an unhealthy container does not read as healthy")
    check(I.estado_do_container("Up 2 hours (healthy)") == "healthy",
          "and a healthy one still does")
    check(I.estado_do_container("Exited (1) 3 minutes ago") == "down",
          "and a stopped one is down")

    # addresses() narrows to the picked unit, like every other accessor.
    s = I.Service("media-stack", None, "media-stack-jellyfin")
    check(len(I.addresses(s, "exemplo")) == 1,
          "a picked unit gets its own address, not the folder's twelve")

    # ${VAR} volumes reach the branch written for them.
    tipos = dict((f, t) for f, t in
                 ((p, tipo) for p, tipo in I.Service("frigate").volumes()))
    check(any(t is None for t in tipos.values()),
          "a ${VAR} volume is classified, not dropped before the test for it")

    # A typed value is data, not a regex replacement template.
    env = Path(tmp, "v.env")
    env.write_text("BOOT=alpine\n")
    I.set_env_value(env, "BOOT", r"C:\Users\me\x.iso")
    check(env.read_text().strip() == r"BOOT=C:\Users\me\x.iso",
          "a backslash in a typed value is stored, not interpreted")
    I.set_env_value(env, "BOOT", r"\g<0>")
    check(env.read_text().strip() == r"BOOT=\g<0>",
          "and neither is a group reference")

    # --status resolves a unit basename, and says so on a typo.
    home = str(Path(tmp, "st"))
    run("vm-windows", "--apply", "--prefix", home)
    # exit 1 because nothing is running in a sandbox, which is what --status is
    # for; the question here is only whether the basename resolved at all.
    r = run("--status", "vm-windows", "--prefix", home, expected=1)
    check("vm-windows" in r.stdout, "--status accepts a unit basename")
    r = run("--status", "vm-widnows", "--prefix", home, expected=1)
    check("not found" in r.stdout, "and a typo is reported, not answered")


def scenario_update_gaps(tmp):
    """An update is the weekly command, and it did less than an install.

    A version that adds a `Volume=` or a `User=` was copied and then died at
    the restart, because rule 6 was enforced on install only. The restart order
    went main-first, so the unit the tool followed to healthy was torn down
    twice more by its own dependencies. And on the flat-to-subfolder migration
    the drift warning compared against a file that did not exist yet, so a hand
    edit went out with the stray removal without a word.
    """
    check(I.restart_order(sorted(Path(ROOT, "apps", "owntracks").glob("*.container")))
          == ["owntracks-mosquitto", "owntracks-recorder", "owntracks-frontend"],
          "a two-deep chain orders dependencies first, main last")

    # And the plan has to USE it: asserting the function alone passed while the
    # call site still went main-first.
    ordenado = str(Path(tmp, "ordem"))
    run(STACK, "--apply", "--prefix", ordenado)
    for f in path(ordenado, "systemd", STACK).iterdir():
        os.utime(f, (0, 0))
    r = run(STACK, "--update", "--prefix", ordenado)
    reinicios = [l.split("restart ")[1].split()[0]
                 for l in r.stdout.splitlines() if "systemctl --user restart" in l]
    check(reinicios and reinicios[-1] == STACK,
          f"the plan restarts the main unit last ({reinicios})")

    home = str(Path(tmp, "upd"))
    run(APP, "--apply", "--prefix", home)
    unidade = path(home, "systemd", f"{APP}.container")

    # A missing volume directory is created by the update, not left to podman.
    alvo = path(home, "volumes", APP, "data")
    shutil.rmtree(alvo)
    unidade.write_text(unidade.read_text().replace("Image=", "# touched\nImage=", 1))
    r = run(APP, "--update", "--prefix", home)
    check(f"mkdir -p {alvo}" in r.stdout, "an update creates a Volume= that is missing")

    # The drift warning has to read the file that is actually there.
    plano = str(Path(tmp, "upd-flat"))
    run(STACK, "--apply", "--prefix", plano)
    origem = path(plano, "systemd", STACK)
    for f in origem.iterdir():
        f.rename(path(plano, "systemd", f.name))
    origem.rmdir()
    alvo = path(plano, "systemd", f"{STACK}.container")
    alvo.write_text(alvo.read_text().replace("[Container]", "[Container]\n# minha linha", 1))
    r = run(STACK, "--update", "--prefix", plano)
    check("minha linha" in r.stdout,
          "and names a hand edit even when the unit is moving address")


def scenario_sandbox(tmp):
    """--prefix promises not to touch the real host. It was touching it.

    `find_tailnet` read the real $HOME, so a rehearsal wrote the live tailnet
    name into the sandbox `.env` files and printed it — the leak CLAUDE.md
    records as having already happened once, "num bloco que mostrava a saída do
    install.py", and CI builds one sandbox per app exactly this way.
    """
    home = str(Path(tmp, "caixa"))
    env = {**os.environ, "QH_LANG": "en", "TAILNET": "segredo-de-teste"}
    r = subprocess.run([sys.executable, str(ROOT / "install.py"), APP,
                        "--apply", "--prefix", home],
                       capture_output=True, text=True, cwd=ROOT, env=env)
    escrito = "".join(f.read_text(errors="replace")
                      for f in Path(home).rglob("*") if f.is_file())
    check("segredo-de-teste" not in (r.stdout + r.stderr),
          "a sandbox run does not print the tailnet name")
    check("segredo-de-teste" not in escrito,
          "and does not write it into the files it creates")
    check("${TAILNET}" in escrito, "the unit keeps the variable instead")

    # Credentials are not world-readable, wherever they land.
    for f in [path(home, "env", f"{APP}.env"),
              *Path(path(home, "secrets", APP)).glob("*.txt")]:
        check(oct(f.stat().st_mode)[-3:] == "600", f"{f.name} is 0600")
    check(oct(path(home, "secrets", APP).stat().st_mode)[-3:] == "700",
          "and the secrets directory is 0700")

    # --verify consults systemd, podman and the tailnet; a sandbox has none.
    r = run(APP, "--verify", "--prefix", home, expected=2)
    check("--prefix" in (r.stdout + r.stderr),
          "--verify refuses under --prefix instead of asking the real host")


def scenario_archive_safety(tmp):
    """What a backup promises: it can be restored, and only over its own service.

    Three ways it did not. A per-unit archive was refused by the same tool that
    wrote it, because the identity check cut every entry to two path components
    before comparing against full-depth paths. The check passed on ONE matching
    entry, so the rest of the tar — another service's units and secrets — came
    along. And the volume was deleted before tar ran, so an archive tar gave up
    on left the data gone with nothing put back.
    """
    home = str(Path(tmp, "arq"))
    out = str(Path(tmp, "arq-out"))
    unidade = "media-stack-jellyfin"
    run(unidade, "--apply", "--prefix", home)
    run(unidade, "--backup", "--apply", "--prefix", home, "--out", out)
    tgz = sorted(Path(out).glob(f"{unidade}-*.tar.gz"))
    check(bool(tgz), "a single unit of a stack can be backed up")
    if not tgz:
        return
    r = run(unidade, "--restore", str(tgz[0]), "--apply", "--prefix", home,
            stdin=f"{unidade}\n")
    check("restored." in r.stdout, "and the same tool takes it back")

    # One matching entry must not license the whole tar.
    mal = Path(tmp, "mal")
    (mal / "volumes" / "media-stack" / "jellyfin").mkdir(parents=True, exist_ok=True)
    (mal / "secrets" / "vaultwarden").mkdir(parents=True, exist_ok=True)
    (mal / "secrets" / "vaultwarden" / "admin-token.txt").write_text("stolen\n")
    envenenado = Path(tmp, "poison.tar.gz")
    subprocess.run(["tar", "czf", str(envenenado), "-C", str(mal),
                    "volumes/media-stack", "secrets/vaultwarden"], check=True)
    r = run(unidade, "--restore", str(envenenado), "--prefix", home, expected=1)
    check("secrets/vaultwarden" in r.stdout,
          "an archive carrying another service's paths is refused, naming them")

    # A tar that fails must not have deleted anything first.
    vivo = path(home, "volumes", "media-stack", "jellyfin")
    antes = sorted(x.name for x in vivo.rglob("*"))
    truncado = Path(tmp, "truncado.tar.gz")
    truncado.write_bytes(tgz[0].read_bytes()[:200])
    r = run(unidade, "--restore", str(truncado), "--apply", "--prefix", home,
            stdin=f"{unidade}\n", expected=1)
    check("Traceback" not in (r.stdout + r.stderr),
          "a truncated archive is reported, not raised")
    check(sorted(x.name for x in vivo.rglob("*")) == antes,
          "and the live data is still there")


def scenario_restore_refuses(home, tgz, out):
    run(APP, "--restore", str(Path(out) / "missing.tar.gz"), "--apply",
        "--prefix", home, stdin=f"{APP}\n", expected=1)
    check(True, "restoring a missing file exits 1")

    other = "traccar"
    r = run(other, "--restore", str(tgz), "--apply", "--prefix", home,
            stdin=f"{other}\n", expected=1)
    check(f"{APP}" in r.stdout and "carries paths that are not" in r.stdout,
          "restore refuses a .tar.gz from another service, naming what is foreign")

    broken = Path(out) / "broken.tar.gz"
    broken.write_bytes(b"this is not a tar")
    run(APP, "--restore", str(broken), "--apply", "--prefix", home,
        stdin=f"{APP}\n", expected=1)
    check(True, "restoring an unreadable file exits 1")


def scenario_remove(home):
    run(APP, "--remove", "--apply", "--prefix", home)
    check(not path(home, "systemd", f"{APP}.container").exists(),
          "remove takes the unit away")
    check(path(home, "volumes", APP).is_dir(), "remove KEEPS the data")

    run(APP, "--remove", "--purge", "--apply", "--prefix", home, stdin="wrong\n",
        expected=1)
    check(path(home, "volumes", APP).is_dir(),
          "a cancelled purge deletes nothing")

    run(APP, "--remove", "--purge", "--apply", "--prefix", home, stdin=f"{APP}\n")
    check(not path(home, "volumes", APP).exists(), "a confirmed purge deletes the volume")
    check(not path(home, "env", f"{APP}.env").exists(), "purge deletes the .env")


def scenario_recovery(tmp):
    """The recovery runbook, exercised: a wiped machine plus a .tar.gz.

    It exists so the order documented in the README does not go stale on its
    own — install first, restore afterwards.
    """
    home, out = str(Path(tmp) / "dr-home"), str(Path(tmp) / "dr-bkp")
    Path(out).mkdir(parents=True)
    run(APP, "--apply", "--prefix", home)
    data = path(home, "volumes", APP, "data", "db.sqlite")
    data.write_text("irreplaceable-data")
    run(APP, "--backup", "--apply", "--prefix", home, "--out", out)
    tgz = next(Path(out).glob(f"{APP}-*.tar.gz"))

    shutil.rmtree(home)                      # the machine died
    Path(home).mkdir(parents=True)

    # Restoring without installing has to refuse, with the command that fixes
    # it, instead of blowing up halfway through the extraction.
    r = run(APP, "--restore", str(tgz), "--apply", "--prefix", home,
            stdin=f"{APP}\n", expected=1)
    check("is not installed" in r.stdout,
          "restore on a wiped machine tells you to install first")

    run(APP, "--apply", "--prefix", home)
    run(APP, "--restore", str(tgz), "--apply", "--prefix", home, stdin=f"{APP}\n")
    check(data.is_file() and data.read_text() == "irreplaceable-data",
          "install + restore recovers the data on a wiped machine")
    check(path(home, "secrets", APP).is_dir() and
          path(home, "env", f"{APP}.env").is_file(),
          "recovery brings back the secret and the .env")


def scenario_local(home):
    run("memos", "--apply", "--prefix", home, "--local")
    # A glob rather than a fixed path: a service with 2+ Quadlet files goes into
    # a subfolder under systemd/, and memos is one of them (it has a .network).
    unit = next(path(home, "systemd").rglob("memos.container")).read_text()
    href = next((l for l in unit.splitlines() if l.startswith("Label=homepage.href")), "")
    check("${TAILNET}" not in href and href.startswith("Label=homepage.href=http://"),
          f"--local swaps the href for the LAN address ({href.split('=')[-1]})")


def scenario_catalog(home):
    """--catalog is what a front end reads: valid JSON, every app, the host's state."""
    import json
    r = run("--catalog", "--prefix", home)
    try:
        cat = json.loads(r.stdout)
    except ValueError:
        check(False, "--catalog prints JSON and nothing else")
        return
    apps = {a["id"]: a for a in cat["apps"]}
    pastas = {p.parent.name for p in (ROOT / "apps").glob("*/*.container")}
    check(set(apps) == pastas, "--catalog lists every folder that has a .container")
    sem = sorted(a for a, x in apps.items()
                 if not (x["icon"] and x["description"]["en"] and x["description"]["pt"]))
    check(not sem, "every app has an icon and both descriptions from the READMEs"
          + (f" (missing: {', '.join(sem)})" if sem else ""))
    grupos = {x["group"]["en"] for x in apps.values() if x["group"]}
    check(apps["vm"]["group"] == {"en": "Virtual Machines", "pt": "Máquinas Virtuais"}
          and all(g and '"' not in g for g in grupos),
          "--catalog takes the category from homepage.group, quotes stripped, in both languages")
    check(apps[APP]["installed"] and all(u["installed"] for u in apps[APP]["units"]),
          "--catalog sees the sandbox install")
    check(not apps[STACK]["installed"], "--catalog does not see what was never installed")
    check(cat["tailnet"] is False, "--catalog under --prefix never reads the real tailnet")
    manuais = [s["secret"] for s in apps["vaultwarden"]["asks"]["secrets"]]
    check(manuais == ["vaultwarden-admin-token"],
          "--catalog names the `manual` secrets a form has to ask for")
    one = json.loads(run("--catalog", APP, "--prefix", home).stdout)
    check([a["id"] for a in one["apps"]] == [APP], "--catalog APP narrows to that service")


def scenario_override(tmp):
    """A customization is a drop-in beside the unit: qh sees it, keeps it, and removes it with the unit."""
    import json
    O = I.overrides
    home = str(Path(tmp, "ov"))
    run(APP, "--apply", "--prefix", home)
    unit = path(home, "systemd", f"{APP}.container")
    base = O.base_of(unit.read_text())
    texto = f"# base={O.base_hash(base)}\n[Container]\nEnvironment=\nEnvironment=NOVA=1\n"
    O.write_override(unit, texto)

    cat = json.loads(run("--catalog", APP, "--prefix", home).stdout)["apps"][0]
    check(cat["units"][0]["override"] is True, "--catalog says which unit carries a customization")
    check(json.loads(run("--catalog", "--prefix", str(Path(tmp, "vazio"))).stdout)["apps"][0]["units"][0]["override"] is False,
          "and false where there is none")
    # exit 1: nothing is running in a sandbox, which --status counts as needing attention
    check("customized" in run("--status", "--prefix", home, expected=1).stdout, "--status marks it")

    # An update leaves the drop-in alone and says so; the unit is made stale so there is something to update.
    unit.write_text(unit.read_text() + "# stale\n")
    out = run(APP, "--update", "--prefix", home).stdout
    check("keeps its customization" in out, "--update says it keeps the customization")
    check(O.read_override(unit) == texto, "and does not touch the file")
    # One written against another version of the unit is flagged, not silently kept.
    O.write_override(unit, texto.replace(O.base_hash(base), "0" * 16))
    check("older version of the unit" in run(APP, "--update", "--prefix", home).stdout,
          "a customization written against an older unit is flagged")
    run(APP, "--update", "--apply", "--prefix", home)
    check(O.read_override(unit) is not None, "--update --apply keeps the drop-in")

    run(APP, "--remove", "--apply", "--prefix", home)
    check(O.read_override(unit) is None and not O.dropin_path(unit).parent.exists(),
          "--remove takes the customization with the unit")


def scenario_deprecated(tmp):
    """A service marked deprecated in install.ini: qh warns, the catalog says so, `--all` leaves it out.

    Run from a copy of the repository, because the marking lives in a file of the repo."""
    import json
    raiz = Path(tmp, "dep-repo")
    raiz.mkdir()
    for f in ("install.py", "qhui.py", "overrides.py", "trials.py"):
        shutil.copy(ROOT / f, raiz / f)
    shutil.copytree(ROOT / "apps", raiz / "apps", ignore_dangling_symlinks=True)   # apps/durockrj may point nowhere
    import configparser
    ini = raiz / "apps" / APP / "install.ini"
    cp = configparser.ConfigParser(interpolation=None)
    cp.optionxform = str
    cp.read(ini)
    if not cp.has_section("store"):          # an app may already carry one, for its screenshots
        cp.add_section("store")
    cp.set("store", "deprecated", "Archived upstream.")
    cp.set("store", "deprecated_pt", "Arquivado no upstream.")
    with open(ini, "w") as fh:
        cp.write(fh)
    home = str(Path(tmp, "dep-home"))

    def executa(*args, lang="en"):
        r = subprocess.run([sys.executable, str(raiz / "install.py"), *args], capture_output=True, text=True,
                           cwd=raiz, env={**os.environ, "QH_LANG": lang})
        return r.stdout + r.stderr, r.returncode
    out, _ = executa(APP, "--prefix", home)
    check("this service is marked deprecated: Archived upstream." in out, "qh warns, with the reason, before installing")
    out, _ = executa(APP, "--prefix", home, lang="pt")
    check("descontinuado: Arquivado no upstream." in out, "…in Portuguese, with the Portuguese reason")
    cat = json.loads(executa("--catalog", APP, "--prefix", home)[0])["apps"][0]
    check(cat["deprecated"] == {"en": "Archived upstream.", "pt": "Arquivado no upstream."}, "--catalog carries the reason in both languages")
    outro = json.loads(executa("--catalog", STACK, "--prefix", home)[0])["apps"][0]
    check(outro["deprecated"] is None, "and null for a service that is not marked")
    out, rc = executa("--all", "--prefix", home)
    check(f"{APP}: skipped, marked deprecated: Archived upstream." in out, "`--all` leaves it out and says why")
    check(f"{STACK}: skipped" not in out, "…and only that one")
    out, rc = executa(APP, "--apply", "--prefix", home)
    check(rc == 0 and (path(home, "systemd", f"{APP}.container")).is_file(), "naming it still installs: the warning is not a ban")


def scenario_trial(tmp):
    """--trial arms a self-removal; --trial-expire obeys the record and nothing beyond it."""
    import json
    import time
    home = str(Path(tmp, "trial-home"))
    rec = Path(home, ".config", "quadlet-homelab", "trials", f"{APP}.json")
    units = Path(home, ".config", "systemd", "user")
    out = run("--trial", "5m", APP, "--apply", "--prefix", home, expected=2)
    check("at least" in (out.stdout + out.stderr) or "minimum" in (out.stdout + out.stderr).lower() or out.returncode == 2,
          "a trial too short is refused")
    run(APP, "--apply", "--prefix", home, "--trial", "2h")
    check(rec.is_file() and (units / f"qh-trial-{APP}.timer").is_file(), "--trial writes the record and the timer")
    check("trial" in run("--status", "--prefix", home, expected=1).stdout, "--status marks it")
    check(APP in run("--trials", "--prefix", home).stdout, "--trials lists it")
    r = run(APP, "--apply", "--prefix", home, "--trial", "2h", expected=1)
    check("already installed" in r.stdout, "a trial over an installed service is refused")
    r = run(APP, "--trial-expire", "--prefix", home, expected=1)
    check("not due yet" in r.stdout and path(home, "systemd", f"{APP}.container").is_file(),
          "--trial-expire before its time refuses and removes nothing")
    d = json.loads(rec.read_text()); d["expires"] = int(time.time()) - 60; rec.write_text(json.dumps(d))
    run(APP, "--trial-expire", "--prefix", home)
    check(not path(home, "systemd", f"{APP}.container").is_file() and not rec.exists()
          and not (units / f"qh-trial-{APP}.timer").exists(), "after its time it removes the service and clears the trial")
    check(Path(home, ".config", "containers", "volumes", APP).exists(), "…and keeps the data, as armed")
    r = run(APP, "--apply", "--prefix", home, "--trial", "2h", "--trial-purge", expected=1)
    check("--trial-purge refused" in r.stdout and not rec.exists(), "--trial-purge over data from before is refused")
    run(APP, "--apply", "--prefix", home, "--trial", "2h")
    run(APP, "--trial-keep", "--apply", "--prefix", home)
    check(not rec.exists() and path(home, "systemd", f"{APP}.container").is_file(), "--trial-keep cancels it, the service stays")
    r = run(STACK, "--apply", "--prefix", str(Path(tmp, "trial-reboot")), "--trial", "reboot")
    d = json.loads(next(Path(tmp, "trial-reboot", ".config", "quadlet-homelab", "trials").glob("*.json")).read_text())
    check(d["mode"] == "reboot", "--trial reboot records the boot")
    r = run(STACK, "--trial-expire", "--prefix", str(Path(tmp, "trial-reboot")), expected=1)
    check("not due yet" in r.stdout, "…and does not end within the same boot")


def main():
    with tempfile.TemporaryDirectory() as tmp:
        home, out = str(Path(tmp) / "home"), str(Path(tmp) / "backups")
        Path(out).mkdir(parents=True)

        print("install:");            scenario_install(home)
        print("user files:");         scenario_no_overwrite(home)
        print("catalog:");            scenario_catalog(home)
        print("customization:");      scenario_override(tmp)
        print("deprecated:");         scenario_deprecated(tmp)
        print("drift:");              scenario_drift(home)
        print("failure:");            scenario_failure(home, tmp)
        print("remove safety:");      scenario_remove_safety(tmp)
        print("archive safety:");     scenario_archive_safety(tmp)
        print("access mode:");        scenario_access(tmp)
        print("answers:");            scenario_answers(tmp)
        print("update gaps:");        scenario_update_gaps(tmp)
        print("sandbox:");            scenario_sandbox(tmp)
        print("backup and restore:"); tgz = scenario_backup_restore(home, out)
        if tgz:
            print("restore refuses:"); scenario_restore_refuses(home, tgz, out)
        print("removal:");            scenario_remove(home)

        print("trials:");              scenario_trial(tmp)
        print("recovery:");           scenario_recovery(tmp)

        with tempfile.TemporaryDirectory() as other:
            print("without a tailnet:"); scenario_local(other)

    print()
    if failures:
        print(f"{len(failures)} failure(s):")
        for f in failures:
            print(f"  - {f.splitlines()[0]}")
        return 1
    print("everything passed")
    return 0


if __name__ == "__main__":
    sys.exit(main())
