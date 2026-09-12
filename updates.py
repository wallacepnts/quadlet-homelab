#!/usr/bin/env python3
"""Compares the `Image=` tags in this repository with the latest GitHub release.

The rule this script exists to automate: **the source of truth is the
project's GitHub releases page, not the registry's tag list**. Registries list
betas, RCs and build variants that sort as "newer" without being releases —
n8n keeps 2.38.x and 2.39.x in parallel and marks 2.38 as latest, publishing
both on the same day; nginx, AdGuard, Memos and Frigate publish RCs alongside
the stable tags.

That is why the lookup follows the redirect of
`github.com/<org>/<repo>/releases/latest`, which returns the tag without
spending API rate limit.

    python3 updates.py           # table of what is behind
    python3 updates.py --all     # include what is up to date
    python3 updates.py --selftest  # test the parsing, no network
    python3 updates.py --bump --apply   # take it, in the unit and the docs

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

import qhui
from qhui import (translator, directives, directives_of, ref_parts, FLOATING,
                  red, yellow, green, dim)

PT = {
    "also show what is up to date": "mostra também o que está em dia",
    "test the parsing, no network": "testa o parsing, sem rede",
    "OUTDATED (": "DESATUALIZADOS (",
    "PINNED IMAGE IS GONE (": "IMAGEM FIXADA SUMIU (",
    "no longer pullable": "não baixa mais",
    "MAJOR — read the release notes first (": "MAJOR — leia as notas da release antes (",
    "  take them with --bump --major, one at a time":
        "  pegue com --bump --major, um de cada vez",
    "BUMP (": "SUBIR (",
    "nothing to bump.": "nada a subir.",
    "file(s) rewritten": "arquivo(s) reescrito(s)",
    "  check it with:  python3 check.py": "  confira com:  python3 check.py",
    "Image= did not match — left alone": "Image= não bateu — deixado como está",
    "nothing was done. repeat with --apply": "nada foi feito. repita com --apply",
    "rewrite Image= and every doc that mirrors it (without --apply, only show)":
        "reescreve o Image= e todo doc que o espelha (sem --apply, só mostra)",
    "execute (without it, only show)": "executa (sem ele, só mostra)",
    "with --bump: include the major bumps it refuses by default":
        "com --bump: inclui os majors que ele recusa por padrão",
    "gone from the registry": "sumiram do registry",
    "floating tag, moved since your pull (": "tag flutuante, mudou desde o seu pull (",
    "new digest": "digest novo",
    "same digest": "mesmo digest",
    "released, image not published yet (": "lançado, imagem ainda não publicada (",
    "cannot compare (": "sem comparação (",
    "up to date:": "em dia:",
    "images:": "imagens:",
    "outdated,": "desatualizadas,",
    "up to date,": "em dia,",
    "with a floating tag,": "com tag flutuante,",
    'waiting for the image': 'aguardando a imagem',
    'on a floating tag': 'com tag flutuante',
    'all up to date': 'tudo em dia',
    'images': 'imagens',
    'outdated': 'desatualizadas',
    'up to date': 'em dia',
    'not compared': 'não comparadas',

}
loc = translator(PT)

# The docstring `--help` opens with, in Portuguese.
AJUDA_PT = """Compara as tags `Image=` deste repositório com a última release no GitHub.

A regra que este script existe pra automatizar: **a fonte é a página de
releases do projeto no GitHub, não a lista de tags do registry**. Registry
lista beta, RC e variante de build que ordenam como "mais novo" sem serem
release — o n8n mantém a 2.38.x e a 2.39.x em paralelo e marca a 2.38 como
latest, publicando as duas no mesmo dia; nginx, AdGuard, Memos e Frigate
publicam RC junto das estáveis.

Por isso a consulta segue o redirect de
`github.com/<org>/<repo>/releases/latest`, que devolve a tag sem gastar rate
limit da API.

    python3 updates.py           # tabela do que está atrasado
    python3 updates.py --all     # inclui o que está em dia
    python3 updates.py --selftest  # testa o parsing, sem rede
    python3 updates.py --bump --apply   # pega, na unit e nos docs

Sem dependências: só a stdlib. Sai 0 mesmo com serviço desatualizado — estar
atrás é informação, não defeito; só erro de execução reprova.
"""




UA = "quadlet-homelab updates.py"

RAIZ = Path(__file__).resolve().parent
APPS = RAIZ / "apps"

# A tag that is not a version: there is nothing to compare between runs.




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


def registry_stable(image, tag):
    """The numbered tag `latest` points at, which is the released one.

    Fedora publishes the stable release, the branched one and rawhide side by
    side, all numbered: `46` and `rawhide` are the same digest, `45` says
    `Prerelease` inside, and `latest` is `44`. Taking the highest number — what
    `registry` does — recommends rawhide every month, and had this repository
    pinned to a prerelease for five weeks without anyone writing it down.

    Matching by digest and not by name because `latest` is a pointer: the thing
    to compare against is whichever numbered tag it currently resolves to.
    """
    h = _manifest_head(image, "latest")
    alvo = (h or {}).get("Docker-Content-Digest")
    if not alvo:
        return None
    forma = re.sub(r"\d+", r"\\d+", re.escape(tag))
    candidatos = [x for x in (registry_tags(image) or []) if re.fullmatch(forma, x)]
    # Newest first, so the usual case answers on the first request.
    for cand in sorted(candidatos, key=lambda x: [int(v) for v in re.findall(r"\d+", x)],
                       reverse=True)[:12]:
        outro = _manifest_head(image, cand)
        if outro and outro.get("Docker-Content-Digest") == alvo:
            return cand
    return None


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


def image_name(image):
    """The last path segment of a reference, without its tag or digest.

    `docker.io/valkey/valkey:9@sha256:70739f…` and `valkey/valkey@sha256:70739f…`
    are both `valkey`: the tag is optional, and splitting on the last colon
    without checking swallows the whole path when there is none.
    """
    ultimo = image.partition("@")[0].rpartition("/")[2]
    return ultimo.rpartition(":")[0] if ":" in ultimo else ultimo




def compose_image(spec, ref, image):
    """The whole reference this image carries in the app's own compose, at `ref`.

    The reference and not just the tag, because a sidecar pinned by digest says
    nothing in its tag — see ref_parts.

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
    nome = image_name(image)
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
            if image_name(cand) == nome:
                return cand
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


def target_tags(tag, remote):
    """The tags that could carry `remote`, best guess first.

    A release name is not a tag. Around the version each side puts its own
    decoration, and they rarely agree: we pin `v0.107.78`, `version-5.0.4` or
    `1.5.1-stable` while the release is called `v0.107.79`, `5.1.3-ls273`,
    `version/2026.8.2` or `n8n@2.38.7`.

    So the first guess keeps *our* tag's shape and swaps only the version
    inside it — that is the tag this repository would pin next. The release
    name itself comes after, for the case the shape carries something the
    version does not, such as the date in any-sync-bundle's
    `1.5.0-2026-07-17`.
    """
    aqui, la = (re.search(r"\d+(?:\.\d+)+", s) for s in (tag, remote))
    saida = []
    if aqui and la:
        saida.append(tag[:aqui.start()] + la.group() + tag[aqui.end():])
    saida.append(remote)
    if remote[:1] == "v" and remote[1:2].isdigit():
        saida.append(remote[1:])
    return list(dict.fromkeys(saida))


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
            img = next((v for k, v in directives_of(principal) if k == "Image"), "")
            ref = img.split("@")[0].rpartition(":")[2]
        for cont in conts:
            for key, value in directives_of(cont):
                if key == "Image":
                    yield folder.name, cont.stem, value, overrides.get(cont.stem), ref


def check(item):
    app, unit, image, override, ref = item
    tag = image.split("@")[0].rpartition(":")[2]

    # Before asking whether something newer exists, ask whether what is pinned
    # still does. Nothing used to: the newer tag was checked in the registry and
    # the current one never was, so an image that stopped being servable read as
    # "up to date" forever. Two got there by different roads — the Zenika chrome
    # karakeep used was withdrawn, and the arch-toolbox digest was collected out
    # from under a rolling image. Both keep running from the local copy, and
    # both fail the next install with nothing having warned.
    marca, digest = ref_parts(image)
    if registry_has(image, digest or marca or "latest") is False:
        return (unit, image, tag, "no longer pullable", "GONE")

    if override and override.startswith("registry"):
        # For an image that does not version by GitHub release — a distro tag,
        # a project that only publishes git tags, an image versioned apart from
        # its repository — the registry is the only source that knows.
        _, _, padrao = override.partition(":")
        # `registry:latest` asks which numbered tag `latest` resolves to, for a
        # project that publishes its prereleases under numbers too.
        there = (registry_stable(image, tag) if padrao == "latest"
                 else registry_newest(image, tag, padrao or None))
        if not there:
            return (unit, image, tag, "?", "registry: no comparable tag")
        n = lambda x: tuple(int(v) for v in re.findall(r"\d+", x))
        if n(there) > n(tag):
            return (unit, image, tag, there, "BEHIND")
        return (unit, image, tag, there, "up to date")

    if override and override.startswith("compose:"):
        la = compose_image(override, ref, image)
        if not la:
            return (unit, image, tag, "?", "compose: image not found there")
        there, digest_la = ref_parts(la)
        digest_aqui = ref_parts(image)[1]
        if digest_la and digest_aqui:
            # Both sides pin by digest, and then the tag carries nothing: the
            # valkey in immich's compose read `9` in 3.1.0 and `9` in 3.2.0
            # while the image under it changed. Comparing tags called that up
            # to date, and the rebuild only surfaced by reading the compose.
            if digest_la != digest_aqui:
                return (unit, image, f"{tag}@{digest_aqui[7:15]}…",
                        f"{there or tag}@{digest_la}", "BEHIND")
            return (unit, image, tag, "same digest", "up to date")
        if there in FLOATING:
            # The app does not pin it either: following the compose says
            # nothing, and calling that "up to date" would be a false comfort.
            return (unit, image, tag, there, "compose: not pinned there")
        if there.isdigit() and not version(tag):
            return (unit, image, tag, there, "floating tag")
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
            return (unit, image, tag, "new digest", "MOVED")
        if m is False:
            return (unit, image, tag, "same digest", "up to date")
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
        # shape (`v`, `version-`, `-alpine`, `-stable`). Check that the tag
        # exists before calling it available: a release can land hours before
        # the image does.
        alvos = target_tags(tag, remote)
        for alvo in alvos:
            existe = registry_has(image, alvo)
            # `None` is the check itself failing: reporting "not published" on
            # a network error would cry wolf. Take the tag at face value.
            if existe or existe is None:
                return (unit, image, tag, alvo, "BEHIND")
        return (unit, image, tag, alvos[0], "released, not published yet")
    return (unit, image, tag, remote, "up to date")


def selftest():
    """The reference parsing, which is where this script gets things wrong.

    Everything here is pure, so it runs in CI beside check.py's — the network
    half cannot be tested there and is not the half that has broken.
    """
    assert image_name("docker.io/valkey/valkey:9@sha256:" + "a" * 64) == "valkey"
    assert image_name("docker.io/valkey/valkey@sha256:" + "a" * 64) == "valkey"
    assert image_name("ghcr.io/immich-app/immich-server:v3.2.0") == "immich-server"
    assert image_name("registry.local:5000/foo/bar:1") == "bar", "the port is not a tag"
    assert image_name("nginx") == "nginx"

    assert ref_parts("a/b:9@sha256:" + "c" * 64) == ("9", "sha256:" + "c" * 64)
    assert ref_parts("a/b@sha256:" + "c" * 64) == ("", "sha256:" + "c" * 64)
    assert ref_parts("ghcr.io/a/b:v1.2.3") == ("v1.2.3", "")
    assert ref_parts("registry.local:5000/foo/bar") == ("", ""), "the port is not a tag"

    # A release name is not a tag: keep our own shape and swap the version.
    assert target_tags("v0.107.78", "v0.107.79")[0] == "v0.107.79"
    assert target_tags("version-5.0.4", "5.1.3-ls273")[0] == "version-5.1.3"
    assert target_tags("1.29.1-alpine", "1.30.0")[0] == "1.30.0-alpine"
    assert target_tags("2026.5.6", "version/2026.8.2")[0] == "2026.8.2"
    assert target_tags("2.33.7", "n8n@2.38.7")[0] == "2.38.7"
    # any-sync-bundle carries a date the version does not: the release name itself.
    assert "1.6.0-2026-08-18" in target_tags("1.5.0-2026-07-17", "v1.6.0-2026-08-18")

    # The pinned image's own liveness, which is asked before "is there a newer
    # one": both halves of a reference have to be checkable.
    assert ref_parts("quay.io/toolbx/arch-toolbox@sha256:" + "3" * 64)[1] == \
        "sha256:" + "3" * 64, "a digest-pinned image is checked by its digest"
    assert ref_parts("gcr.io/zenika-hub/alpine-chrome:124")[0] == "124"
    for chave in ("no longer pullable", "new digest", "same digest"):
        assert chave in PT, f"{chave} is printed in the table and must translate"

    # What --bump refuses on its own. A version is chosen, not received.
    assert major("1.37.1", "2.0.0"), "a first number that changes is never mechanical"
    assert not major("1.37.1", "1.37.2")
    assert not major("v11.0.0", "v11.0.1")
    assert major("44", "46"), "a bare number is a version too (fedora-toolbox)"
    assert not major("9", "9"), "a digest moving under the same tag is not a major"
    assert not major("2026.8.1", "2026.9.2"), \
        "a calendar version has no major — the filter cannot catch that one"

    # The reference `--bump` writes, for both shapes the comparison produces.
    import tempfile as _tf
    with _tf.TemporaryDirectory() as d:
        u = Path(d) / "x.container"
        u.write_text("[Container]\nImage=ghcr.io/a/b:v1.0.0\n")
        assert escrever_imagem(u, "ghcr.io/a/b:v1.0.0", "v1.0.1") == "ghcr.io/a/b:v1.0.1"
        assert "Image=ghcr.io/a/b:v1.0.1" in u.read_text()
        # a sidecar the app's compose pins by digest
        velha = "docker.io/valkey/valkey:9@sha256:" + "a" * 64
        u.write_text(f"[Container]\nImage={velha}\n")
        nova = escrever_imagem(u, velha, "9@sha256:" + "b" * 64)
        assert nova == "docker.io/valkey/valkey:9@sha256:" + "b" * 64, nova
        # a reference that is not there is left alone rather than guessed at
        assert escrever_imagem(u, "ghcr.io/nao/existe:1", "2") is None

    # `registry:latest` builds the shape to look for from our own tag, so it
    # compares `44` against other bare numbers and never against `rawhide`.
    forma = lambda tag: re.sub(r"\d+", r"\\d+", re.escape(tag))
    import re as _re
    assert _re.fullmatch(forma("44"), "46") and not _re.fullmatch(forma("44"), "rawhide")
    assert _re.fullmatch(forma("26.04"), "25.10")
    assert not _re.fullmatch(forma("26.04"), "latest")

    assert version("1.30.0-alpine") == (1, 30, 0)
    assert version("release") is None, "a name with no digits has no version"
    assert "release" in FLOATING, "karakeep's chrome is pinned at `release` upstream"

    print("selftest: ok")


FIXADO = re.compile(r"^(?:Pinned to|Fixado em|Pinado em) ((?:`[^`]+`(?:, )?)+)")
LINHA_UNIT = re.compile(r"^(\| <img.*\]\(\./docs/(?:pt-BR/)?([a-z0-9._-]+)\.md\).*\| `)([^`]+)(` \|)$")


def major(aqui, la):
    """True when the first number differs — the bump that is never mechanical.

    wud 9 exits at startup without an administrator that did not exist before;
    wger 2.7 converts old sessions with a timezone that has to be right BEFORE
    and cannot be changed after; jellyfin 12 wants a backup and a full library
    scan. Rule 9 of the conventions says a version is taken deliberately, and
    an updater that takes majors on its own is that rule written and ignored.

    A filter, not a guarantee. A calendar version has no major — home-assistant
    2026.8 to 2026.9 reads as a minor here and carried eight integrations with
    breaking changes. Reading the release notes is still the job; this only
    keeps the obvious ones from going through unread.
    """
    if aqui == la:
        return False                 # only the digest under the tag moved
    n = lambda s: [int(x) for x in re.findall(r"\d+", s)]
    a, b = n(aqui), n(la)
    return not (a and b) or a[0] != b[0]


def escrever_imagem(unit, atual, alvo):
    """Rewrites `Image=`, keeping the registry and repository, taking the rest.

    `alvo` is what the comparison produced: a tag (`v2.13.1`), or a tag with
    the digest under it (`9@sha256:...`), which is the shape a sidecar tracked
    by its app's own compose comes back with — immich's valkey kept reading `9`
    across two releases while the image under it changed. Replacing the whole
    reference is what makes that second shape work at all; substituting the tag
    could not see it.
    """
    repo = atual.partition("@")[0]
    if ":" in repo.rpartition("/")[2]:
        repo = repo.rpartition(":")[0]
    nova = f"{repo}:{alvo}"
    texto = unit.read_text()
    novo, n = re.subn(rf"^Image={re.escape(atual)}$", f"Image={nova}", texto, flags=re.M)
    if n != 1:
        return None
    unit.write_text(novo)
    return nova


def tags_de(pasta):
    """Every tag the folder's units pin, sorted and deduplicated.

    An image pinned by digest has no tag and the docs quote the bare hex, which
    is what immich's database and mdrop carry.
    """
    out = []
    for unit in sorted(pasta.glob("*.container")):
        for chave, valor in directives_of(unit):
            if chave == "Image":
                out.append(valor.partition("@sha256:")[2] or valor.rpartition(":")[2])
    return sorted(set(out))


def escrever_tabela(app, velha, nova):
    """Swaps one tag in the version tables of both root READMEs.

    Patched and not regenerated: the cell is prose in some rows — openwebui
    carries `v0.11.0` (Open WebUI) + `0.32.6` (Ollama), and rebuilding it from
    the units would keep the tags and lose the names.
    """
    mudados = []
    for doc, padrao in ((RAIZ / "README.md", f"(./apps/{app})"),
                        (RAIZ / "docs/pt-BR/README.md", f"(../../apps/{app}/README")):
        if not doc.exists():
            continue
        linhas = doc.read_text().splitlines(keepends=True)
        alvo = [i for i, l in enumerate(linhas) if padrao in l and f"`{velha}`" in l]
        if len(alvo) != 1:
            continue          # `—` for a stack with no single version, or already done
        linhas[alvo[0]] = linhas[alvo[0]].replace(f"`{velha}`", f"`{nova}`")
        doc.write_text("".join(linhas))
        mudados.append(f"{doc.relative_to(RAIZ)}:{alvo[0] + 1}")
    return mudados


def sincronizar_docs():
    """Rewrites every place that mirrors a tag, from the units themselves.

    The version lives in six: `Image=`, the two version tables, the `Pinned to`
    line of each service README in both languages, and — for a folder that
    documents each unit apart — that unit's page and the Version column that
    links to it. `check.py` fails on four of them, so this is what keeps a bump
    from having to be typed six times and remembered six times.

    Regenerated, not patched: it is derived data, and rebuilding it also
    settles whatever drifted before.
    """
    mudados = []
    for pasta in sorted(p for p in APPS.iterdir() if p.is_dir()):
        esperado = ", ".join(f"`{x}`" for x in tags_de(pasta))
        if not esperado:
            continue
        for doc in sorted(pasta.glob("README*.md")):
            linhas = doc.read_text().splitlines(keepends=True)
            for i, linha in enumerate(linhas):
                m = FIXADO.match(linha)
                if m and m.group(1) != esperado:
                    linhas[i] = linha[:m.start(1)] + esperado + linha[m.end(1):]
                    mudados.append(f"{doc.relative_to(RAIZ)}:{i + 1}")
            doc.write_text("".join(linhas))
        mudados += _sincronizar_por_unit(pasta)
    return mudados


def _sincronizar_por_unit(pasta):
    """The per-unit pages and Version column of a folder that has them.

    media-stack and vm document each unit on its own page; toolbx lists them in
    a table. Those are a seventh and eighth place, and the sweep that found
    them found 36 lines already stale.
    """
    mudados = []
    tags = {}
    for unit in sorted(pasta.glob("*.container")):
        for chave, valor in directives_of(unit):
            if chave == "Image":
                tags[unit.stem.replace(f"{pasta.name}-", "")] = (
                    valor.partition("@sha256:")[2] or valor.rpartition(":")[2])
    for doc in sorted(pasta.glob("docs/*.md")) + sorted(pasta.glob("docs/*/*.md")):
        alvo = tags.get(doc.stem)
        if not alvo:
            continue
        linhas = doc.read_text().splitlines(keepends=True)
        for i, linha in enumerate(linhas):
            m = FIXADO.match(linha)
            if m and m.group(1) != f"`{alvo}`":
                linhas[i] = linha[:m.start(1)] + f"`{alvo}`" + linha[m.end(1):]
                mudados.append(f"{doc.relative_to(RAIZ)}:{i + 1}")
        doc.write_text("".join(linhas))
    for doc in sorted(pasta.glob("README*.md")):
        linhas = doc.read_text().splitlines(keepends=True)
        for i, linha in enumerate(linhas):
            m = LINHA_UNIT.match(linha.rstrip("\n"))
            if not m:
                continue
            alvo = tags.get(m.group(2))
            # `digest` is deliberate where the image is pinned by one: sixty-four
            # hex characters in a table cell say less than the word.
            if not alvo or alvo == m.group(3) or (
                    m.group(3) == "digest" and re.fullmatch(r"[0-9a-f]{64}", alvo)):
                continue
            linhas[i] = m.group(1) + alvo + m.group(3) + "\n"
            mudados.append(f"{doc.relative_to(RAIZ)}:{i + 1}")
        doc.write_text("".join(linhas))
    return mudados


def bump(behind, items, apply, com_major):
    """Takes the versions that are behind, in the unit and in every doc.

    What it does NOT take is the point. Rule 9 of the conventions says a
    version is chosen, not received: a major can need a secret created before
    it starts (wud 9), a setting that has to be right before a migration and
    cannot be changed after (wger 2.7), or a backup and a full library scan
    (jellyfin 12). Those are listed and left, with the release page to read.
    """
    por_unit = {unit: (app, image) for (app, unit, image, _o, _r) in items}
    fazer, segurar = [], []
    for unit, imagem, _mostrado, la, _status in sorted(behind):
        # From the unit's real `Image=`, not from the column the table printed:
        # the digest case renders as `9@8e8d64b4…`, an ellipsis and all, which
        # is a thing to read and not a thing to write.
        tag_aqui = ref_parts(imagem)[0]
        tag_la = la.partition("@")[0]
        destino = (segurar if major(tag_aqui, tag_la) and not com_major else fazer)
        destino.append((unit, imagem, tag_aqui, la))

    if segurar:
        print("\n" + yellow(loc("MAJOR — read the release notes first (")
                            + f"{len(segurar)}):"))
        for unit, _img, aqui, la in segurar:
            print(f"  {unit:<28} {aqui:<24} -> {la}")
        print(dim(loc("  take them with --bump --major, one at a time")))
    if not fazer:
        print("\n" + loc("nothing to bump."))
        return 0

    print("\n" + (green if apply else yellow)(
        loc("BUMP (") + f"{len(fazer)}):" + ("" if apply else "  " + loc("(dry-run)"))))
    tocados = []
    for unit, imagem, aqui, la in fazer:
        app, _ = por_unit[unit]
        print(f"  {unit:<28} {aqui:<24} -> {la[:40]}")
        if not apply:
            continue
        caminho = APPS / app / f"{unit}.container"
        if not escrever_imagem(caminho, imagem, la):
            print(dim(f"     {loc('Image= did not match — left alone')}"))
            continue
        tocados.append(f"{caminho.relative_to(RAIZ)}")
        # The table cell carries the tag, never the digest under it.
        tocados += escrever_tabela(app, aqui, la.partition("@")[0])
    if not apply:
        print("\n" + loc("nothing was done. repeat with --apply"))
        return 0
    tocados += sincronizar_docs()
    print("\n" + green(loc("done:")) + f" {len(tocados)} " + loc("file(s) rewritten"))
    print(dim(loc("  check it with:  python3 check.py")))
    return 0


def main():
    qhui.argparse_ptbr()
    ap = argparse.ArgumentParser(description=AJUDA_PT if qhui.PTBR else __doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--all", action="store_true", help=loc("also show what is up to date"))
    ap.add_argument("--selftest", action="store_true", help=loc("test the parsing, no network"))
    ap.add_argument("--bump", action="store_true",
                    help=loc("rewrite Image= and every doc that mirrors it "
                             "(without --apply, only show)"))
    ap.add_argument("--apply", action="store_true", help=loc("execute (without it, only show)"))
    ap.add_argument("--major", action="store_true",
                    help=loc("with --bump: include the major bumps it refuses by default"))
    a = ap.parse_args()

    if a.selftest:
        selftest()
        return 0

    items = list(services())
    with ThreadPoolExecutor(max_workers=8) as pool:
        rows = list(pool.map(check, items))

    sumidas = [l for l in rows if l[4] == "GONE"]
    behind = [l for l in rows if l[4] == "BEHIND"]

    if a.bump:
        return bump(behind, items, a.apply, a.major)
    movidas = [l for l in rows if l[4] == "MOVED"]
    unclear = [l for l in rows if l[4].startswith(("unknown repo", "not comparable", "compose:"))
               or "no published release" in l[4]]
    pendente = [l for l in rows if l[4] == "released, not published yet"]

    def table(label, ls, cor=yellow):
        if not ls:
            return
        print("\n" + cor(loc(label)))
        for unit, _, here, there, _ in sorted(ls):
            print(f"  {unit:<28} {here:<24} -> {loc(there)}")

    table(f"PINNED IMAGE IS GONE ({len(sumidas)}):", sumidas, red)
    table(f"OUTDATED ({len(behind)}):", behind, red)
    table(f"released, image not published yet ({len(pendente)}):", pendente)
    table(f"floating tag, moved since your pull ({len(movidas)}):", movidas)
    # What could not be compared stays out of the way: it is a property of the
    # image's naming, not something to act on. --all brings it back.
    if a.all:
        table(f"cannot compare ({len(unclear)}):", unclear)
        table("up to date:", [l for l in rows if l[4] == "up to date"], green)

    # Zeros are not news. What is left is coloured by whether it asks anything
    # of you: red acts now, yellow waits, the rest is background.
    partes = []
    for n, rotulo, cor in (
            (len(sumidas), "gone from the registry", red),
            (len(behind), "outdated", red),
            (len(pendente), "waiting for the image", yellow),
            (sum(1 for l in rows if l[4] == "up to date"), "up to date", green),
            (sum(1 for l in rows if l[4] == "floating tag"), "on a floating tag", dim),
            (len(unclear), "not compared", dim)):
        if n:
            partes.append(cor(f"{n} {loc(rotulo)}"))
    cabeca = dim(loc(f"{len(rows)} images"))
    if not behind and not pendente and not sumidas:
        print(f"\n{cabeca} {dim('·')} {green(loc('all up to date'))}")
    else:
        print("\n" + f" {dim('·')} ".join([cabeca] + partes))
    return 0


if __name__ == "__main__":
    sys.exit(main())
