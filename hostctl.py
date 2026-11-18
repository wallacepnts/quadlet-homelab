#!/usr/bin/env python3
"""The host, as the store acts on it: what each app's data takes on disk, and restarting or shutting down on a schedule.

Both are small and both touch the machine, so every call that does goes through a `run` the tests replace.

- `usage`: bytes per directory. `podman unshare du` when podman is there, because the files a container wrote belong
  to a subuid and a plain `du` cannot read into them (it reports a part and complains). Without podman, plain `du`.
- `power_*`: a transient systemd user timer, `qh-power.timer`, that runs `systemctl reboot` or `poweroff` when it
  elapses. One at a time, cancellable, and the state is a small file beside the other store settings so the panel can
  say what is scheduled without parsing systemd's output. The same polkit rule that lets the logged-in user restart
  now lets the timer do it later.

    python3 hostctl.py --selftest
"""

import json
import re
import shutil
import subprocess
import sys
import tempfile
import time
from pathlib import Path

UNIT = "qh-power"
VERBS = ("reboot", "poweroff")
MIN_DELAY, MAX_DELAY = 60, 7 * 24 * 3600        # a minute to a week: sooner is a mistake, later is forgotten


def _run(cmd, **kw):
    return subprocess.run(cmd, capture_output=True, text=True, timeout=kw.pop("timeout", 30), check=False, **kw)


# -- disk usage ------------------------------------------------------------------------------

def dir_bytes(path, run=_run, unshare=None):
    """The apparent size of `path` in bytes (0 when it is not there), counting what a container wrote."""
    if not Path(path).exists():
        return 0
    usar = shutil.which("podman") is not None if unshare is None else unshare
    cmd = (["podman", "unshare"] if usar else []) + ["du", "-sb", "--one-file-system", str(path)]
    r = run(cmd, timeout=300)
    m = re.match(r"(\d+)\s", r.stdout or "")
    return int(m.group(1)) if m else 0       # a partial answer (rc 1, some directories unreadable) still counts


def usage(roots_by_app, run=_run, unshare=None):
    """[{"app", "bytes"}] largest first: each app's volume directories added up. `roots_by_app` is {app: [paths]}."""
    saida = [{"app": app, "bytes": sum(dir_bytes(p, run, unshare) for p in roots)} for app, roots in roots_by_app.items()]
    return sorted(saida, key=lambda x: (-x["bytes"], x["app"]))


# -- scheduled restart / shutdown ------------------------------------------------------------

def state_file(base):
    return Path(base) / ".config/quadlet-homelab/power.json"


def _seconds_until(hhmm, now):
    """Seconds from `now` (epoch) to the next local HH:MM, today or tomorrow."""
    m = re.fullmatch(r"([01]?\d|2[0-3]):([0-5]\d)", hhmm or "")
    if not m:
        raise ValueError("time")
    t = time.localtime(now)
    alvo = time.mktime((t.tm_year, t.tm_mon, t.tm_mday, int(m.group(1)), int(m.group(2)), 0, 0, 0, -1))
    if alvo <= now + MIN_DELAY:
        alvo += 24 * 3600
    return int(alvo - now)


def delay_of(minutes=None, at=None, now=None):
    """Seconds to wait for `minutes` from now, or for the next HH:MM; ValueError when out of range."""
    now = time.time() if now is None else now
    if at:
        seg = _seconds_until(at, now)
    elif isinstance(minutes, int) and not isinstance(minutes, bool):
        seg = minutes * 60
    else:
        raise ValueError("when")
    if not MIN_DELAY <= seg <= MAX_DELAY:
        raise ValueError("range")
    return seg


def schedule(base, verb, seconds, run=_run, now=None):
    """Arm the timer, replacing one already armed. Returns the state written, or None when systemd refused."""
    if verb not in VERBS:
        raise ValueError("verb")
    now = time.time() if now is None else now
    cancel(base, run)
    r = run(["systemd-run", "--user", f"--unit={UNIT}", f"--on-active={seconds}s",
             f"--description=qh scheduled {verb}", "systemctl", verb])
    if r.returncode != 0:
        return None
    estado = {"action": verb, "at": int(now + seconds)}
    f = state_file(base)
    f.parent.mkdir(parents=True, exist_ok=True)
    f.write_text(json.dumps(estado) + "\n")
    return estado


def cancel(base, run=_run):
    run(["systemctl", "--user", "stop", f"{UNIT}.timer", f"{UNIT}.service"])
    state_file(base).unlink(missing_ok=True)


def state(base, run=_run, now=None):
    """{"action", "at"} while the timer is armed, else None (a file left by a timer that already fired is dropped)."""
    f = state_file(base)
    try:
        d = json.loads(f.read_text())
    except (OSError, ValueError):
        return None
    now = time.time() if now is None else now
    ativo = run(["systemctl", "--user", "is-active", f"{UNIT}.timer"]).stdout.strip() == "active"
    if d.get("action") in VERBS and isinstance(d.get("at"), int) and ativo and d["at"] > now - 5:
        return d
    f.unlink(missing_ok=True)
    return None


# -- selftest -----------------------------------------------------------------------------------

def selftest():
    class R:
        def __init__(self, out="", rc=0):
            self.stdout, self.returncode = out, rc

    with tempfile.TemporaryDirectory() as tmp:
        # usage: the number is the first field; a partial answer (rc 1) counts; a missing path is 0
        d = Path(tmp, "v"); d.mkdir()
        chamadas = []
        def du(cmd, **kw):
            chamadas.append(cmd)
            return R(f"1234\t{cmd[-1]}\n", 1)
        assert dir_bytes(d, du, unshare=True) == 1234 and chamadas[-1][:3] == ["podman", "unshare", "du"], chamadas
        assert dir_bytes(d, du, unshare=False) == 1234 and chamadas[-1][0] == "du"
        assert dir_bytes(Path(tmp, "nope"), du) == 0
        assert dir_bytes(d, lambda c, **k: R("", 1), unshare=False) == 0
        u = usage({"a": [d], "b": [d, d], "c": []}, du, unshare=False)
        assert [(x["app"], x["bytes"]) for x in u] == [("b", 2468), ("a", 1234), ("c", 0)], u

        # delays: minutes, or the next HH:MM; out of range or malformed is refused
        agora = time.mktime((2026, 11, 18, 10, 0, 0, 0, 0, -1))
        assert delay_of(minutes=15, now=agora) == 900
        assert delay_of(at="10:30", now=agora) == 1800
        assert delay_of(at="09:00", now=agora) == 23 * 3600, "an hour already past means tomorrow"
        assert delay_of(at="10:00", now=agora) == 24 * 3600, "now is too soon: tomorrow"
        for ruim in ({"minutes": 0}, {"minutes": 10 ** 6}, {"at": "25:00"}, {"at": "9"}, {"minutes": "5"}, {"minutes": True}, {}):
            try:
                delay_of(now=agora, **ruim)
            except ValueError:
                continue
            raise AssertionError(ruim)

        # schedule / state / cancel, with a systemd that answers
        ativo = {"v": False}
        log = []
        def systemd(cmd, **kw):
            log.append(cmd)
            if cmd[0] == "systemd-run":
                ativo["v"] = True
                return R()
            if cmd[:3] == ["systemctl", "--user", "stop"]:
                ativo["v"] = False
                return R()
            if cmd[:3] == ["systemctl", "--user", "is-active"]:
                return R("active\n" if ativo["v"] else "inactive\n", 0 if ativo["v"] else 3)
            return R()
        assert state(tmp, systemd, now=agora) is None
        e = schedule(tmp, "reboot", 900, systemd, now=agora)
        assert e == {"action": "reboot", "at": int(agora) + 900}
        run_cmd = next(c for c in log if c[0] == "systemd-run")
        assert run_cmd[-2:] == ["systemctl", "reboot"] and "--on-active=900s" in run_cmd and "--user" in run_cmd, run_cmd
        assert state(tmp, systemd, now=agora) == e
        e2 = schedule(tmp, "poweroff", 3600, systemd, now=agora)
        assert state(tmp, systemd, now=agora) == e2, "a second schedule replaces the first"
        ativo["v"] = False
        assert state(tmp, systemd, now=agora) is None and not state_file(tmp).exists(), "the timer is gone: the file goes too"
        schedule(tmp, "reboot", 900, systemd, now=agora)
        cancel(tmp, systemd)
        assert state(tmp, systemd, now=agora) is None
        assert schedule(tmp, "reboot", 900, lambda c, **k: R("", 1)) is None and not state_file(tmp).exists(), "refused: nothing kept"
        try:
            schedule(tmp, "halt", 900, systemd)
            raise AssertionError("an unknown verb")
        except ValueError:
            pass
    print("hostctl selftest: ok")


if __name__ == "__main__":
    if "--selftest" in sys.argv:
        selftest()
    else:
        print(__doc__)
