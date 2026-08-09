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
import json
import subprocess
import urllib.parse
import urllib.request
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

from qhui import translator, red, yellow, green, dim

PT = {
    "OUTDATED (": "DESATUALIZADOS (",
    "floating tag, moved since your pull (": "tag flutuante, mudou desde o seu pull (",
    "novo digest": "digest novo",
    "mesmo digest": "mesmo digest",
    "released, image not published yet (": "lançado, imagem ainda não publicada (",
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


def _repo_ref(image):
    """(host, repo) for the registry API, from an image reference."""
    ref = image.split("@")[0]
    if ":" in ref.rsplit("/", 1)[-1]:
        ref = ref.rpartition(":")[0]
    parts = ref.split("/")
    if "." in parts[0] or ":" in parts[0]:
        host, repo = parts[0], "/".join(parts[1:])
    else:
        host, repo = "registry-1.docker.io", ref if "/" in ref else "library/" + ref
    return ("registry-1.docker.io" if host == "docker.io" else host), repo


def _registry_get(url, token=None):
    """GET with the registry's token dance. (body, token) or (None, None)."""
    cab = {"User-Agent": UA}
    if token:
        cab["Authorization"] = f"Bearer {token}"
    try:
        with urllib.request.urlopen(urllib.request.Request(url, headers=cab), timeout=25) as f:
            return f.read().decode("utf-8", "replace"), token
    except urllib.error.HTTPError as e:
        if e.code != 401 or token:
            return None, token
        campos = dict(re.findall(r'(\w+)="([^"]*)"', e.headers.get("WWW-Authenticate", "")))
        if "realm" not in campos:
            return None, None
        q = urllib.parse.urlencode({k: v for k, v in campos.items() if k != "realm"})
        try:
            with urllib.request.urlopen(urllib.request.Request(
                    f"{campos['realm']}?{q}", headers={"User-Agent": UA}), timeout=20) as f:
                dados = json.load(f)
            tok = dados.get("token") or dados.get("access_token")
        except Exception:
            return None, None
        return _registry_get(url, tok)
    except Exception:
        return None, token


def _registry_get_link(url, token=None):
    """_registry_get plus the `Link: rel="next"` of a paginated listing."""
    cab = {"User-Agent": UA}
    if token:
        cab["Authorization"] = f"Bearer {token}"
    try:
        with urllib.request.urlopen(urllib.request.Request(url, headers=cab), timeout=25) as f:
            link = f.headers.get("Link", "")
            prox = re.search(r'<([^>]+)>;\s*rel="next"', link)
            return f.read().decode("utf-8", "replace"), token, prox.group(1) if prox else None
    except urllib.error.HTTPError as e:
        if e.code != 401 or token:
            return None, token, None
        corpo, tok = _registry_get(url, None)
        if corpo is None:
            return None, None, None
        # segunda ida, agora com o token, para pegar o Link
        return _registry_get_link(url, tok)
    except Exception:
        return None, token, None


def registry_tags(image, paginas=20):
    """Every tag the registry lists for this image, or None if it cannot.

    Paginated and capped: nginx publishes thousands, and the newest versions
    are what matter — a cap keeps one image from spending the whole run.
    """
    host, repo = _repo_ref(image)
    url = f"https://{host}/v2/{repo}/tags/list?n=1000"
    todas, token, visto = [], None, set()
    for _ in range(paginas):
        corpo, token, prox = _registry_get_link(url, token)
        if corpo is None:
            break
        try:
            todas += json.loads(corpo).get("tags") or []
        except Exception:
            break
        if not prox or prox in visto:
            break
        visto.add(prox)
        url = prox if prox.startswith("http") else f"https://{host}{prox}"
    return todas or None


def registry_newest(image, tag, padrao=None):
    """The newest registry tag shaped like ours, or None.

    Shape matters: `1.31.1-alpine` and `1.31.1-perl` are different images with
    the same version, and `26.04` must not be compared against `latest`. The
    pattern comes from our own tag — digits become \\d+, everything else stays.
    """
    tags = registry_tags(image)
    if not tags:
        return None
    if padrao:
        # An explicit pattern, for a project whose numbering carries meaning the
        # shape cannot: nginx puts stable on even minors and mainline on odd,
        # and both publish `-alpine`.
        rx = re.compile(padrao)
    else:
        forma = "".join(r"\d+" if p.isdigit() else re.escape(p)
                        for p in re.findall(r"\d+|\D+", tag))
        rx = re.compile("^" + forma + "$")
    def numeros(x):
        return tuple(int(n) for n in re.findall(r"\d+", x))
    candidatas = [(numeros(x), x) for x in tags if rx.match(x)]
    return max(candidatas)[1] if candidatas else None


def _manifest_head(image, tag):
    """HEAD on the manifest, with the registry's token dance. Headers, or None.

    Ask without auth, read the WWW-Authenticate challenge, come back with the
    token — the standard flow, so it works on Docker Hub and ghcr without a
    branch for each.
    """
    ref = image.split("@")[0]
    # Only the last segment can carry the tag; a `:` earlier is a registry port.
    if ":" in ref.rsplit("/", 1)[-1]:
        ref = ref.rpartition(":")[0]
    parts = ref.split("/")
    if "." in parts[0] or ":" in parts[0]:
        host, repo = parts[0], "/".join(parts[1:])
    else:
        host, repo = "registry-1.docker.io", ref if "/" in ref else "library/" + ref
    if host == "docker.io":
        host = "registry-1.docker.io"
    url = f"https://{host}/v2/{repo}/manifests/{tag}"
    aceita = ("application/vnd.oci.image.index.v1+json,"
              "application/vnd.docker.distribution.manifest.list.v2+json,"
              "application/vnd.oci.image.manifest.v1+json,"
              "application/vnd.docker.distribution.manifest.v2+json")

    def pedir(cabec):
        return urllib.request.urlopen(urllib.request.Request(
            url, method="HEAD",
            headers={"Accept": aceita, "User-Agent": UA, **cabec}), timeout=20)

    try:
        return pedir({}).headers
    except urllib.error.HTTPError as e:
        if e.code == 404:
            return False
        if e.code != 401:
            return None
        desafio = e.headers.get("WWW-Authenticate", "")
    except Exception:
        return None
    campos = dict(re.findall(r'(\w+)="([^"]*)"', desafio))
    if "realm" not in campos:
        return None
    q = urllib.parse.urlencode({k: v for k, v in campos.items() if k != "realm"})
    try:
        with urllib.request.urlopen(urllib.request.Request(
                f"{campos['realm']}?{q}", headers={"User-Agent": UA}), timeout=20) as f:
            dados = json.load(f)
        token = dados.get("token") or dados.get("access_token")
        return pedir({"Authorization": f"Bearer {token}"}).headers
    except urllib.error.HTTPError as e:
        return False if e.code == 404 else None
    except Exception:
        return None


def registry_has(image, tag):
    """True when that exact tag can be pulled, None when the check itself failed.

    A GitHub release is not a published image: the release can land hours
    before the registry has the tag, and reporting it as available sends you
    to a `podman pull` that fails.
    """
    h = _manifest_head(image, tag)
    return None if h is None else bool(h)


def moved(image, tag):
    """True when a floating tag now points somewhere else than the local copy.

    A floating tag has no version to compare, but it does have a digest. The
    local image carries both digests podman knows — the platform manifest and
    the multi-arch index — and the registry answers with the index, so the
    check is whether the registry's is among them. Without podman, or with the
    image not pulled yet, there is nothing to compare and it returns None.
    """
    h = _manifest_head(image, tag)
    if not h:
        return None
    remoto = h.get("Docker-Content-Digest")
    if not remoto:
        return None
    try:
        r = subprocess.run(["podman", "image", "inspect", image, "--format",
                            "{{.Digest}} {{range .RepoDigests}}{{.}} {{end}}"],
                           capture_output=True, text=True, timeout=30)
    except Exception:
        return None
    if r.returncode != 0 or not r.stdout.strip():
        return None
    locais = {x.rpartition("@")[2] or x for x in r.stdout.split()}
    return remoto not in locais


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
    if override and override.startswith("registry"):
        # For an image that does not version by GitHub release — a distro tag,
        # a project that only publishes git tags, an image versioned apart from
        # its repository — the registry is the only source that knows.
        _, _, padrao = override.partition(":")
        there = registry_newest(image, tag, padrao or None)
        if not there:
            return (unit, image, tag, "?", "registry: no comparable tag")
        n = lambda x: tuple(int(v) for v in re.findall(r"\d+", x))
        if n(there) > n(tag):
            return (unit, image, tag, there, "BEHIND")
        return (unit, image, tag, there, "up to date")

    if override and override.startswith("compose:"):
        there = compose_tag(override, ref, image)
        if not there:
            return (unit, image, tag, "?", "compose: image not found there")
        if there in FLOATING or there.isdigit() and not version(tag):
            return (unit, image, tag, there, "floating tag")
        if there in FLOATING:
            # The app does not pin it either: following the compose says
            # nothing, and calling that "up to date" would be a false comfort.
            return (unit, image, tag, there, "compose: not pinned there")
        if version(there) and version(tag) and version(there) > version(tag):
            return (unit, image, tag, there, "BEHIND")
        return (unit, image, tag, there, "up to date")
    # A bare major (`:2`) moves the same way `latest` does: the digest changes
    # under the same name, so there is no version to compare.
    if tag in FLOATING or "/" in tag or tag.isdigit():
        # No version to compare, but there is a digest: if the tag now points
        # somewhere else than the local copy, an update is waiting behind the
        # same name. Without podman, or before the first pull, there is nothing
        # to compare against.
        m = moved(image, tag)
        if m is True:
            return (unit, image, tag, "novo digest", "MOVED")
        if m is False:
            return (unit, image, tag, "mesmo digest", "up to date")
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
        # The release names a version; the tag we would pull keeps our own
        # variant (`-alpine`, `-stable`). Check that exact tag exists before
        # calling it available: a release can land hours before the image does.
        sufixo = re.sub(r"^[0-9][0-9.]*", "", tag)
        alvo = remote.lstrip("v") + sufixo
        existe = registry_has(image, alvo)
        if existe is False:
            return (unit, image, tag, alvo, "released, not published yet")
        return (unit, image, tag, alvo, "BEHIND")
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
    movidas = [l for l in rows if l[4] == "MOVED"]
    unclear = [l for l in rows if l[4].startswith(("unknown repo", "not comparable", "compose:"))
               or "no published release" in l[4]]
    pendente = [l for l in rows if l[4] == "released, not published yet"]

    def table(label, ls, cor=yellow):
        if not ls:
            return
        print("\n" + cor(loc(label)))
        for unit, _, here, there, _ in sorted(ls):
            print(f"  {unit:<28} {here:<24} -> {there}")

    table(f"OUTDATED ({len(behind)}):", behind, red)
    table(f"released, image not published yet ({len(pendente)}):", pendente)
    table(f"floating tag, moved since your pull ({len(movidas)}):", movidas)
    # What could not be compared stays out of the way: it is a property of the
    # image's naming, not something to act on. --all brings it back.
    if a.all:
        table(f"cannot compare ({len(unclear)}):", unclear)
        table("up to date:", [l for l in rows if l[4] == "up to date"], green)

    floating = sum(1 for l in rows if l[4] == "floating tag")
    print(loc(f"\n{len(rows)} images: {len(behind)} outdated, "
              f"{sum(1 for l in rows if l[4] == 'up to date')} up to date, "
              f"{floating} with a floating tag, {len(unclear)} not compared"))
    return 0


if __name__ == "__main__":
    sys.exit(main())
