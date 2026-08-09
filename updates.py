#!/usr/bin/env python3
"""Compares the `Image=` tags in this repository with the latest GitHub release.

The rule this script exists to automate: **the source of truth is the
project's GitHub releases page, not the registry's tag list**. Registries list
betas, RCs and build variants that sort as "newer" without being releases —
n8n keeps 2.33.x and 2.34.x in parallel and marks 2.33 as latest; nginx,
AdGuard, Memos and Frigate publish RCs alongside the stable tags.

That is why the lookup follows the redirect of
`github.com/<org>/<repo>/releases/latest`, which returns the tag without
spending API rate limit.

    python3 updates.py           # table of what is behind
    python3 updates.py --all     # include what is up to date

No dependencies: stdlib only. Exits 0 even with an outdated service — being
behind is information, not a defect; only an execution error fails.
"""

import argparse
import configparser
import re
import sys
import urllib.error
import urllib.request
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

from qhlang import translator

PT = {
    "OUTDATED (": "DESATUALIZADOS (",
    "cannot compare (": "sem comparação (",
    "up to date:": "em dia:",
    "images:": "imagens:",
    "outdated,": "desatualizadas,",
    "up to date,": "em dia,",
    "with a floating tag,": "com tag flutuante,",
    "not compared": "não comparadas",
}
loc = translator(PT)


UA = "quadlet-homelab updates.py"

RAIZ = Path(__file__).resolve().parent
APPS = RAIZ / "apps"

# A tag that is not a version: there is nothing to compare between runs.
FLOATING = {"latest", "main", "master", "stable", "edge", "develop", "nightly"}


def directives(text):
    out = []
    for line in text.splitlines():
        line = line.strip()
        if not line or line.startswith(("#", ";", "[")):
            continue
        key, sep, value = line.partition("=")
        if sep:
            out.append((key.strip(), value.strip()))
    return out


def compose_tag(spec, ref, image):
    """The tag this image carries in the app's own compose, at version `ref`.

    A sidecar follows the version the app validates, not its own upstream: the
    Postgres in immich's compose moves when immich moves it, and reporting
    Postgres's latest release would only ever say "behind". Spelled in
    install.ini as

        [upstream]
        immich-postgres = compose:immich-app/immich:docker/docker-compose.yml

    and read from the tag the main unit is pinned at, which is the version you
    would be going to.
    """
    resto = spec.partition(":")[2]
    nome = image.split("@")[0].rpartition(":")[0].split("/")[-1]
    if resto.startswith(("http://", "https://")):
        # Not every project keeps its compose in the repository: authentik
        # publishes it on its own site, and that is the file its docs tell you
        # to use.
        urls = [resto]
    else:
        try:
            repo, path = resto.split(":", 1)
        except ValueError:
            return None
        urls = [f"https://raw.githubusercontent.com/{repo}/{r}/{path}"
                for r in (ref, "v" + ref, "main", "master")]
    for url in urls:
        try:
            # Some sites answer 403 to urllib's default agent; GitHub does not,
            # but goauthentik.io does, and that is where its compose lives.
            req = urllib.request.Request(url, headers={"User-Agent": UA})
            with urllib.request.urlopen(req, timeout=20) as f:
                texto = f.read().decode("utf-8", "replace")
        except Exception:
            continue
        for m in re.finditer(r"image:\s*[\"\']?([^\s\"\']+)", texto):
            cand = m.group(1)
            if cand.split("@")[0].rpartition(":")[0].split("/")[-1] == nome:
                return cand.split("@")[0].rpartition(":")[2] or None
        return None
    return None


def github_repo(image, override):
    """`org/repo` on GitHub from the image, or None when it cannot be derived.

    Derives it where the convention holds (ghcr mirrors the repository owner)
    and accepts an override in `apps/<app>/install.ini`, section [upstream],
    for the cases where the image name has nothing to do with the project's.
    """
    if override:
        return None if override == "-" else override
    path = image.split(":")[0]
    parts = path.split("/")
    if parts[0] == "ghcr.io" and len(parts) >= 3:
        # ghcr.io/<org>/<repo> comes from GitHub itself: same owner.
        return f"{parts[1]}/{parts[2]}"
    if parts[0] == "lscr.io" and len(parts) >= 3:
        # LinuxServer publishes each image in a docker-<name> repo.
        return f"linuxserver/docker-{parts[2]}"
    if parts[0] == "docker.io" and len(parts) == 3:
        # A guess with a good hit rate (traccar/traccar, donetick/donetick);
        # when it misses, [upstream] in install.ini corrects it.
        return f"{parts[1]}/{parts[2]}"
    return None


class NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, *a, **k):
        return None


OPENER = urllib.request.build_opener(NoRedirect)


def latest_release(repo):
    """The tag /releases/latest redirects to, without spending the API quota."""
    url = f"https://github.com/{repo}/releases/latest"
    try:
        r = OPENER.open(urllib.request.Request(url, method="HEAD"), timeout=20)
        target = r.headers.get("Location", r.url)
    except urllib.error.HTTPError as e:
        if e.code not in (301, 302, 303, 307, 308):
            return None
        target = e.headers.get("Location", "")
    except OSError:
        return None
    if "/tag/" not in target:
        return None          # project with no published release
    return target.rsplit("/tag/", 1)[1]


def version(tag):
    """(1, 2, 3) from the first dotted number in the tag, or None.

    Works for both sides: our tag may carry a variant suffix
    (`0.10.1-nginx-php8.2`) and GitHub's may carry a prefix (`v2.27.0`).
    """
    m = re.search(r"\d+(?:\.\d+)+", tag or "")
    return tuple(int(x) for x in m.group().split(".")) if m else None


def services():
    for folder in sorted(p for p in APPS.iterdir() if p.is_dir()):
        ini = configparser.ConfigParser(interpolation=None)
        ini.read(folder / "install.ini")
        overrides = dict(ini.items("upstream")) if ini.has_section("upstream") else {}
        principal = folder / f"{folder.name}.container"
        conts = sorted(folder.glob("*.container"))
        if not principal.exists() and len(conts) == 1:
            principal = conts[0]
        ref = ""
        if principal.exists():
            img = next((v for k, v in directives(principal.read_text()) if k == "Image"), "")
            ref = img.split("@")[0].rpartition(":")[2]
        for cont in conts:
            for key, value in directives(cont.read_text()):
                if key == "Image":
                    yield folder.name, cont.stem, value, overrides.get(cont.stem), ref


def check(item):
    app, unit, image, override, ref = item
    tag = image.split("@")[0].rpartition(":")[2]
    if override and override.startswith("compose:"):
        there = compose_tag(override, ref, image)
        if not there:
            return (unit, image, tag, "?", "compose: image not found there")
        if version(there) and version(tag) and version(there) > version(tag):
            return (unit, image, tag, there, "BEHIND")
        return (unit, image, tag, there, "up to date")
    if tag in FLOATING or "/" in tag:
        return (unit, image, tag, "—", "floating tag")
    repo = github_repo(image, override)
    if not repo:
        return (unit, image, tag, "?", "unknown repo — declare it in [upstream]")
    remote = latest_release(repo)
    if not remote:
        return (unit, image, tag, "?", f"{repo}: no published release")
    here, there = version(tag), version(remote)
    if not here or not there:
        return (unit, image, tag, remote, "not comparable")
    # Common prefix only: LinuxServer publishes release `4.0.19.2979-ls320`
    # for an image pinned at `4.0.19`, and comparing everything would always
    # say "behind".
    n = min(len(here), len(there))
    here, there = here[:n], there[:n]
    if there > here:
        return (unit, image, tag, remote, "BEHIND")
    return (unit, image, tag, remote, "up to date")


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--all", action="store_true", help="also show what is up to date")
    a = ap.parse_args()

    items = list(services())
    with ThreadPoolExecutor(max_workers=8) as pool:
        rows = list(pool.map(check, items))

    behind = [l for l in rows if l[4] == "BEHIND"]
    unclear = [l for l in rows if l[4].startswith(("unknown repo", "not comparable", "compose:"))
               or "no published release" in l[4]]

    def table(label, ls):
        if not ls:
            return
        print(loc(f"\n{label}"))
        for unit, _, here, there, _ in sorted(ls):
            print(f"  {unit:<28} {here:<24} -> {there}")

    table(f"OUTDATED ({len(behind)}):", behind)
    # What could not be compared stays out of the way: it is a property of the
    # image's naming, not something to act on. --all brings it back.
    if a.all:
        table(f"cannot compare ({len(unclear)}):", unclear)
        table("up to date:", [l for l in rows if l[4] == "up to date"])

    floating = sum(1 for l in rows if l[4] == "floating tag")
    print(loc(f"\n{len(rows)} images: {len(behind)} outdated, "
              f"{sum(1 for l in rows if l[4] == 'up to date')} up to date, "
              f"{floating} with a floating tag, {len(unclear)} not compared"))
    return 0


if __name__ == "__main__":
    sys.exit(main())
