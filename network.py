#!/usr/bin/env python3
"""The tailnet as part of the project: Tailscale or Headscale beside tsdproxy, or none at all (local only).

One choice, kept in `~/.config/quadlet-homelab/network.json`:

    local       no tailnet. The apps are reached on the LAN port, tsdproxy is stopped.
    tailscale   the host runs Tailscale (a host package: it has to be the host on the network, rule 20) and
                tsdproxy gives each app a name on the tailnet.
    headscale   the same, but the control server is Headscale, which the project runs as an app: your own
                network, no account at a third party. The host's Tailscale client signs in to it (`--login-server`)
                and tsdproxy points its `controlUrl` at it.

This module is the logic: reading the state, and the steps of a switch. What touches the world goes through
`ctx` (commands, the engine's own helpers), so the selftest runs against fakes. `install.py` builds the real
`ctx` and runs the steps (`qh --network MODE`), the store shows the state and starts the same command.

    python3 network.py --selftest
"""

import json
import re
import shutil
import sys
from pathlib import Path

MODES = ("local", "tailscale", "headscale")
HEADSCALE_URL_PORT = 8093            # the port apps/headscale publishes
LABEL = re.compile(r"[a-z0-9]([a-z0-9-]{0,30}[a-z0-9])?")
TS_COMMANDS = {
    "install": ["sudo transactional-update pkg install tailscale   # then reboot (an immutable host)",
                "# or, on a mutable one: your package manager, then `sudo systemctl enable --now tailscaled`"],
    "service": ["sudo systemctl enable --now tailscaled"],
    "operator": ["sudo tailscale set --operator=$USER      # once: lets the store sign the host in, without root"],
}


def config_file(home):
    return Path(home) / ".config/quadlet-homelab/network.json"


def load(home):
    """{mode, server_url, tailnet}; `tailscale` is what a host that never chose has always done."""
    try:
        d = json.loads(config_file(home).read_text())
    except (OSError, ValueError):
        d = {}
    d = d if isinstance(d, dict) else {}
    return {"mode": d.get("mode") if d.get("mode") in MODES else "tailscale",
            "server_url": d.get("server_url") or "", "tailnet": d.get("tailnet") or "",
            "chosen": d.get("mode") in MODES}


def save(home, cfg):
    f = config_file(home)
    f.parent.mkdir(parents=True, exist_ok=True)
    f.write_text(json.dumps({k: cfg[k] for k in ("mode", "server_url", "tailnet") if k in cfg}, indent=2) + "\n")


def check(mode, server_url="", tailnet=""):
    """Errors in what the form sent, as a list."""
    erros = []
    if mode not in MODES:
        erros.append(f"mode is one of: {', '.join(MODES)}")
    if server_url and not re.fullmatch(r"https?://[A-Za-z0-9.\-]+(:\d+)?(/[A-Za-z0-9._~/\-]*)?", server_url):
        erros.append("server_url is an http(s) address, like http://192.168.1.10:8093")
    if tailnet and not LABEL.fullmatch(tailnet):
        erros.append("tailnet is a name of lowercase letters, digits and -, up to 32")
    if mode == "headscale" and not tailnet:
        erros.append("a Headscale network needs a name (the apps' names on it)")
    return erros


def tailscale_bin(env):
    return env.get("QH_TAILSCALE") or shutil.which("tailscale")


def tailscale_state(ctx):
    """{installed, active, backend, ip, domain, operator} of the host's Tailscale client."""
    saida = {"installed": False, "active": False, "backend": None, "ip": None, "domain": None, "operator": False}
    binario = ctx["tailscale_bin"]()
    if not binario:
        return saida
    saida["installed"] = True
    r = ctx["run_read"]([binario, "status", "--json"])
    try:
        d = json.loads(r)
    except (ValueError, TypeError):
        return saida                                 # tailscaled is not answering
    saida["active"] = True
    saida["backend"] = d.get("BackendState")
    ips = (d.get("Self") or {}).get("TailscaleIPs") or d.get("TailscaleIPs") or []
    saida["ip"] = next((i for i in ips if "." in i), None)
    saida["domain"] = (d.get("CurrentTailnet") or {}).get("MagicDNSSuffix") or None
    # `tailscale set --operator` is what lets the user (the store) run `tailscale up` without root; it is
    # recorded in the prefs, and `tailscale debug prefs` shows it
    prefs = ctx["run_read"]([binario, "debug", "prefs"])
    saida["operator"] = bool(re.search(r'"OperatorUser":\s*"[^"]+"', prefs or ""))
    return saida


def state(ctx):
    """Everything the Network screen shows."""
    home, cfg = ctx["home"], load(ctx["home"])
    ts = tailscale_state(ctx)
    return {"mode": cfg["mode"], "chosen": cfg["chosen"], "server_url": cfg["server_url"] or ctx["default_server_url"](),
            "tailnet": cfg["tailnet"] or (ts["domain"] or "").removesuffix(".ts.net"),
            "tailscale": ts,
            "headscale": {"installed": ctx["app_installed"]("headscale"), "active": ctx["unit_active"]("headscale")},
            "tsdproxy": {"installed": ctx["app_installed"]("tsdproxy"), "active": ctx["unit_active"]("tsdproxy"),
                         "authkey": ctx["secret_exists"]("authkey")},
            "access": ctx["saved_access"](), "commands": TS_COMMANDS}


def edit_yaml_value(text, path, value):
    """`text` with the scalar at the dotted `path` (two levels deep at most) set to `value`, keeping every
    other line as it was: the config files are the user's, and a YAML round trip would lose their comments."""
    chaves = path.split(".")
    linhas = text.split("\n")
    alvo, nivel, recuo = 0, 0, 0
    for i, l in enumerate(linhas):
        ind = len(l) - len(l.lstrip())
        if not l.strip() or l.lstrip().startswith("#"):
            continue
        if ind == recuo * 2 and re.match(rf"\s*{re.escape(chaves[nivel])}:", l):
            if nivel == len(chaves) - 1:
                linhas[i] = re.sub(r":.*$", f": {value}", l, count=1)
                return "\n".join(linhas)
            nivel, recuo = nivel + 1, recuo + 1
    return None


def plan(mode, opts, ctx):
    """([(description, callable)], [warning]) for switching to `mode`; the callables do the work.

    opts: server_url, tailnet. Nothing here runs anything: the steps run only on --apply."""
    home = ctx["home"]
    cfg0 = load(home)
    opts = {"server_url": opts.get("server_url") or cfg0["server_url"] or ctx["default_server_url"](),
            "tailnet": opts.get("tailnet") or cfg0["tailnet"]}
    steps, avisos = [], []
    erros = check(mode, opts["server_url"] if mode == "headscale" else "", opts["tailnet"])
    if erros:
        return [], erros
    ts = tailscale_state(ctx)
    novo = {"mode": mode, "server_url": opts["server_url"] if mode == "headscale" else cfg0["server_url"],
            "tailnet": opts["tailnet"] or cfg0["tailnet"]}
    steps.append((f"save the network choice: {mode}", lambda: save(home, novo)))

    if mode == "local":
        steps.append(("access rule: local (the LAN port, no tailnet name)", lambda: ctx["save_access"]("local")))
        for app in ctx["access_drift"]("local"):
            steps.append((f"update {app} to the new rule", lambda app=app: ctx["engine"]([app, "--update", "--apply"])))
        if ctx["unit_active"]("tsdproxy"):
            steps.append(("stop tsdproxy (not needed without a tailnet)", lambda: ctx["stop_unit"]("tsdproxy")))
        avisos.append("Headscale, if it runs, is left as it is, and so is the host's Tailscale: remove them by hand if you do not want them.")
        return steps, avisos

    # --- a tailnet: the host's client, tsdproxy, and for Headscale the server -------------------------
    if not ts["installed"]:
        avisos += ["Tailscale is not installed on this host. Install it (once), then run this again:"] + TS_COMMANDS["install"]
    elif not ts["active"]:
        avisos += ["tailscaled is not running:"] + TS_COMMANDS["service"]
    elif not ts["operator"]:
        avisos += ["Let the store sign the host in without root (once):"] + TS_COMMANDS["operator"]
    pronto = ts["installed"] and ts["active"]

    if mode == "headscale":
        url, nome = opts["server_url"], opts["tailnet"]
        if not ctx["app_installed"]("headscale"):
            steps.append(("install the Headscale server (the headscale app)", lambda: ctx["engine"](["headscale", "--apply"])))
        steps.append((f"Headscale: server_url {url}, base_domain {".".join((nome, "ts", "net"))}", lambda: ctx["headscale_config"](url, nome)))
        steps.append(("restart Headscale and wait until it answers", lambda: ctx["headscale_restart"]()))
        steps.append(("Headscale: a user and a reusable key for this host and tsdproxy", lambda: ctx["headscale_key"]()))
        if pronto:
            steps.append((f"sign this host in to {url}", lambda: ctx["ts_login"](url, ctx["key"]())))
        steps.append(("tsdproxy: the key as its secret, controlUrl pointing at Headscale, then restart",
                      lambda: ctx["tsdproxy_setup"](url, ctx["key"]())))
        steps.append(("labels: Headscale issues no HTTPS certificate, so tsdproxy serves plain HTTP on the tailnet", lambda: None))
        for app in ctx["tailnet_apps"]():
            steps.append((f"update {app} (its tsdproxy labels)", lambda app=app: ctx["engine"]([app, "--update", "--apply"])))
        avisos.append("Headscale cannot issue HTTPS certificates: the apps are served over HTTP on the tailnet (WireGuard still encrypts it). "
                      "Apps that insist on HTTPS — " + ", ".join(ctx["https_apps"]() or ["none installed"]) + " — need the Tailscale choice.")
    else:
        if pronto:
            if ts["backend"] != "Running":
                steps.append(("sign the host in to Tailscale (a link to open appears below)", lambda: ctx["ts_login"]("", ctx["key"]())))
        steps.append(("tsdproxy: controlUrl on Tailscale's own control plane", lambda: ctx["tsdproxy_control"]("https://controlplane.tailscale.com")))
        if not ctx["app_installed"]("tsdproxy"):
            avisos.append("tsdproxy is not installed: install it from the store (it asks for a reusable Tailscale auth key).")
        elif ctx["unit_active"]("tsdproxy") is False:
            steps.append(("start tsdproxy", lambda: ctx["start_unit"]("tsdproxy")))

    steps.append(("TAILNET for the units (environment.d)", lambda: ctx["write_tailnet"](novo["tailnet"] or ctx["tailnet_from_host"]())))
    if not ctx["saved_access"]() or ctx["saved_access"]() == "local":
        steps.append(("access rule: tailnet (apps get their names)", lambda: ctx["save_access"]("tailnet")))
    return steps, avisos


def selftest():
    import tempfile
    DOM = ".".join(("casa", "ts", "net"))
    assert check("headscale", "http://192.168.1.10:8093", "casa") == []
    assert check("headscale", "ftp://x", "casa") and check("headscale", "http://x", "Casa Nova") and check("headscale", "http://x", "")
    assert check("nope") and check("tailscale") == [] and check("local") == []
    assert edit_yaml_value("a:\n  b: 1\n  # c: 2\nd: 3\n", "a.b", "9") == "a:\n  b: 9\n  # c: 2\nd: 3\n"
    t = "tailscale:\n  providers:\n    default:\n      authKey: \"\"\n      controlUrl: https://x\n  dataDir: /data/\n"
    assert "controlUrl: http://hs:8093" in edit_yaml_value(t, "tailscale.providers.default.controlUrl", "http://hs:8093")
    assert edit_yaml_value("server_url: http://a\n", "server_url", "http://b") == "server_url: http://b\n"
    assert edit_yaml_value("a: 1\n", "x.y", "2") is None
    chamadas = []
    with tempfile.TemporaryDirectory() as tmp:
        status = json.dumps({"BackendState": "Running", "Self": {"TailscaleIPs": ["100.64.0.1", "fd7a::1"]},
                             "CurrentTailnet": {"MagicDNSSuffix": DOM}})
        ctx = {"home": tmp, "tailscale_bin": lambda: "/bin/tailscale",
               "run_read": lambda cmd: status if cmd[1] == "status" else '{"OperatorUser": "w"}',
               "default_server_url": lambda: "http://192.168.1.10:8093", "app_installed": lambda a: a == "tsdproxy",
               "unit_active": lambda u: u == "tsdproxy", "secret_exists": lambda n: True, "saved_access": lambda: "tailnet",
               "save_access": lambda m: chamadas.append(("access", m)), "access_drift": lambda m: ["memos"],
               "engine": lambda a: chamadas.append(("qh", a)), "stop_unit": lambda u: chamadas.append(("stop", u)),
               "start_unit": lambda u: chamadas.append(("start", u)), "tailnet_apps": lambda: ["memos"], "https_apps": lambda: ["vaultwarden"],
               "headscale_config": lambda u, n: chamadas.append(("hs-config", u, n)), "headscale_restart": lambda: chamadas.append("hs-restart"),
               "headscale_key": lambda: chamadas.append("hs-key"), "key": lambda: "KEY", "ts_login": lambda u, k: chamadas.append(("login", u, k)),
               "tsdproxy_setup": lambda u, k: chamadas.append(("tsd", u, k)), "tsdproxy_control": lambda u: chamadas.append(("control", u)),
               "write_tailnet": lambda n: chamadas.append(("tailnet", n)), "tailnet_from_host": lambda: "fromhost"}
        s = state(ctx)
        assert s["tailscale"] == {"installed": True, "active": True, "backend": "Running", "ip": "100.64.0.1", "domain": DOM, "operator": True}, s["tailscale"]
        assert s["tailnet"] == "casa" and s["tsdproxy"] == {"installed": True, "active": True, "authkey": True} and s["mode"] == "tailscale" and not s["chosen"]
        # local: the rule, the services that drift, tsdproxy stopped; nothing else is touched
        steps, av = plan("local", {}, ctx)
        for _, fn in steps:
            fn()
        assert chamadas == [("access", "local"), ("qh", ["memos", "--update", "--apply"]), ("stop", "tsdproxy")], chamadas
        assert load(tmp)["mode"] == "local" and load(tmp)["chosen"]
        # headscale: server, config, key, host login, tsdproxy, apps — in that order, with the HTTP/HTTPS warning
        chamadas.clear()
        steps, av = plan("headscale", {"tailnet": "casa"}, ctx)
        assert [d.split(":")[0].split(" (")[0] for d, _ in steps][:3] == ["save the network choice", "install the Headscale server", "Headscale"], [d for d, _ in steps]
        for _, fn in steps:
            fn()
        ordem = [c if isinstance(c, str) else c[0] for c in chamadas]
        assert ordem == ["qh", "hs-config", "hs-restart", "hs-key", "login", "tsd", "qh", "tailnet"], ordem
        assert ("login", "http://192.168.1.10:8093", "KEY") in chamadas and ("tailnet", "casa") in chamadas
        assert any("vaultwarden" in a and "HTTPS" in a for a in av), av
        assert load(tmp) == {"mode": "headscale", "server_url": "http://192.168.1.10:8093", "tailnet": "casa", "chosen": True}
        # tailscale on a host that is not ready: it says what to run, and does the part that does not need it
        ctx["tailscale_bin"] = lambda: None
        steps, av = plan("tailscale", {"tailnet": "casa"}, ctx)
        assert any("transactional-update" in a for a in av) and not any(d.startswith("sign the host in") for d, _ in steps)
        save(tmp, {"mode": "tailscale", "server_url": "", "tailnet": ""})
        assert plan("headscale", {"server_url": "http://x:1"}, ctx)[0] == [], "a Headscale network needs a name"
    print("network selftest: ok")


if __name__ == "__main__":
    selftest() if "--selftest" in sys.argv else print(__doc__)
