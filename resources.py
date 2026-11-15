#!/usr/bin/env python3
"""What Podman keeps on the disk that nothing uses any more: images, networks, volumes.

Every update leaves the previous image behind. `podman image prune -a` would clear
them, and also the image of every service that is installed but stopped — pulled
again at its next start. So "unused" here means what no container uses AND no
installed unit asks for: the `Image=` of every Quadlet file on the host decides.

    python3 resources.py                       # what could go, and how much
    python3 resources.py --json                # the same, for the store
    python3 resources.py prune images --apply  # remove them (dry-run without --apply)
    python3 resources.py --selftest

Networks and volumes are only listed when nothing — no container, no Quadlet
file — refers to them. A volume holds data, so pruning volumes asks for its name
typed (or --confirmed, which the store passes after asking the person).
"""

import argparse
import json
import os
import re
import subprocess
import sys
import tempfile
from pathlib import Path

PODMAN = os.environ.get("QH_PODMAN", "podman")     # tests point it at a stand-in
KINDS = ("images", "networks", "volumes")


# -- what the units ask for ------------------------------------------------------

def quadlet_files(home, suffix):
    base = Path(home) / ".config/containers/systemd"
    return sorted(base.rglob(f"*{suffix}")) if base.is_dir() else []


def directive(texto, chave):
    """The values of `chave=` in a unit's text (the last assignment wins for a scalar; all are returned)."""
    return [m.group(1).strip() for m in re.finditer(rf"^{chave}\s*=\s*(.+)$", texto, re.M)]


def normalize(ref):
    """`neosmemo/memos:0.31` -> `docker.io/neosmemo/memos:0.31`, the way Podman names it."""
    ref = ref.strip()
    primeiro = ref.split("/", 1)[0]
    if "/" not in ref:
        return "docker.io/library/" + ref
    if "." in primeiro or ":" in primeiro or primeiro == "localhost":
        return ref
    return "docker.io/" + ref


def wanted_images(home):
    """(names, digests) every installed unit asks for in `Image=`."""
    nomes, digests = set(), set()
    for f in quadlet_files(home, ".container") + quadlet_files(home, ".image"):
        for ref in directive(f.read_text(errors="replace"), "Image"):
            if ref.endswith(".image") or ref.endswith(".build"):
                continue                    # a reference to another Quadlet file, not a name
            if "@sha256:" in ref:
                digests.add("sha256:" + ref.split("@sha256:", 1)[1])
            nomes.add(normalize(ref.split("@")[0]))
    return nomes, digests


def declared(home, suffix, chave, prefixo):
    """Names a `.network`/`.volume` Quadlet file creates: its own key, else `systemd-<stem>`."""
    saida = set()
    for f in quadlet_files(home, suffix):
        explicito = directive(f.read_text(errors="replace"), chave)
        saida.add(explicito[-1] if explicito else prefixo + f.stem)
    return saida


# -- podman ------------------------------------------------------------------------

def podman_json(*args):
    r = subprocess.run([PODMAN, *args, "--format", "json"], capture_output=True, text=True, timeout=60)
    if r.returncode != 0:
        raise RuntimeError(r.stderr.strip() or f"podman {' '.join(args)} failed")
    return json.loads(r.stdout or "[]") or []


def survey(home):
    """What is unused, with sizes: {images: [...], networks: [...], volumes: [...], reclaimable: bytes}."""
    nomes, digests = wanted_images(home)
    imagens = []
    for im in podman_json("images"):
        refs = {normalize(n) for n in (im.get("Names") or [])}
        dig = {d.split("@")[-1] for d in (im.get("RepoDigests") or [])} | ({im["Digest"]} if im.get("Digest") else set())
        if im.get("Containers", 0) or refs & nomes or dig & digests:
            continue
        imagens.append({"id": im["Id"], "name": (im.get("Names") or ["<none>"])[0], "size": im.get("Size", 0),
                        "created": im.get("Created", 0)})
    imagens.sort(key=lambda x: -x["size"])

    containers = podman_json("ps", "-a")
    em_uso = {n for c in containers for n in (c.get("Networks") or [])}
    mantidas = declared(home, ".network", "NetworkName", "systemd-") | {"podman"}
    redes = [{"name": n["name"]} for n in podman_json("network", "ls")
             if n["name"] not in em_uso and n["name"] not in mantidas]

    # Podman's own word for "no container, running or not, mounts it"; a Quadlet-declared one is kept.
    vol_decl = declared(home, ".volume", "VolumeName", "systemd-")
    volumes = [{"name": v["Name"]} for v in podman_json("volume", "ls", "--filter", "dangling=true")
               if v["Name"] not in vol_decl]
    return {"images": imagens, "networks": redes, "volumes": volumes,
            "reclaimable": sum(i["size"] for i in imagens)}


def human(n):
    for u in ("B", "KB", "MB", "GB", "TB"):
        if n < 1024 or u == "TB":
            return f"{n:.0f} {u}" if u == "B" else f"{n:.1f} {u}"
        n /= 1024


def prune(kind, home, apply):
    """Removes what `survey` found, one by one (a failure on one does not stop the rest). Returns (done, failed)."""
    achado = survey(home)[kind]
    comando = {"images": "rmi", "networks": ("network", "rm"), "volumes": ("volume", "rm")}[kind]
    comando = (comando,) if isinstance(comando, str) else comando
    feitos = falhas = 0
    for item in achado:
        alvo = item["id"] if kind == "images" else item["name"]
        rotulo = item["name"] + (f"  ({human(item['size'])})" if kind == "images" else "")
        if not apply:
            print(f"  would remove {rotulo}")
            continue
        r = subprocess.run([PODMAN, *comando, alvo], capture_output=True, text=True)
        if r.returncode == 0:
            feitos += 1
            print(f"  removed {rotulo}")
        else:
            falhas += 1
            print(f"  kept {rotulo}: {(r.stderr.strip().splitlines() or ['?'])[-1]}")
    if apply:
        print(f"\nremoved {feitos}" + (f", kept {falhas} (still referenced by something)" if falhas else ""))
    elif not achado:
        print(f"  no unused {kind}.")
    return feitos, falhas


# -- command line --------------------------------------------------------------------

def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("action", nargs="?", choices=("list", "prune"), default="list")
    ap.add_argument("kind", nargs="?", choices=KINDS)
    ap.add_argument("--apply", action="store_true", help="do it (the default is to show)")
    ap.add_argument("--confirmed", action="store_true", help="skip the typed confirmation for volumes")
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--prefix", help="sandbox home")
    ap.add_argument("--selftest", action="store_true")
    a = ap.parse_args(argv)
    if a.selftest:
        return selftest()
    home = Path(a.prefix) if a.prefix else Path.home()
    try:
        if a.action == "list":
            r = survey(home)
            if a.json:
                print(json.dumps(r))
                return 0
            print(f"images no unit or container uses: {len(r['images'])}, up to {human(r['reclaimable'])}")
            for i in r["images"][:15]:
                print(f"  {human(i['size']):>9}  {i['name']}")
            print(f"networks: {len(r['networks'])}   volumes: {len(r['volumes'])}")
            return 0
        if not a.kind:
            ap.error("prune what? " + ", ".join(KINDS))
        if a.kind == "volumes" and a.apply and not a.confirmed:
            # A volume is data: the name typed, the way qh asks for a restore.
            if input("type `volumes` to delete the unused volumes: ").strip() != "volumes":
                print("cancelled.")
                return 1
        prune(a.kind, home, a.apply)
        if not a.apply:
            print("\nnothing was removed. repeat with --apply")
        return 0
    except (RuntimeError, OSError, subprocess.TimeoutExpired, json.JSONDecodeError) as e:
        print(f"podman: {e}")
        return 1


# -- selftest --------------------------------------------------------------------------

def selftest():
    assert normalize("neosmemo/memos:0.31") == "docker.io/neosmemo/memos:0.31"
    assert normalize("nginx:1.29") == "docker.io/library/nginx:1.29"
    assert normalize("ghcr.io/a/b:1") == "ghcr.io/a/b:1" and normalize("localhost/x:1") == "localhost/x:1"
    with tempfile.TemporaryDirectory() as t:
        d = Path(t, ".config/containers/systemd/app")
        d.mkdir(parents=True)
        (d / "a.container").write_text("[Container]\nImage=ghcr.io/a/b:1.0\n")
        (d / "c.container").write_text("[Container]\nImage=docker.io/x/y:2@sha256:abc\n")
        (d / "a-net.network").write_text("[Network]\nNetworkName=a-net\n")
        (d / "z.network").write_text("[Network]\n")
        (d / "kept.volume").write_text("[Volume]\n")
        n, g = wanted_images(t)
        assert n == {"ghcr.io/a/b:1.0", "docker.io/x/y:2"} and g == {"sha256:abc"}, (n, g)
        assert declared(t, ".network", "NetworkName", "systemd-") == {"a-net", "systemd-z"}

        # a stand-in podman: images (one used by a unit, one by a container, one by digest, two free),
        # networks and volumes
        falso = Path(t, "podman")
        falso.write_text("""#!/bin/sh
case "$*" in
  "images --format json") echo '[
    {"Id":"i1","Names":["ghcr.io/a/b:1.0"],"Size":100,"Containers":0},
    {"Id":"i2","Names":["ghcr.io/a/b:0.9"],"Size":300,"Containers":0},
    {"Id":"i3","Names":["docker.io/q/r:1"],"Size":50,"Containers":1},
    {"Id":"i4","Names":["docker.io/x/y:old"],"Size":70,"Containers":0,"RepoDigests":["docker.io/x/y@sha256:abc"]},
    {"Id":"i5","Names":[],"Size":20,"Containers":0}]';;
  "ps -a --format json") echo '[{"Networks":["used-net"],"Mounts":["/data"]}]';;
  "network ls --format json") echo '[{"name":"podman"},{"name":"a-net"},{"name":"systemd-z"},{"name":"used-net"},{"name":"stray"}]';;
  "volume ls --filter dangling=true --format json") echo '[{"Name":"vol-free"},{"Name":"systemd-kept"}]';;
  "rmi i2"|"rmi i5"|"network rm stray"|"volume rm vol-free") echo gone;;
  *) echo "unexpected: $*" >&2; exit 1;;
esac
""")
        falso.chmod(0o755)
        global PODMAN
        PODMAN = str(falso)
        r = survey(t)
        assert [i["id"] for i in r["images"]] == ["i2", "i5"], "the unit's image, the container's and the digest-pinned one stay"
        assert r["reclaimable"] == 320
        assert [x["name"] for x in r["networks"]] == ["stray"], "the default, the declared and the used one stay"
        assert [x["name"] for x in r["volumes"]] == ["vol-free"], "a declared volume stays"
        assert prune("images", t, False) == (0, 0) and prune("images", t, True) == (2, 0)
        assert prune("networks", t, True) == (1, 0) and prune("volumes", t, True) == (1, 0)
    print("resources selftest: ok")
    return 0


if __name__ == "__main__":
    sys.exit(main())
