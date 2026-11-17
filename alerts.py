#!/usr/bin/env python3
"""Alerts: the store tells an ntfy topic when something is wrong. Opt-in, and never the same thing twice in a row.

What is watched (each can be turned off): a unit that failed, a container that is unhealthy, a unit that
restarts in a loop, a backup that failed, a new upstream release, a disk past a percentage.

The same alert is not repeated within `cooldown_hours`; a new release is told once per version. The settings
live in `~/.config/quadlet-homelab/alerts.json` (mode 600: it may hold an ntfy token), what was sent and when in
`~/.cache/quadlet-homelab/alerts-state.json`.

This module is the logic and the sending; `store.py` runs the check on a timer and shows the settings.

    python3 alerts.py --selftest
"""

import json
import os
import re
import shutil
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path

KINDS = ("failed", "unhealthy", "restart_loop", "backup", "update", "disk")
DEFAULTS = {"enabled": False, "server": "", "topic": "", "token": "", "cooldown_hours": 6, "disk_percent": 90,
            "kinds": {k: True for k in KINDS}}
LOOP_RESTARTS, LOOP_WINDOW = 3, 3600       # restarted 3 times, the last less than an hour ago
TAGS = {"failed": ("rotating_light", 4), "unhealthy": ("warning", 4), "restart_loop": ("repeat", 4),
        "backup": ("floppy_disk", 4), "update": ("arrow_up", 2), "disk": ("package", 4), "test": ("bell", 3)}


def config_file(home=None):
    return Path(home or Path.home()) / ".config/quadlet-homelab/alerts.json"


def state_file(home=None):
    return Path(home or Path.home()) / ".cache/quadlet-homelab/alerts-state.json"


def clean(data):
    """(config, errors) from whatever the form sent, filling what is missing from the defaults."""
    cfg, erros = json.loads(json.dumps(DEFAULTS)), []
    data = data or {}
    cfg["enabled"] = bool(data.get("enabled", cfg["enabled"]))
    server = str(data.get("server", cfg["server"])).strip().rstrip("/")
    if server and not re.fullmatch(r"https?://[A-Za-z0-9.\-]+(:\d+)?(/[A-Za-z0-9._~/\-]*)?", server):
        erros.append("server must be an http(s) address, like https://ntfy.example.org")
    topic = str(data.get("topic", cfg["topic"])).strip()
    if topic and not re.fullmatch(r"[A-Za-z0-9_\-]{1,64}", topic):
        erros.append("topic is letters, digits, _ and -, up to 64")
    token = str(data.get("token", cfg["token"])).strip()
    if token and not re.fullmatch(r"[A-Za-z0-9_\-.]{1,200}", token):
        erros.append("token has characters a token does not")
    for chave, lo, hi in (("cooldown_hours", 1, 168), ("disk_percent", 50, 99)):
        try:
            v = int(data.get(chave, cfg[chave]))
        except (TypeError, ValueError):
            v = -1
        if not lo <= v <= hi:
            erros.append(f"{chave} is a number from {lo} to {hi}")
        else:
            cfg[chave] = v
    sel = data.get("kinds") if isinstance(data.get("kinds"), dict) else {}
    cfg["kinds"] = {k: bool(sel.get(k, True)) for k in KINDS}
    cfg.update(server=server, topic=topic, token=token)
    if cfg["enabled"] and not (server and topic):
        erros.append("turning alerts on needs the server and the topic")
    return cfg, erros


def load(home=None):
    try:
        return clean(json.loads(config_file(home).read_text()))[0]
    except (OSError, ValueError):
        return json.loads(json.dumps(DEFAULTS))


def save(cfg, home=None):
    f = config_file(home)
    f.parent.mkdir(parents=True, exist_ok=True)
    f.write_text(json.dumps(cfg, indent=2) + "\n")
    f.chmod(0o600)


def public(cfg):
    """The config for the page: the token never leaves, only whether there is one."""
    return {**{k: v for k, v in cfg.items() if k != "token"}, "has_token": bool(cfg.get("token"))}


def disk_percent(path):
    try:
        u = shutil.disk_usage(path)
    except OSError:
        return None
    return round(100 * u.used / u.total) if u.total else None


def events(apps, rows, disk_pct, cfg, now=None):
    """[{key, kind, title, message}] of what is wrong right now, from the catalog's apps, the update rows and the disk."""
    now = now or time.time()
    on, saida = cfg["kinds"], []

    def add(kind, key, title, message):
        if on.get(kind):
            saida.append({"key": key, "kind": kind, "title": title, "message": message})
    for a in apps:
        for u in a.get("units", []):
            if not u.get("installed") or u.get("stopped"):
                continue
            nome, f = u["unit"], u.get("failure") or {}
            if f.get("state") == "failed" or f.get("result") not in (None, "", "success") and f.get("state") != "active":
                add("failed", f"failed:{nome}", f"{a['name']} failed",
                    f"Unit {nome} is {f.get('state') or 'failed'} (exit {f.get('exit')}, {f.get('result')}).")
            elif f.get("sub") == "auto-restart" or (f.get("restarts", 0) >= LOOP_RESTARTS and f.get("last")
                                                    and now - f["last"] < LOOP_WINDOW):
                add("restart_loop", f"restart_loop:{nome}", f"{a['name']} keeps restarting",
                    f"Unit {nome} restarted {f.get('restarts')} times.")
            if u.get("container") == "unhealthy":
                add("unhealthy", f"unhealthy:{nome}", f"{a['name']} is unhealthy", f"The healthcheck of {nome} is failing.")
    for r in rows or []:
        if r.get("bucket") == "BEHIND":
            add("update", f"update:{r['unit']}:{r.get('there')}", f"New version of {r['app']}",
                f"{r['unit']}: {r.get('here')} -> {r.get('there')}")
    if disk_pct is not None and disk_pct >= cfg["disk_percent"]:
        add("disk", "disk", "Disk almost full", f"The disk is at {disk_pct}% (limit {cfg['disk_percent']}%).")
    return saida


def due(evs, state, cfg, now=None):
    """(events to send, new state): the same key is not sent again within the cooldown.

    A new release is told once per version (its key carries the version), so it never repeats. The state
    forgets keys older than a week."""
    now = now or time.time()
    espera = cfg["cooldown_hours"] * 3600
    enviar = [e for e in evs if e["kind"] == "update" and e["key"] not in state
              or e["kind"] != "update" and now - state.get(e["key"], 0) >= espera]
    novo = {k: v for k, v in state.items() if now - v < 7 * 86400}
    novo.update({e["key"]: now for e in enviar})
    return enviar, novo


def push(cfg, ev, opener=urllib.request.urlopen):
    """Sends one alert to the ntfy topic. Returns None on success, else the error text."""
    tag, prio = TAGS.get(ev["kind"], ("bell", 3))
    cab = {"Title": ev["title"].encode("ascii", "replace").decode(), "Priority": str(prio), "Tags": tag,
           "User-Agent": "quadlet-homelab-alerts"}
    if cfg.get("token"):
        cab["Authorization"] = f"Bearer {cfg['token']}"
    req = urllib.request.Request(f"{cfg['server']}/{cfg['topic']}", data=ev["message"].encode(), headers=cab, method="POST")
    try:
        with opener(req, timeout=15) as r:
            return None if 200 <= r.status < 300 else f"HTTP {r.status}"
    except urllib.error.HTTPError as e:
        return f"HTTP {e.code}"
    except (urllib.error.URLError, OSError) as e:
        return str(getattr(e, "reason", e))


def run(apps, rows, home, cfg=None, sender=push, now=None, disk_path=None, extra=()):
    """One check: what is wrong, what is due, sending it. Returns the list of {key, error} that went out."""
    cfg = cfg or load(home)
    if not cfg["enabled"] or not (cfg["server"] and cfg["topic"]):
        return []
    sf = state_file(home)
    try:
        estado = json.loads(sf.read_text())
    except (OSError, ValueError):
        estado = {}
    evs = events(apps, rows, disk_percent(disk_path or home or Path.home()), cfg, now) + [
        e for e in extra if cfg["kinds"].get(e["kind"])]
    enviar, novo = due(evs, estado, cfg, now)
    enviados = []
    for e in enviar:
        erro = sender(cfg, e)
        if erro:
            novo.pop(e["key"], None)          # not delivered: tried again next time
        enviados.append({"key": e["key"], "error": erro})
    sf.parent.mkdir(parents=True, exist_ok=True)
    sf.write_text(json.dumps(novo))
    return enviados


def selftest():
    import tempfile
    cfg, err = clean({"enabled": True, "server": "https://ntfy.example.org/", "topic": "lab", "cooldown_hours": 2})
    assert not err and cfg["server"] == "https://ntfy.example.org" and cfg["kinds"]["disk"], err
    assert clean({"enabled": True})[1], "on needs a server and a topic"
    assert clean({"server": "ftp://x"})[1] and clean({"topic": "a b"})[1] and clean({"disk_percent": 10})[1] and clean({"cooldown_hours": "x"})[1]
    assert "token" not in public({**cfg, "token": "tk_x"}) and public({**cfg, "token": "tk_x"})["has_token"]
    now = 1_000_000
    apps = [{"name": "Memos", "units": [
        {"unit": "memos", "installed": True, "failure": {"state": "failed", "result": "exit-code", "exit": 1}},
        {"unit": "ok", "installed": True, "container": "unhealthy"},
        {"unit": "loop", "installed": True, "failure": {"state": "activating", "sub": "auto-restart", "restarts": 5, "result": "success"}},
        {"unit": "old", "installed": True, "failure": {"state": "active", "restarts": 4, "result": "success", "last": now - 86400}},
        {"unit": "off", "installed": True, "stopped": True, "failure": {"state": "failed"}},
        {"unit": "none", "installed": False}]}]
    rows = [{"app": "memos", "unit": "memos", "bucket": "BEHIND", "here": "1", "there": "2"}, {"app": "x", "unit": "x", "bucket": "up to date"}]
    evs = events(apps, rows, 93, cfg, now)
    assert sorted(e["key"] for e in evs) == sorted(["failed:memos", "unhealthy:ok", "restart_loop:loop", "update:memos:2", "disk"]), evs
    sem = {**cfg, "kinds": {**cfg["kinds"], "update": False}}
    assert "update:memos:2" not in [e["key"] for e in events(apps, rows, 93, sem, now)], "a kind can be turned off"
    assert "disk" not in [e["key"] for e in events(apps, rows, 80, cfg, now)]
    est, s1 = due(evs, {}, cfg, now)
    assert len(est) == 5
    est2, s2 = due(evs, s1, cfg, now + 3600)
    assert est2 == [], "within the cooldown: nothing repeats"
    est3, s3 = due(evs, s2, cfg, now + 3 * 3600)
    assert sorted(e["kind"] for e in est3) == ["disk", "failed", "restart_loop", "unhealthy"], "an update is told once per version"
    assert due(evs, {"x": now - 8 * 86400}, cfg, now)[1].get("x") is None, "old keys are forgotten"
    with tempfile.TemporaryDirectory() as tmp:
        sent = []
        def ok(c, e):
            sent.append(e["key"])
        full = {**cfg, "enabled": True}
        r = run(apps, rows, tmp, full, ok, now, tmp)
        assert len(r) >= 4 and all(x["error"] is None for x in r), r
        n = len(sent)
        assert run(apps, rows, tmp, full, ok, now + 60, tmp) == [] and len(sent) == n, "the second check is quiet"
        sent.clear()
        run(apps, rows, tmp, full, lambda c, e: "boom", now + 10 * 86400, tmp)
        again = run(apps, rows, tmp, full, ok, now + 10 * 86400 + 60, tmp)
        assert again and sent, "what failed to send is tried again"
        assert run(apps, rows, tmp, {**cfg, "enabled": False}, ok, now, tmp) == []
        save(full, tmp)
        assert load(tmp)["topic"] == "lab" and oct(config_file(tmp).stat().st_mode)[-3:] == "600"
    class R:  # a fake response
        status = 200
        def __enter__(self): return self
        def __exit__(self, *a): pass
    visto = {}
    def op(req, timeout):
        visto.update(url=req.full_url, h=dict(req.header_items()), body=req.data)
        return R()
    assert push({**cfg, "token": "tk_1"}, {"kind": "failed", "title": "Memos fell", "message": "m"}, op) is None
    assert visto["url"] == "https://ntfy.example.org/lab" and visto["h"]["Authorization"] == "Bearer tk_1" and visto["body"] == b"m"
    print("alerts selftest: ok")


if __name__ == "__main__":
    if "--selftest" in sys.argv:
        selftest()
    else:
        print(__doc__)
