#!/usr/bin/env python3
"""Checks the rules of this repository that currently rely on human discipline.

It covers mainly the traps the conventions classify as "no visible error":
Quadlet generates the unit, `podman inspect` does not complain, and the
defect only shows up in production.

Usage:
    python3 check.py            # check the repository
    python3 check.py --selftest # test the parser itself

Exits 1 if there is any error, 0 if there are only warnings.
No dependencies: stdlib only, so it runs on the immutable host as-is.
"""

import re
import sys
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parent
APPS = ROOT / "apps"

errors: list[str] = []
warnings: list[str] = []


def error(rule, msg):
    errors.append(f"{rule}: {msg}")


def warn(rule, msg):
    warnings.append(f"{rule}: {msg}")


# --------------------------------------------------------------------------
# parsing
# --------------------------------------------------------------------------

def directives(text):
    """[(key, value)] for the directive lines, skipping comments and sections.

    Quadlet has no line continuation, so a simple scan is enough.
    """
    out = []
    for line in text.splitlines():
        line = line.strip()
        if not line or line.startswith(("#", ";", "[")):
            continue
        key, sep, value = line.partition("=")
        if sep:
            out.append((key.strip(), value.strip()))
    return out


def exemptions(text):
    """Rules the unit waives itself, via `# check: ignore <rule> <reason>`.

    It lives in the unit instead of a central allowlist on purpose: the reason
    sits next to what it justifies, like every other comment in this repo.
    """
    return {m.group(1) for m in re.finditer(r"^#\s*check:\s*ignore\s+(\S+)", text, re.M)}


def published_port(value):
    """('8099', 'tcp') for what the host opens, or None if it opens nothing.

    Forms Quadlet accepts: `port`, `host:cont`, `ip:host:cont`, with an optional
    `/proto`. A bare `port` lets Podman pick the host side at random — there is
    no collision to check, so it is ignored.
    """
    value, _, proto = value.partition("/")
    proto = proto or "tcp"
    parts = value.split(":")
    if len(parts) < 2:
        return None
    return parts[-2], proto


def main_unit(folder):
    """The .container that represents the app (the one the version table mirrors)."""
    conts = sorted(folder.glob("*.container"))
    if not conts:
        return None
    exact = folder / f"{folder.name}.container"
    if exact in conts:
        return exact
    return conts[0] if len(conts) == 1 else None


def image_tag(path):
    """The tag in `Image=`, or None when there is no comparable tag.

    An image pinned by digest (`...@sha256:abc...`) has no tag: comparing the
    hex against the README's Version column would only produce noise.
    """
    for key, value in directives(path.read_text()):
        if key == "Image":
            if "@sha256:" in value:
                return None
            _, _, tag = value.rpartition(":")
            return tag if tag and "/" not in tag else None
    return None


# --------------------------------------------------------------------------
# checks
# --------------------------------------------------------------------------

def check_units(folders):
    seen = defaultdict(list)
    for folder in folders:
        files = sorted(folder.glob("*.container")) + sorted(folder.glob("*.network"))
        for f in files:
            seen[f.name].append(f"apps/{folder.name}")
            if not f.name.startswith(folder.name) and not folder.name.startswith(f.stem):
                warn("rule 1", f"apps/{folder.name}/{f.name} does not use the app name "
                               f"as a prefix")

        conts = [a for a in files if a.suffix == ".container"]
        nets = [a for a in files if a.suffix == ".network"]
        if nets and len(conts) == 1:
            warn("structure", f"apps/{folder.name} is single-container but has a .network "
                              f"(single-container uses the default network)")

        for f in conts:
            check_container(f, folder)

    # The basename becomes the unit name across the whole host, even across
    # subfolders: two files with the same name in different folders really collide.
    for name, where in seen.items():
        if len(where) > 1:
            error("rule 1", f"basename {name} repeated in {', '.join(where)} "
                            f"— they become the same systemd unit")


def check_container(path, folder):
    text = path.read_text()
    ds = directives(text)
    keys = {c for c, _ in ds}
    ref = f"apps/{folder.name}/{path.name}"

    if ("Notify", "healthy") in ds and "HealthCmd" not in keys:
        error("rule 14", f"{ref} uses Notify=healthy without HealthCmd= "
                         f"(the image's own HEALTHCHECK does not count)")

    for key, value in ds:
        if key == "HealthCmd":
            if "localhost" in value:
                error("rule 13", f"{ref} uses localhost in HealthCmd "
                                 f"(resolves IPv4+IPv6; use 127.0.0.1)")
            # systemd expands $VAR; a literal one needs $$.
            if re.search(r"(?<!\$)\$(?!\$)[A-Za-z{]", value):
                error("rule 7", f"{ref} has a bare $ in HealthCmd (escape it as $$)")

        if key == "Label":
            if "\\" in value:
                error("rule 18", f"{ref}: Label with a backslash — Quadlet drops the "
                                 f"whole line ({value[:40]}…)")
            _, _, content = value.partition("=")
            if " " in content and not (content.startswith(('"', "'"))):
                error("rule 12", f"{ref}: Label with an unquoted space, truncates at the "
                                 f"first one ({value[:40]}…)")

    # Main container only: a sidecar (database, broker, worker) usually follows
    # the version the app's own compose validates, not its own upstream.
    if path == main_unit(folder) and "wud" not in exemptions(text):
        if "AutoUpdate" not in keys and not any(
                c == "Label" and v.startswith("wud.watch") for c, v in ds):
            warn("wud", f"{ref} has neither AutoUpdate= nor wud.watch — "
                        f"nothing will report a new version")


def check_ports(folders):
    uses = defaultdict(list)
    for folder in folders:
        for f in sorted(folder.glob("*.container")):
            text = f.read_text()
            if "ports" in exemptions(text):
                continue
            for key, value in directives(text):
                if key != "PublishPort":
                    continue
                p = published_port(value)
                if p:
                    uses[p].append(f"apps/{folder.name}/{f.name}")
    for (port, proto), where in sorted(uses.items()):
        if len(set(where)) > 1:
            error("ports", f"{port}/{proto} published by {', '.join(sorted(set(where)))}")
    return uses


def check_manifest(folders):
    """Every Secret= has a recipe, and every .example has a known destination.

    This is what keeps install.py from stopping halfway through a service.
    """
    import configparser
    for folder in folders:
        ini = configparser.ConfigParser(interpolation=None)
        ini.read(folder / "install.ini")
        recipes = set(ini["secrets"]) if ini.has_section("secrets") else set()
        declared = set()
        for f in sorted(folder.glob("*.container")):
            for key, value in directives(f.read_text()):
                if key == "Secret":
                    declared.add(value.split(",")[0])
        for missing in sorted(declared - recipes):
            error("manifest", f"apps/{folder.name}: Secret={missing} has no recipe in "
                              f"install.ini [secrets] — install.py cannot generate it")
        for extra in sorted(recipes - declared):
            warn("manifest", f"apps/{folder.name}: install.ini has a recipe for {extra}, "
                             f"which no unit uses")
        # [login] names the secret the install prints as the password. A typo
        # here is silent — the footer would just skip the login block.
        pw = ini.get("login", "password", fallback=None) if ini.has_section("login") else None
        if pw and pw not in declared:
            error("manifest", f"apps/{folder.name}: install.ini [login] password = {pw}, "
                              f"which no unit declares as a Secret=")


# O rótulo que pode aparecer imediatamente antes de `.ts.net`. Vazio inclusive:
# a documentação mostra `my-app..ts.net` de propósito, pra explicar o que
# acontece quando ${TAILNET} não está definida.
TAILNET_PLACEHOLDERS = {"", "${TAILNET}", "<tailnet>", "<your-tailnet>", "your-tailnet"}


def check_tailnet():
    """No real tailnet name anywhere: the repository is public.

    It leaked once from a block showing install.py's output — which looks like
    a log rather than configuration, and so escaped review. This checks every
    text file, not just the units.
    """
    skip = {".git", "__pycache__", "volumes", "secrets"}
    for f in sorted(ROOT.rglob("*")):
        if not f.is_file() or any(p in skip for p in f.parts):
            continue
        try:
            text = f.read_text()
        except (UnicodeDecodeError, OSError):
            continue
        lines = text.split("\n")
        for m in re.finditer(r"([A-Za-z0-9_${}<>-]*)\.ts\.net", text):
            if m.group(1) not in TAILNET_PLACEHOLDERS:
                line = text[: m.start()].count("\n") + 1
                if "check: ignore tailnet" in lines[line - 1]:
                    continue
                error("tailnet", f"{f.relative_to(ROOT)}:{line} carries a real "
                                 f"tailnet name (`{m.group(1)}`) — the repository is "
                                 f"public; use ${{TAILNET}} or <your-tailnet>")


def check_table(folders):
    readme = (ROOT / "README.md").read_text()
    rows = {}
    for line in readme.splitlines():
        m = re.match(r"^\|.*?\|\s*\[[^\]]+\]\(\./apps/([a-z0-9._-]+)\)\s*\|([^|]*)\|", line)
        if m:
            rows[m.group(1)] = m.group(2).strip()

    names = {p.name for p in folders}
    for missing in sorted(names - rows.keys()):
        error("table", f"apps/{missing} has no row in the README version table")
    for extra in sorted(rows.keys() - names):
        error("table", f"the README table mentions apps/{extra}, which does not exist")

    for folder in folders:
        cell = rows.get(folder.name)
        if cell is None or cell.strip() in ("—", "-", ""):
            continue  # stack with no single version (media-stack)
        unit = main_unit(folder)
        if unit is None:
            continue  # multi-container with no clear main unit
        tag = image_tag(unit)
        if tag and tag not in cell:
            error("table", f"apps/{folder.name}: Image= uses `{tag}` but the README "
                           f"table says `{cell}`")


# --------------------------------------------------------------------------
# selftest
# --------------------------------------------------------------------------

def selftest():
    assert directives("[Container]\n# c\nImage=x:1\n\nPublishPort=8080:80\n") == [
        ("Image", "x:1"), ("PublishPort", "8080:80")]
    assert directives("Label=homepage.name=Open WebUI") == [("Label", "homepage.name=Open WebUI")]

    assert published_port("8099:8082") == ("8099", "tcp")
    assert published_port("5056:5055/udp") == ("5056", "udp")
    assert published_port("127.0.0.1:8082:80") == ("8082", "tcp")
    assert published_port("69") is None, "a bare port is picked by Podman"

    # $$ is the correct escape; a bare $ is the silent defect of rule 7
    bad = re.compile(r"(?<!\$)\$(?!\$)[A-Za-z{]")
    assert bad.search("test $$(date)") is None
    assert bad.search("echo $VAR") is not None
    assert bad.search("price is R$ 5") is None, "a lone dollar sign is not expansion"

    import tempfile
    with tempfile.TemporaryDirectory() as d:
        p = Path(d) / "x.container"
        p.write_text("[Container]\nImage=ghcr.io/a/b:v1.2.3\n")
        assert image_tag(p) == "v1.2.3"
        p.write_text("[Container]\nImage=quay.io/a/b\n")
        assert image_tag(p) is None, "an untagged image must not become a fake tag"
        p.write_text("[Container]\nImage=docker.io/a/b@sha256:" + "0" * 64 + "\n")
        assert image_tag(p) is None, "a digest is not a tag: nothing to compare against"

    # o guarda de tailnet: pega nome real, aceita os placeholders
    lab = lambda t: re.findall(r"([A-Za-z0-9_${}<>-]*)\.ts\.net", t)
    assert lab("https://traccar.some-real-name.ts.net") == ["some-real-name"]  # check: ignore tailnet
    assert lab("https://memos.${TAILNET}.ts.net") == ["${TAILNET}"]
    assert lab("https://x.<your-tailnet>.ts.net") == ["<your-tailnet>"]
    assert lab("https://my-app..ts.net") == [""], "TAILNET vazia é exemplo da doc"
    assert all(x in TAILNET_PLACEHOLDERS for x in
               lab("https://a.${TAILNET}.ts.net https://b.<tailnet>.ts.net"))
    assert "some-real-name" not in TAILNET_PLACEHOLDERS  # check: ignore tailnet

    print("selftest: ok")


# --------------------------------------------------------------------------

def main():
    if "--selftest" in sys.argv:
        selftest()
        return 0

    if not APPS.is_dir():
        print(f"could not find {APPS}", file=sys.stderr)
        return 2

    folders = sorted(p for p in APPS.iterdir() if p.is_dir())
    check_units(folders)
    uses = check_ports(folders)
    check_manifest(folders)
    check_table(folders)
    check_tailnet()

    conts = sum(len(list(p.glob("*.container"))) for p in folders)
    print(f"{len(folders)} services, {conts} containers, {len(uses)} published ports\n")

    for label, items in (("ERROR", errors), ("warn ", warnings)):
        for i in items:
            print(f"  {label}  {i}")
    if errors or warnings:
        print()
    print(f"{len(errors)} error(s), {len(warnings)} warning(s)")
    return 1 if errors else 0


if __name__ == "__main__":
    sys.exit(main())
