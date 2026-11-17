#!/usr/bin/env python3
"""Instances: the same app installed more than once (`qh memos --instance casa` is `memos-casa`).

An instance is a derived copy of the app's folder, written beside it as `apps/<app>-<name>/` (git ignores it,
and `check.py` skips it: the `.instance` marker). Everything the app owns gets the suffix: its units, container
and network names, secrets, volume and `.env` paths and the tsdproxy name; what is shared (`tsdproxy-net`, other
apps' volumes, the image) is left alone. A published host port moves to the next free one. Because the copy is a
plain app folder, install, update, backup, remove and the store treat it like any other app.

The record of what exists is `~/.config/quadlet-homelab/instances.json`; the folder is rebuilt from the base app
on every run, so a change to the app reaches its instances.

    python3 instances.py --selftest
"""

import json
import re
import shutil
import socket
import sys
from pathlib import Path

MARKER = ".instance"
NAME = re.compile(r"[a-z0-9]+(-[a-z0-9]+)*")
PORT = re.compile(r"^(?:([^:]+):)?(\d+):(\d+)(/\w+)?$")
SKIP_FILES = {"app.json", MARKER, ".gitignore"}


def is_instance(folder):
    return (Path(folder) / MARKER).is_file()


def file_of(home):
    return Path(home) / ".config/quadlet-homelab/instances.json"


def load(home):
    try:
        d = json.loads(file_of(home).read_text())
        return d if isinstance(d, dict) else {}
    except (OSError, ValueError):
        return {}


def save(home, registro):
    f = file_of(home)
    f.parent.mkdir(parents=True, exist_ok=True)
    f.write_text(json.dumps(registro, indent=2, sort_keys=True) + "\n")


def name_problem(app, inst, existing_dirs):
    """Why `inst` cannot be an instance name of `app`, or None."""
    if not NAME.fullmatch(inst or "") or len(inst) > 20:
        return "an instance name is lowercase letters, digits and -, up to 20"
    if f"{app}-{inst}" in existing_dirs:
        return f"{app}-{inst} already exists"
    return None


def directive_values(text, key):
    return [l.split("=", 1)[1].strip() for l in text.splitlines() if l.startswith(key + "=")]


def identifiers(folder, units_text):
    """What the app owns, by name: its folder, unit basenames, container/network names, secrets and tsdproxy name."""
    ids = {Path(folder).name}
    for f in Path(folder).iterdir():
        if f.suffix in (".container", ".network"):
            ids.add(f.stem)
    for t in units_text:
        ids.update(directive_values(t, "ContainerName"))
        ids.update(directive_values(t, "NetworkName"))
        ids.update(v.split(",")[0] for v in directive_values(t, "Secret"))
        ids.update(v.split("=", 1)[1] for v in directive_values(t, "Label") if v.startswith("tsdproxy.name="))
    # a name no unit text uses elsewhere is still fine; an id that is a plain word shared with other things is not
    return {i for i in ids if i and re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9._-]*", i)}


def rename(text, ids, suffix, keep=("Image=", "NetworkAlias=")):
    """`text` with every owned name given the suffix, except on lines that name something else (the image).

    A name inside a container path (`/var/opt/memos`) is the app's own business and stays; the host side of a
    `Volume=` and an `EnvironmentFile=` are paths of ours, so there it is renamed."""
    if not ids:
        return text
    alt = "|".join(re.escape(i) for i in sorted(ids, key=len, reverse=True))
    nome = rf"({alt})(?![A-Za-z0-9_-])"
    estrito = re.compile(rf"(?<![A-Za-z0-9_.-])(?<![^/]/){nome}")     # not after a path slash (http://name is fine)
    caminho = re.compile(rf"(?<![A-Za-z0-9_.-]){nome}")
    sub = lambda rx, t: rx.sub(lambda m: m.group(1) + suffix, t)

    def linha(l):
        if l.startswith(keep):
            return l
        if l.startswith("Volume="):
            host, dois, resto = l.partition(":")
            return sub(caminho, host) + dois + sub(estrito, resto)
        if l.startswith("EnvironmentFile="):
            return sub(caminho, l)
        return sub(estrito, l)
    return "".join(linha(l) for l in text.splitlines(keepends=True))


def port_free(p):
    for fam, addr in ((socket.AF_INET, "0.0.0.0"), (socket.AF_INET6, "::")):
        try:
            with socket.socket(fam, socket.SOCK_STREAM) as s:
                s.bind((addr, p))
        except OSError as e:
            if fam == socket.AF_INET6 and e.errno in (97, 99):
                continue                    # no IPv6 here
            return False
    return True


def next_port(wanted, taken, free=port_free):
    p = wanted + 1
    while p < 65535 and (p in taken or not free(p)):
        p += 1
    return p


def host_ports(texts):
    """{host port} the unit texts publish (the numeric ones)."""
    saida = set()
    for t in texts:
        for v in directive_values(t, "PublishPort"):
            m = PORT.match(v)
            if m:
                saida.add(int(m.group(2)))
    return saida


def refusal(folder):
    """Why this app cannot be installed twice, or None."""
    for f in Path(folder).glob("*.container"):
        t = f.read_text()
        if "Network=host" in t.splitlines():
            return "it uses the host network, so two copies would fight over the same ports"
        for v in directive_values(t, "PublishPort"):
            if re.search(r"\d+-\d+", v.split("/")[0]):
                return "it publishes a range of ports"
    return None


def build(base, dest, inst, all_taken, ports=None, free=port_free, fingerprint=""):
    """Writes the instance folder `dest` from `base`. Returns {unit: {original port: new port}}."""
    base, dest, suffix = Path(base), Path(dest), f"-{inst}"
    if dest.exists():
        shutil.rmtree(dest)
    dest.mkdir(parents=True)
    textos = {f.name: f.read_text() for f in base.iterdir() if f.suffix in (".container", ".network")}
    ids = identifiers(base, textos.values())
    ports = {u: dict(p) for u, p in (ports or {}).items()}
    taken = set(all_taken)
    for nome, texto in textos.items():
        novo = rename(texto, ids, suffix)
        stem = Path(nome).stem
        mapa = ports.setdefault(stem, {})

        def troca(l):
            if l.startswith("Description="):
                return l.rstrip("\n") + f" [{inst}]\n"
            if not l.startswith("PublishPort="):
                return l
            m = PORT.match(l.split("=", 1)[1].strip())
            if not m:
                return l
            orig = m.group(2)
            if orig not in mapa:
                mapa[orig] = str(next_port(int(orig), taken, free))
            taken.add(int(mapa[orig]))
            ip = f"{m.group(1)}:" if m.group(1) else ""
            return f"PublishPort={ip}{mapa[orig]}:{m.group(3)}{m.group(4) or ''}\n"
        novo = "".join(troca(l) for l in novo.splitlines(keepends=True))
        (dest / (rename(Path(nome).stem, ids, suffix) + Path(nome).suffix)).write_text(novo)
        if not mapa:
            ports.pop(stem)
    # the rest of the folder: the logo and the files `config` copies, renamed when named after the app
    for f in base.rglob("*"):
        rel = f.relative_to(base)
        if f.is_dir() or rel.parts[0] == "screenshots" or rel.name in SKIP_FILES or f.suffix in (".container", ".network"):
            continue
        alvo = dest / rel.parent / rename(rel.name, ids, suffix)
        alvo.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(f, alvo)
    (dest / MARKER).write_text(f"{base.name}\n{fingerprint}\n")
    (dest / ".gitignore").write_text("*\n")
    return ports, ids


def fingerprint(base, inst, ports):
    """What the instance folder was built from: the base files (name, size, mtime) and the instance's ports."""
    import hashlib
    h = hashlib.sha1(json.dumps([inst, ports], sort_keys=True).encode())
    for f in sorted(Path(base).rglob("*")):
        if f.is_file() and "screenshots" not in f.parts:
            st = f.stat()
            h.update(f"{f.relative_to(base)}:{st.st_size}:{st.st_mtime_ns}".encode())
    return h.hexdigest()[:16]


def current(dest, fp):
    """Whether the folder was built from exactly this fingerprint."""
    try:
        return (Path(dest) / MARKER).read_text().split("\n")[1] == fp
    except (OSError, IndexError):
        return False


def make(base, dest, inst, all_taken, manifest_mod, ports=None, free=port_free):
    """Builds the folder and its app.json; returns the ports used ({unit: {original: new}})."""
    base = Path(base)
    ports, ids = build(base, dest, inst, all_taken, ports, free)
    m = manifest_mod.load(base)
    (Path(dest) / manifest_mod.FILE).write_text(manifest_mod.dump(derive_manifest(m, base.name, inst, ids)))
    (Path(dest) / MARKER).write_text(f"{base.name}\n{fingerprint(base, inst, ports)}\n")
    return ports


def derive_manifest(m, base_name, inst, ids):
    """app.json of the instance: the same recipe with the owned names suffixed, and what it is an instance of."""
    suffix = f"-{inst}"

    def r(s):
        return rename(s, ids, suffix) if isinstance(s, str) else s

    def keys(d):
        return {r(k): v for k, v in d.items()} if isinstance(d, dict) else d
    novo = {k: v for k, v in m.items() if k != "screenshots"}
    novo["title"] = f"{m.get('title', base_name)} ({inst})"
    for k in ("secrets", "validate", "units"):
        if k in novo:
            novo[k] = keys(novo[k])
    for k in ("config", "vars"):
        if k in novo and isinstance(novo[k], dict):
            novo[k] = {(rename(a, ids, suffix) if k == "config" else a): r(b) for a, b in novo[k].items()}
    if isinstance(novo.get("login"), dict):
        novo["login"] = {a: r(b) if a in ("password", "credentials") else b for a, b in novo["login"].items()}
    if isinstance(novo.get("units"), dict):
        novo["units"] = {u: ({**c, "login": {a: r(b) if a in ("password", "credentials") else b for a, b in c["login"].items()}}
                             if isinstance(c.get("login"), dict) else c) for u, c in novo["units"].items()}
    if isinstance(novo.get("options"), dict):
        for o in novo["options"].values():
            for v in o.get("values", {}).values():
                for k in ("units", "secrets"):
                    if k in v:
                        v[k] = [r(x) for x in v[k]]
    if isinstance(novo.get("widgets"), list):
        novo["widgets"] = [{**w, "unit": r(w["unit"])} if isinstance(w, dict) and w.get("unit") else w for w in novo["widgets"]]
    novo["instance"] = {"of": base_name, "name": inst}
    return novo


def selftest():
    import tempfile
    ids = {"memos", "memos-net", "memos-db"}
    t = ("[Container]\nImage=ghcr.io/x/memos-db:1\nContainerName=memos\nNetwork=memos-net.network\nNetworkAlias=memos\n"
         "Network=tsdproxy-net.network\nVolume=%h/.config/containers/volumes/memos/data:/data:Z\nEnvironment=MEMOS_X=1\n"
         "Secret=memos-key,type=env,target=K\nLabel=tsdproxy.name=memos\nPublishPort=5230:5230\n")
    out = rename(t, ids | {"memos-key"}, "-casa")
    assert "Image=ghcr.io/x/memos-db:1" in out and "NetworkAlias=memos\n" in out, "the image and the alias are not ours to rename"
    assert "ContainerName=memos-casa" in out and "Network=memos-net-casa.network" in out and "Network=tsdproxy-net.network" in out
    assert "Volume=%h/.config/containers/volumes/memos-casa/data:/data:Z" in out
    v = rename("Volume=%h/.config/containers/volumes/memos/data:/var/opt/memos:Z\nEnvironment=U=http://memos:5230\nEnvironment=P=/opt/memos\n"
               "EnvironmentFile=%h/.config/containers/env/memos.env\n", ids, "-casa")
    assert v == ("Volume=%h/.config/containers/volumes/memos-casa/data:/var/opt/memos:Z\nEnvironment=U=http://memos-casa:5230\n"
                 "Environment=P=/opt/memos\nEnvironment" "File=%h/.config/containers/env/memos-casa.env\n"), v
    assert "volumes/memos-casa/data" in out and "MEMOS_X=1" in out and "Secret=memos-key-casa," in out and "tsdproxy.name=memos-casa" in out
    assert next_port(8000, {8001, 8002}, lambda p: p != 8003) == 8004
    assert name_problem("memos", "Casa", set()) and name_problem("memos", "a", {"memos-a"}) and name_problem("memos", "casa", set()) is None
    with tempfile.TemporaryDirectory() as tmp:
        base, dest = Path(tmp) / "memos", Path(tmp) / "memos-casa"
        base.mkdir()
        (base / "memos.container").write_text(t.replace("Label=tsdproxy.name=memos\n", "Label=tsdproxy.name=memos\n"))
        (base / "memos-net.network").write_text("[Network]\nNetworkName=memos-net\n")
        (base / "memos.env.example").write_text("A=1\n")
        (base / "icon.svg").write_text("<svg/>")
        ports, ids2 = build(base, dest, "casa", {5230}, free=lambda p: True)
        assert ports == {"memos": {"5230": "5231"}}, ports
        assert (dest / "memos-casa.container").is_file() and (dest / "memos-net-casa.network").is_file()
        assert "PublishPort=5231:5230" in (dest / "memos-casa.container").read_text()
        assert (dest / "memos-casa.env.example").is_file() and (dest / "icon.svg").is_file() and is_instance(dest)
        assert "NetworkName=memos-net-casa" in (dest / "memos-net-casa.network").read_text()
        ports2, _ = build(base, dest, "casa", {5230, 5231}, ports, lambda p: True)
        assert ports2 == ports, "the recorded port stays"
        assert refusal(base) is None
        (base / "x.container").write_text("[Container]\nNetwork=host\n")
        assert "host network" in refusal(base)
        m = derive_manifest({"title": "Memos", "secrets": {"memos-key": "rand-hex 8"}, "units": {"memos": {"upstream": "a/b"}},
                             "login": {"user": "u", "password": "memos-key"}}, "memos", "casa", ids2)
        assert m["title"] == "Memos (casa)" and "memos-key-casa" in m["secrets"] and "memos-casa" in m["units"]
        assert m["login"]["password"] == "memos-key-casa" and m["instance"] == {"of": "memos", "name": "casa"}
        save(tmp, {"memos-casa": {"app": "memos"}})
        assert load(tmp)["memos-casa"]["app"] == "memos" and load(Path(tmp) / "none") == {}
    print("instances selftest: ok")


if __name__ == "__main__":
    selftest() if "--selftest" in sys.argv else print(__doc__)
