#!/usr/bin/env python3
"""Trial installs: an app that removes itself after N hours, or at the next reboot.

`qh <app> --apply --trial 24h` installs the app as usual and arms a systemd
user timer. When it fires, `qh <app> --trial-expire` removes the app. The pieces
here are pure or file-only, so they are tested without a host:

    python3 trials.py --selftest

Why it is built the way it is — each choice is a way this could have gone wrong:

  * An ABSOLUTE time (`OnCalendar=... UTC`, `Persistent=true`), not `OnActiveSec`.
    A relative timer starts counting again at every boot, so a reboot would
    quietly extend the trial; an absolute one fires at the same instant, and
    `Persistent=` fires it at the next start when the machine was off then.
  * "Until reboot" is a oneshot service wanted by `default.target`, plus the
    boot id recorded at install. The id is what keeps it from firing in the very
    boot that installed it, and what a reboot changes.
  * The record, not the command line, says what to remove and whether to delete
    the data. That is the consent given at install time. Nothing at the timer's
    end asks, because nobody is there to answer — so nothing it was not told at
    install time may happen then.
  * A trial is only ever armed on an app the same command just installed, and
    asking it to delete data is refused when data was already there (install.py
    checks both). Those two are what separate "try this app" from "delete the
    app I use".
  * Expiring early is refused. Keeping the app deletes the record and the units,
    so an expiry that fires afterwards finds nothing to do.
"""

import json
import os
import re
import sys
import tempfile
import time
from pathlib import Path

MIN_SECONDS, MAX_SECONDS = 10 * 60, 30 * 24 * 3600
SLACK = 30                      # a timer may fire a little early; not so early that it is a mistake
_UNITS = {"m": 60, "h": 3600, "d": 86400, "w": 7 * 86400}
APP = re.compile(r"^[a-z0-9][a-z0-9-]*$")


def parse_duration(texto):
    """("time", seconds) for `30m`, `6h`, `2d`, `1w`; ("reboot", None) for `reboot`. ValueError otherwise."""
    t = (texto or "").strip().lower()
    if t == "reboot":
        return "reboot", None
    m = re.fullmatch(r"(\d+)\s*([mhdw])", t)
    if not m:
        raise ValueError("use a number and m, h, d or w (`6h`, `2d`), or `reboot`")
    segundos = int(m.group(1)) * _UNITS[m.group(2)]
    if segundos < MIN_SECONDS:
        raise ValueError(f"at least {MIN_SECONDS // 60} minutes: a shorter trial ends before it can be used")
    if segundos > MAX_SECONDS:
        raise ValueError(f"at most {MAX_SECONDS // 86400} days: past that it is not a trial anymore")
    return "time", segundos


def calendar(epoch):
    """The `OnCalendar=` value for an instant: absolute and in UTC, so no time zone or DST can move it."""
    return time.strftime("%Y-%m-%d %H:%M:%S UTC", time.gmtime(epoch))


def boot_id():
    """This boot's id, or None where it cannot be read."""
    try:
        return Path("/proc/sys/kernel/random/boot_id").read_text().strip() or None
    except OSError:
        return None


def new_record(app, modo, expira, purge, agora, boot=None):
    return {"app": app, "mode": modo, "created": int(agora), "expires": None if expira is None else int(expira),
            "purge": bool(purge), "boot_id": boot}


def due(rec, agora, boot):
    """(True, "") when the trial may end now; else (False, why not).

    A timer can fire a little early, so a few seconds of slack; more than that is
    someone running it by hand before the end, and that is refused. For "until
    reboot", the boot has to be a different one from the install's: the unit that
    does it is wanted by the same target the install ran under.
    """
    if rec["mode"] == "time":
        falta = rec["expires"] - agora
        return (True, "") if falta <= SLACK else (False, f"{int(falta)} s remain")
    if boot is None:
        return False, "this boot's id cannot be read, so a reboot cannot be told from this boot"
    if rec.get("boot_id") and boot == rec["boot_id"]:
        return False, "still the boot that installed it"
    return True, ""


def remaining(rec, agora):
    """Seconds left, or None for "until reboot"."""
    return None if rec["mode"] != "time" else max(0, rec["expires"] - int(agora))


def humanize(segundos):
    if segundos is None:
        return "until reboot"
    if segundos < 3600:
        return f"{max(1, round(segundos / 60))} min"
    if segundos < 2 * 86400:
        h, m = divmod(round(segundos / 60), 60)
        return f"{h} h {m:02d} min" if m else f"{h} h"
    return f"{round(segundos / 86400)} d"


# -- the systemd units -----------------------------------------------------------------

def unit_names(app):
    if not APP.match(app):
        raise ValueError(f"{app!r} is not a service name")
    return f"qh-trial-{app}.service", f"qh-trial-{app}.timer"


def _q(valor):
    """One word of an ExecStart= line, quoted the systemd way."""
    return '"' + str(valor).replace("\\", "\\\\").replace('"', '\\"').replace("%", "%%").replace("$", "$$") + '"'


def render_service(app, python, script, modo):
    texto = ["[Unit]", f"Description=qh: end the trial of {app}", "",
             "[Service]", "Type=oneshot", f"ExecStart={_q(python)} {_q(script)} {_q(app)} --trial-expire"]
    if modo == "reboot":
        # Enabled, not started: it runs the next time the user's systemd comes up.
        texto += ["", "[Install]", "WantedBy=default.target"]
    return "\n".join(texto) + "\n"


def render_timer(app, expira):
    return "\n".join(["[Unit]", f"Description=qh: end the trial of {app} at {calendar(expira)}", "",
                      "[Timer]", f"OnCalendar={calendar(expira)}", "Persistent=true", "AccuracySec=1min", "",
                      "[Install]", "WantedBy=timers.target"]) + "\n"


# -- files ----------------------------------------------------------------------------

def records_dir(home):
    return Path(home) / ".config/quadlet-homelab/trials"


def units_dir(home):
    return Path(home) / ".config/systemd/user"


def read(home, app):
    f = records_dir(home) / f"{app}.json"
    try:
        return json.loads(f.read_text())
    except (OSError, ValueError):
        return None


def read_all(home):
    d = records_dir(home)
    saida = {}
    for f in sorted(d.glob("*.json")) if d.is_dir() else []:
        try:
            saida[f.stem] = json.loads(f.read_text())
        except (OSError, ValueError):
            continue
    return saida


def _write(path, texto, modo=0o644):
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_name(path.name + ".tmp")
    fd = os.open(tmp, os.O_WRONLY | os.O_CREAT | os.O_TRUNC, modo)
    with os.fdopen(fd, "w") as fh:
        fh.write(texto)
    tmp.replace(path)


def write_all(home, rec, python, script):
    """The record and its units. The record is private: it says what will be deleted."""
    servico, timer = unit_names(rec["app"])
    _write(records_dir(home) / f"{rec['app']}.json", json.dumps(rec, indent=1) + "\n", 0o600)
    _write(units_dir(home) / servico, render_service(rec["app"], python, script, rec["mode"]))
    if rec["mode"] == "time":
        _write(units_dir(home) / timer, render_timer(rec["app"], rec["expires"]))


def remove_all(home, app):
    """Record and units. Missing ones are not an error: expiring twice must be harmless."""
    servico, timer = unit_names(app)
    for f in (records_dir(home) / f"{app}.json", units_dir(home) / servico, units_dir(home) / timer):
        try:
            f.unlink()
        except FileNotFoundError:
            pass


# -- self-test ---------------------------------------------------------------------------

def selftest():
    import shutil
    import subprocess

    # durations
    assert parse_duration("6h") == ("time", 6 * 3600) and parse_duration(" 2D ") == ("time", 2 * 86400)
    assert parse_duration("30m") == ("time", 1800) and parse_duration("1w") == ("time", 7 * 86400)
    assert parse_duration("reboot") == ("reboot", None) and parse_duration("REBOOT") == ("reboot", None)
    for ruim in ("", "6", "h", "6x", "-1h", "1.5h", "9m", "31d", "0h", "6 hours", None):
        try:
            parse_duration(ruim)
        except ValueError:
            continue
        raise AssertionError(f"{ruim!r} should be refused")

    # the instant: absolute, UTC, and what systemd itself accepts
    assert calendar(0) == "1970-01-01 00:00:00 UTC" and calendar(1_800_000_000) == "2027-01-15 08:00:00 UTC"
    if shutil.which("systemd-analyze"):
        r = subprocess.run(["systemd-analyze", "calendar", calendar(1_800_000_000)], capture_output=True, text=True)
        assert r.returncode == 0 and "2027" in r.stdout, r.stderr

    # when a trial may end
    t = new_record("memos", "time", 10_000, False, 4_000)
    assert due(t, 9_000, "b") == (False, "1000 s remain") and due(t, 9_980, "b")[0], "within the slack counts"
    assert due(t, 10_000, "b")[0] and due(t, 99_999, "b")[0]
    assert remaining(t, 4_000) == 6_000 and remaining(t, 99_999) == 0
    r = new_record("memos", "reboot", None, False, 4_000, boot="boot-A")
    assert due(r, 5_000, "boot-A") == (False, "still the boot that installed it"), "not in the boot that installed it"
    assert due(r, 5_000, "boot-B") == (True, "") and remaining(r, 5_000) is None
    assert due(r, 5_000, None)[0] is False, "an unreadable boot id is not a reboot"
    assert due(new_record("m", "reboot", None, False, 1, boot=None), 2, "boot-B")[0], "no recorded id: any boot is another one"

    assert humanize(None) == "until reboot" and humanize(120) == "2 min" and humanize(3 * 3600) == "3 h"
    assert humanize(5 * 3600 + 20 * 60) == "5 h 20 min" and humanize(3 * 86400) == "3 d" and humanize(5) == "1 min"

    # the unit names refuse anything that is not a service name
    assert unit_names("memos") == ("qh-trial-memos.service", "qh-trial-memos.timer")
    for ruim in ("../x", "A", "a b", "", "-a"):
        try:
            unit_names(ruim)
        except ValueError:
            continue
        raise AssertionError(ruim)

    # what is written
    srv = render_service("memos", "/usr/bin/python3", "/home/u/my repo/install.py", "time")
    assert 'ExecStart="/usr/bin/python3" "/home/u/my repo/install.py" "memos" --trial-expire' in srv
    assert "[Install]" not in srv and "Type=oneshot" in srv, "a timed trial is started by its timer, not wanted by a target"
    assert "WantedBy=default.target" in render_service("memos", "/p", "/s", "reboot")
    assert '"/a%%b$$c"' in render_service("x", "/p", "/a%b$c", "time"), "% and $ are escaped for systemd"
    tm = render_timer("memos", 1_800_000_000)
    assert "OnCalendar=2027-01-15 08:00:00 UTC" in tm and "Persistent=true" in tm and "WantedBy=timers.target" in tm
    assert "OnActiveSec" not in tm, "a relative timer would start over at every boot"

    with tempfile.TemporaryDirectory() as d:
        rec = new_record("memos", "time", 1_800_000_000, True, 1_799_000_000)
        write_all(d, rec, sys.executable, str(Path(__file__).resolve()))
        assert read(d, "memos") == rec and read_all(d) == {"memos": rec} and read(d, "outro") is None
        assert oct((records_dir(d) / "memos.json").stat().st_mode)[-3:] == "600", "the record says what will be deleted"
        assert (units_dir(d) / "qh-trial-memos.timer").is_file() and (units_dir(d) / "qh-trial-memos.service").is_file()
        assert not list(Path(d).rglob("*.tmp")), "no partial file is left behind"
        # the host's own verifier, when it exists and can run without a session
        if shutil.which("systemd-analyze"):
            r = subprocess.run(["systemd-analyze", "verify", str(units_dir(d) / "qh-trial-memos.service"),
                                str(units_dir(d) / "qh-trial-memos.timer")], capture_output=True, text=True)
            assert "OnCalendar" not in r.stderr and "Unknown" not in r.stderr, r.stderr
        remove_all(d, "memos")
        remove_all(d, "memos")          # twice, harmlessly
        assert read(d, "memos") is None and not list(units_dir(d).glob("qh-trial-*"))
        write_all(d, new_record("memos", "reboot", None, False, 1, "b"), sys.executable, __file__)
        assert (units_dir(d) / "qh-trial-memos.service").is_file() and not (units_dir(d) / "qh-trial-memos.timer").exists(), "reboot: a service, no timer"
    print("trials selftest: ok")


if __name__ == "__main__":
    if "--selftest" in sys.argv:
        selftest()
    else:
        print(__doc__)
