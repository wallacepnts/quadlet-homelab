#!/usr/bin/env python3
"""The image version a unit runs, kept on the host and not in the repository.

A unit in this repository says which image it wants and nothing about the version:

    Image=docker.io/neosmemo/memos

`app.json` says what a tag of that image looks like, once:

    [image]
    memos = {version}            # 0.31.0   (`v{version}`, `{version}-alpine`, `{version:2}`...)

and `qh` fills the template with the latest release when it installs (or updates with `--latest`),
writing the result where only this host sees it, a Quadlet drop-in beside the unit:

    ~/.config/containers/systemd/memos.container.d/10-image.conf
        [Container]
        Image=docker.io/neosmemo/memos:0.31.0

The repository never needs a version bump, and the host still runs a pinned, known tag: rolling
back is writing the drop-in again (the one it replaced is kept in a `# was:` comment).

Only the units whose version is a GitHub release (`[upstream] unit = owner/repo`) can be done this
way. A sidecar pinned to what its app's compose validates, or an image pinned by digest, keeps its
tag in the unit.

    python3 imagepin.py --selftest
"""

import json
import os
import re
import sys
from pathlib import Path

from qhui import directives_of, valid_template

DROPIN = "10-image.conf"
TOKEN = re.compile(r"\{version(?::(\d+))?\}")
DOTTED = re.compile(r"\d+(?:\.\d+)+")


# -- the template ------------------------------------------------------------------------------

def template_from_tag(tag):
    """`v0.107.78` -> `v{version}`, `1.31.1-alpine` -> `{version}-alpine`; None when it has no shape to keep.

    `{version}` is three numbers, `{version:N}` another count. A tag carrying other digits around the
    version (a date, a build, `-php8.2`) has a shape a release name cannot fill in, and stays pinned."""
    m = DOTTED.search(tag or "")
    if not m:
        return None
    if re.search(r"\d", tag[:m.start()] + tag[m.end():]):
        return None
    n = m.group().count(".") + 1
    return tag[:m.start()] + ("{version}" if n == 3 else f"{{version:{n}}}") + tag[m.end():]


def count_of(template):
    m = TOKEN.search(template)
    return int(m.group(1) or 3) if m else 3


def fill(template, release):
    """The tag for a release name (`v2.13.1`, `n8n@2.38.7`, `2.6.5.5623-ls161`): its version, cut to N numbers."""
    m, v = TOKEN.search(template), DOTTED.search(release or "")
    if not m or not v:
        return None
    cortada = ".".join(v.group().split(".")[:count_of(template)])
    return template[:m.start()] + cortada + template[m.end():]


def synthetic(template):
    """A tag of this shape at version zero: what `updates.target_tags` swaps the release into."""
    return TOKEN.sub(".".join(["0"] * count_of(template)), template, count=1)


def templates(ini):
    """{unit: template} from `[image]` in an app.json (a parsed ConfigParser)."""
    return dict(ini.items("image")) if ini.has_section("image") else {}


# -- the image reference -----------------------------------------------------------------------

def image_repo(image):
    """The reference without its tag or digest: `docker.io/a/b:1@sha256:x` -> `docker.io/a/b`."""
    ref = image.partition("@")[0]
    return ref.rpartition(":")[0] if ":" in ref.rpartition("/")[2] else ref


def tag_of(image):
    ref = image.partition("@")[0]
    return ref.rpartition(":")[2] if ":" in ref.rpartition("/")[2] else ""


# -- the drop-in on the host -------------------------------------------------------------------

def dropin_path(unit_path):
    p = Path(unit_path)
    return p.parent / (p.name + ".d") / DROPIN


def read_pin(unit_path):
    """{"image": ..., "was": ... or None} from the host's drop-in, or None when there is none."""
    p = dropin_path(unit_path)
    if not p.is_file():
        return None
    texto = p.read_text()
    m = re.search(r"(?m)^Image=(.+)$", texto)
    if not m:
        return None
    anterior = re.search(r"(?m)^# was: (.+)$", texto)
    return {"image": m.group(1).strip(), "was": anterior.group(1).strip() if anterior else None}


def write_pin(unit_path, image, was=None):
    p = dropin_path(unit_path)
    p.parent.mkdir(parents=True, exist_ok=True)
    corpo = ("# Written by qh: the version this host runs. `qh <app> --update --latest` moves it;\n"
             "# to go back, put the tag you want in Image= below.\n"
             f"[Container]\nImage={image}\n" + (f"# was: {was}\n" if was else ""))
    tmp = p.with_name(p.name + ".tmp")
    tmp.write_text(corpo)
    tmp.replace(p)


def remove_pin(unit_path):
    p = dropin_path(unit_path)
    if p.is_file():
        p.unlink()
    try:
        p.parent.rmdir()          # another drop-in there is not ours to remove
    except OSError:
        pass


def effective_image(unit_path):
    """What the unit on the host really runs: the drop-in's Image=, else the unit's own."""
    pin = read_pin(unit_path)
    if pin:
        return pin["image"]
    return next((v for k, v in directives_of(Path(unit_path)) if k == "Image"), "")


# -- finding the latest ------------------------------------------------------------------------

def latest(unit, repo_image, template, override=None):
    """(tag, release, why): the newest tag of this shape that exists, the release it came from, or why not.

    `tag` is None when there is nothing to take: no release, or one whose image is not published yet.
    QH_FAKE_LATEST='{"memos": "v0.32.0"}' stands in for the network, for the tests."""
    fake = os.environ.get("QH_FAKE_LATEST")
    if fake:
        release = json.loads(fake).get(unit)
        tag = fill(template, release) if release else None
        return tag, release, None if tag else "no release"
    import updates as U
    repo = U.github_repo(repo_image, override)
    if not repo:
        return None, None, "no GitHub repository: declare it in [upstream]"
    release = U.latest_release(repo)
    if not release:
        return None, None, f"{repo}: no published release"
    candidatos = U.target_tags(synthetic(template), release)
    for alvo in candidatos:
        existe = U.registry_has(repo_image, alvo)
        if existe or existe is None:               # None: the check itself failed; take it at face value
            return alvo, release, None
    return None, release, f"released ({release}), image not published yet"


# -- selftest ----------------------------------------------------------------------------------

def selftest():
    assert template_from_tag("0.31.0") == "{version}" and template_from_tag("v0.107.78") == "v{version}"
    assert template_from_tag("1.31.1-alpine") == "{version}-alpine" and template_from_tag("version-5.0.4") == "version-{version}"
    assert template_from_tag("26.04") == "{version:2}" and template_from_tag("2026.8.2.1") == "{version:4}"
    assert template_from_tag("1.5.0-2026-07-17") is None and template_from_tag("0.10.1-php8.2") is None
    assert template_from_tag("latest") is None and template_from_tag("16") is None
    assert valid_template("v{version}-alpine") and valid_template("{version:2}")
    assert not valid_template("1.2.3") and not valid_template("{version}{version}") and not valid_template("{ver}")
    assert fill("{version}", "v0.31.1") == "0.31.1" and fill("v{version}", "v2.13.1") == "v2.13.1"
    assert fill("{version}", "2.6.5.5623-ls161") == "2.6.5", "cut to three numbers, as the tag we had"
    assert fill("{version:4}", "n8n@2.38.7") == "2.38.7", "a release with fewer numbers is taken as it is"
    assert fill("{version}-alpine", "1.31.1") == "1.31.1-alpine" and fill("{version}", "nightly") is None
    assert synthetic("v{version}-alpine") == "v0.0.0-alpine" and synthetic("{version:2}") == "0.0"
    assert image_repo("docker.io/a/b:1.2@sha256:ff") == "docker.io/a/b" and image_repo("docker.io/a/b") == "docker.io/a/b"
    assert image_repo("localhost:5000/x") == "localhost:5000/x" and tag_of("a/b:1.2") == "1.2" and tag_of("a/b") == ""
    import tempfile
    with tempfile.TemporaryDirectory() as d:
        unit = Path(d, "app.container")
        unit.write_text("[Container]\nImage=docker.io/o/app\n")
        assert read_pin(unit) is None and effective_image(unit) == "docker.io/o/app"
        write_pin(unit, "docker.io/o/app:1.0.0")
        assert read_pin(unit) == {"image": "docker.io/o/app:1.0.0", "was": None}
        write_pin(unit, "docker.io/o/app:1.1.0", was="1.0.0")
        assert read_pin(unit) == {"image": "docker.io/o/app:1.1.0", "was": "1.0.0"}
        assert effective_image(unit) == "docker.io/o/app:1.1.0"
        remove_pin(unit)
        assert read_pin(unit) is None and not Path(d, "app.container.d").exists()
        os.environ["QH_FAKE_LATEST"] = '{"app": "v2.0.1"}'
        try:
            assert latest("app", "docker.io/o/app", "v{version}") == ("v2.0.1", "v2.0.1", None)
            assert latest("other", "docker.io/o/other", "{version}")[0] is None
        finally:
            del os.environ["QH_FAKE_LATEST"]
    print("imagepin selftest: ok")
    return 0


if __name__ == "__main__":
    if "--selftest" not in sys.argv:
        print("usage: imagepin.py --selftest", file=sys.stderr)
        raise SystemExit(2)
    sys.exit(selftest())
