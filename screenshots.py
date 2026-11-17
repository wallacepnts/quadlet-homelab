#!/usr/bin/env python3
"""Finds screenshots in each project's own README and, only on `--apply`, saves them.

The rule: **only what the project itself hosts**. A picture counts when the README of the app's
`source` repository points at it and it lives in that repository (raw.githubusercontent.com/<owner>/<repo>,
github.com/<owner>/<repo>/raw|blob) or in GitHub's own upload store (github.com/user-attachments, which is
where a README's drag-and-dropped pictures go). Third-party hosts, badges and logos are left out, and so is
another store's gallery (Umbrel's repository declares no licence).

Every candidate is downloaded and checked: status 200, an `image/png|jpeg|webp|gif` content type, the size
limit the store enforces, and not so small it is an icon. Without `--apply` nothing is written.

    python3 screenshots.py                 # dry run: what would be saved, for apps with no screenshots
    python3 screenshots.py --app memos     # one app, even when it already has some
    python3 screenshots.py --apply         # save them as apps/<app>/screenshots/1.png ...
    python3 screenshots.py --selftest      # the parsing, no network

No dependencies: stdlib only.
"""

import argparse
import re
import sys
import urllib.error
import urllib.parse
import urllib.request
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path, PurePosixPath

import manifest

ROOT = Path(__file__).resolve().parent
APPS = ROOT / "apps"
UA = "quadlet-homelab-screenshots"
MIN_BYTES = 30 * 1024
TYPES = {"image/png": ".png", "image/jpeg": ".jpg", "image/webp": ".webp", "image/gif": ".gif"}
SKIP_NAME = re.compile(r"logo|icon|badge|favicon|sponsor|avatar|banner|button|shield|star-history|contributor|get-it-on|fdroid"
                       r"|play-store|app-store|architecture|diagram|steam_|geohash|curl|GApps|README\.gif", re.I)
README_NAMES = ("README.md", "readme.md", "Readme.md", "README.markdown", "README.MD")


def github_repo(source):
    """(owner, repo) of an https://github.com/<owner>/<repo> address, or None."""
    m = re.fullmatch(r"https://github\.com/([A-Za-z0-9_.-]+)/([A-Za-z0-9_.-]+?)(?:\.git)?/?", source or "")
    return (m.group(1), m.group(2)) if m else None


def image_refs(text):
    """The image addresses a markdown/HTML README names, in order, without repeats."""
    achado = re.finditer(r"""!\[[^\]]*\]\(\s*<?([^)\s>]+)|<img\b[^>]*?\bsrc\s*=\s*["']([^"']+)["']""", text, re.I)
    refs = [m.group(1) or m.group(2) for m in achado]
    return list(dict.fromkeys(refs))


def resolve(ref, owner, repo):
    """The raw address of a README reference when the project itself hosts it, else None."""
    ref = ref.strip()
    if ref.startswith("//"):
        ref = "https:" + ref
    if not re.match(r"[a-z]+://", ref):
        path = re.sub(r"^(\./|/)+", "", ref.split("?")[0].split("#")[0])
        return f"https://raw.githubusercontent.com/{owner}/{repo}/HEAD/{path}"
    u = urllib.parse.urlparse(ref)
    mine = f"/{owner}/{repo}/".lower()
    if u.scheme != "https":
        return None
    if u.netloc == "raw.githubusercontent.com" and u.path.lower().startswith(mine):
        return ref.split("#")[0]
    if u.netloc == "github.com":
        if u.path.lower().startswith(mine) and re.match(r"/[^/]+/[^/]+/(raw|blob)/", u.path):
            rest = re.sub(r"^/[^/]+/[^/]+/(?:raw|blob)/", "", u.path)
            return f"https://raw.githubusercontent.com/{owner}/{repo}/{rest}"
        if u.path.startswith("/user-attachments/assets/"):
            return ref.split("#")[0]
    if u.netloc == "user-images.githubusercontent.com":
        return ref.split("#")[0]
    return None


def fetch(url, limite=None, text=False):
    """(status, content type, bytes) with at most `limite`+1 bytes read; (None, None, b"") on a network error."""
    try:
        with urllib.request.urlopen(urllib.request.Request(url, headers={"User-Agent": UA}), timeout=25) as f:
            dados = f.read(limite + 1) if limite else f.read()
            return f.status, (f.headers.get("Content-Type") or "").split(";")[0].strip().lower(), dados
    except urllib.error.HTTPError as e:
        return e.code, None, b""
    except (urllib.error.URLError, TimeoutError, OSError):
        return None, None, b""


def readme(owner, repo):
    for nome in README_NAMES:
        st, _, dados = fetch(f"https://raw.githubusercontent.com/{owner}/{repo}/HEAD/{nome}")
        if st == 200:
            return dados.decode("utf-8", "replace")
    return None


def candidates(owner, repo, text, maximo=manifest.SHOT_COUNT):
    """[(url, bytes, extension)] verified, at most `maximo`."""
    saida = []
    for ref in image_refs(text):
        url = resolve(ref, owner, repo)
        if not url or SKIP_NAME.search(urllib.parse.urlparse(url).path):
            continue
        st, tipo, dados = fetch(url, manifest.SHOT_MAX)
        if st != 200 or tipo not in TYPES or not (MIN_BYTES <= len(dados) <= manifest.SHOT_MAX):
            continue
        saida.append((url, dados, TYPES[tipo]))
        if len(saida) == maximo:
            break
    return saida


def work(app, force):
    m = manifest.load(APPS / app)
    repo = github_repo(m.get("source"))
    folder = APPS / app / "screenshots"
    if not repo:
        return app, None, "no GitHub source"
    if manifest.screenshot_files(APPS / app) and not force:
        return app, None, "already has screenshots"
    texto = readme(*repo)
    if texto is None:
        return app, None, "no README found"
    achados = candidates(*repo, texto)
    return app, achados, None if achados else "no verifiable image"


def save(app, achados):
    folder = APPS / app / "screenshots"
    folder.mkdir(exist_ok=True)
    for old in folder.iterdir():
        old.unlink()
    for i, (_, dados, ext) in enumerate(achados, 1):
        (folder / f"{i}{ext}").write_bytes(dados)


def selftest():
    assert github_repo("https://github.com/o/r") == ("o", "r") and github_repo("https://gitlab.com/o/r") is None
    t = '![a](docs/a.png) <img src="https://x.io/b.png"> ![c](https://github.com/o/r/blob/main/s/c.png?raw=true) ![a](docs/a.png)'
    assert image_refs(t) == ["docs/a.png", "https://x.io/b.png", "https://github.com/o/r/blob/main/s/c.png?raw=true"]
    assert resolve("docs/a.png", "o", "r") == "https://raw.githubusercontent.com/o/r/HEAD/docs/a.png"
    assert resolve("./docs/a.png", "o", "r") == "https://raw.githubusercontent.com/o/r/HEAD/docs/a.png"
    assert resolve("https://x.io/b.png", "o", "r") is None, "a third-party host is not the project's"
    assert resolve("https://github.com/o/r/blob/main/s/c.png?raw=true", "o", "r") == "https://raw.githubusercontent.com/o/r/main/s/c.png"
    assert resolve("https://github.com/other/r/blob/main/c.png", "o", "r") is None
    assert resolve("https://raw.githubusercontent.com/o/r/main/c.png", "o", "r") == "https://raw.githubusercontent.com/o/r/main/c.png"
    assert resolve("https://github.com/user-attachments/assets/abc", "o", "r").endswith("/abc")
    assert resolve("http://github.com/user-attachments/assets/abc", "o", "r") is None
    assert resolve("https://img.shields.io/badge/x.svg", "o", "r") is None
    assert SKIP_NAME.search("project-logo.png") and not SKIP_NAME.search("dashboard.png")
    print("screenshots selftest: ok")


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("--app", action="append", help="only this app (repeatable); replaces its screenshots")
    ap.add_argument("--apply", action="store_true", help="save what was verified (default: only show)")
    ap.add_argument("--selftest", action="store_true")
    a = ap.parse_args()
    if a.selftest:
        return selftest()
    apps = a.app or sorted(p.name for p in APPS.iterdir() if (p / "app.json").is_file())
    with ThreadPoolExecutor(8) as ex:
        feitos = list(ex.map(lambda x: work(x, bool(a.app)), apps))
    achou = 0
    for app, achados, motivo in feitos:
        if achados:
            achou += 1
            print(f"{app}: {len(achados)} image(s)")
            for url, dados, _ in achados:
                print(f"    {len(dados) // 1024:>5} KB  {url}")
            if a.apply:
                save(app, achados)
        elif a.app:
            print(f"{app}: {motivo}")
    print(f"\n{achou} app(s) with verified screenshots" + (" — saved" if a.apply else " — dry run, nothing written (--apply to save)"))


if __name__ == "__main__":
    main()
