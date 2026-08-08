#!/usr/bin/env python3
"""Exercises install.py's lifecycle in a sandbox, the way it is actually used.

It calls the script as a subprocess instead of importing functions: what breaks
in practice is the command line, and that is where the defects showed up.

Runs without podman and without systemd — `--prefix` turns on sandbox mode,
which touches files only. That is the same reason this fits in a bare CI runner.

    python3 test_install.py
"""

import shutil
import subprocess
import sys
import tarfile
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent
APP = "homebox"          # volume + secret + .env + User=: covers all four cases

failures = []


def run(*args, stdin="", expected=0):
    r = subprocess.run([sys.executable, str(ROOT / "install.py"), *args],
                       capture_output=True, text=True, input=stdin, cwd=ROOT)
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


def scenario_restore_refuses(home, tgz, out):
    run(APP, "--restore", str(Path(out) / "missing.tar.gz"), "--apply",
        "--prefix", home, stdin=f"{APP}\n", expected=1)
    check(True, "restoring a missing file exits 1")

    other = "traccar"
    r = run(other, "--restore", str(tgz), "--apply", "--prefix", home,
            stdin=f"{other}\n", expected=1)
    check("does not look like a backup" in r.stdout,
          "restore refuses a .tar.gz from another service")

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


def main():
    with tempfile.TemporaryDirectory() as tmp:
        home, out = str(Path(tmp) / "home"), str(Path(tmp) / "backups")
        Path(out).mkdir(parents=True)

        print("install:");            scenario_install(home)
        print("user files:");         scenario_no_overwrite(home)
        print("backup and restore:"); tgz = scenario_backup_restore(home, out)
        if tgz:
            print("restore refuses:"); scenario_restore_refuses(home, tgz, out)
        print("removal:");            scenario_remove(home)

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
