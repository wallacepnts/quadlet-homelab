#!/usr/bin/env python3
"""The host, as the store acts on it: what each app's data takes on disk, and restarting or shutting down on a schedule.

Both are small and both touch the machine, so every call that does goes through a `run` the tests replace.

- `usage`: bytes per directory. `podman unshare du` when podman is there, because the files a container wrote belong
  to a subuid and a plain `du` cannot read into them (it reports a part and complains). Without podman, plain `du`.
- `power_*`: a transient systemd user timer, `qh-power.timer`, that runs `systemctl reboot` or `poweroff` when it
  elapses. One at a time, cancellable, and the state is a small file beside the other store settings so the panel can
  say what is scheduled without parsing systemd's output. The same polkit rule that lets the logged-in user restart
  now lets the timer do it later.

    python3 hostctl.py --selftest
"""

import json
import os
import re
import shutil
import stat
import subprocess
import sys
import tempfile
import time
from pathlib import Path

UNIT = "qh-power"
VERBS = ("reboot", "poweroff")
MIN_DELAY, MAX_DELAY = 60, 7 * 24 * 3600        # a minute to a week: sooner is a mistake, later is forgotten


def _run(cmd, **kw):
    return subprocess.run(cmd, capture_output=True, text=True, timeout=kw.pop("timeout", 30), check=False, **kw)


# -- disk usage ------------------------------------------------------------------------------

def dir_bytes(path, run=_run, unshare=None):
    """The apparent size of `path` in bytes (0 when it is not there), counting what a container wrote."""
    if not Path(path).exists():
        return 0
    usar = shutil.which("podman") is not None if unshare is None else unshare
    cmd = (["podman", "unshare"] if usar else []) + ["du", "-sb", "--one-file-system", str(path)]
    r = run(cmd, timeout=300)
    m = re.match(r"(\d+)\s", r.stdout or "")
    return int(m.group(1)) if m else 0       # a partial answer (rc 1, some directories unreadable) still counts


def usage(roots_by_app, run=_run, unshare=None):
    """[{"app", "bytes"}] largest first: each app's volume directories added up. `roots_by_app` is {app: [paths]}."""
    saida = [{"app": app, "bytes": sum(dir_bytes(p, run, unshare) for p in roots)} for app, roots in roots_by_app.items()]
    return sorted(saida, key=lambda x: (-x["bytes"], x["app"]))


# -- scheduled restart / shutdown ------------------------------------------------------------

def state_file(base):
    return Path(base) / ".config/quadlet-homelab/power.json"


def _seconds_until(hhmm, now):
    """Seconds from `now` (epoch) to the next local HH:MM, today or tomorrow."""
    m = re.fullmatch(r"([01]?\d|2[0-3]):([0-5]\d)", hhmm or "")
    if not m:
        raise ValueError("time")
    t = time.localtime(now)
    alvo = time.mktime((t.tm_year, t.tm_mon, t.tm_mday, int(m.group(1)), int(m.group(2)), 0, 0, 0, -1))
    if alvo <= now + MIN_DELAY:
        alvo += 24 * 3600
    return int(alvo - now)


def delay_of(minutes=None, at=None, now=None):
    """Seconds to wait for `minutes` from now, or for the next HH:MM; ValueError when out of range."""
    now = time.time() if now is None else now
    if at:
        seg = _seconds_until(at, now)
    elif isinstance(minutes, int) and not isinstance(minutes, bool):
        seg = minutes * 60
    else:
        raise ValueError("when")
    if not MIN_DELAY <= seg <= MAX_DELAY:
        raise ValueError("range")
    return seg


def schedule(base, verb, seconds, run=_run, now=None):
    """Arm the timer, replacing one already armed. Returns the state written, or None when systemd refused."""
    if verb not in VERBS:
        raise ValueError("verb")
    now = time.time() if now is None else now
    cancel(base, run)
    r = run(["systemd-run", "--user", f"--unit={UNIT}", f"--on-active={seconds}s",
             f"--description=qh scheduled {verb}", "systemctl", verb])
    if r.returncode != 0:
        return None
    estado = {"action": verb, "at": int(now + seconds)}
    f = state_file(base)
    f.parent.mkdir(parents=True, exist_ok=True)
    f.write_text(json.dumps(estado) + "\n")
    return estado


def cancel(base, run=_run):
    run(["systemctl", "--user", "stop", f"{UNIT}.timer", f"{UNIT}.service"])
    state_file(base).unlink(missing_ok=True)


def state(base, run=_run, now=None):
    """{"action", "at"} while the timer is armed, else None (a file left by a timer that already fired is dropped)."""
    f = state_file(base)
    try:
        d = json.loads(f.read_text())
    except (OSError, ValueError):
        return None
    now = time.time() if now is None else now
    ativo = run(["systemctl", "--user", "is-active", f"{UNIT}.timer"]).stdout.strip() == "active"
    if d.get("action") in VERBS and isinstance(d.get("at"), int) and ativo and d["at"] > now - 5:
        return d
    f.unlink(missing_ok=True)
    return None


# -- files: look inside an app's folder -------------------------------------------------------

LIST_MAX = 2000                       # entries of one folder shown; a folder past this says so
PREVIEW_MAX = 256 * 1024              # bytes of a file shown as text in the browser


class FsError(Exception):
    """Why a path was refused or could not be read (`code` is what the API answers)."""

    def __init__(self, code, msg):
        super().__init__(msg)
        self.code = code


def confine(root, rel, final_link=False):
    """The real path of `rel` under `root`, or FsError. Never leaves the root, never follows a link.

    A container wrote what is in there and can put a symlink to /etc/passwd in it. Read as the user inside
    `podman unshare` (where the user is root over the subuid files), that link would be followed to the host's
    own files, so a link anywhere on the way is refused, not resolved."""
    raiz = os.path.realpath(root)
    atual = raiz
    partes = [p for p in (rel or "").split("/") if p and p != "."]
    for i, parte in enumerate(partes):
        if parte == ".." or "\0" in parte:
            raise FsError(400, "path")
        atual = os.path.join(atual, parte)
        if os.path.islink(atual) and not (final_link and i == len(partes) - 1):
            raise FsError(400, "link")
    real = os.path.realpath(atual) if not (final_link and os.path.islink(atual)) else atual
    if real != raiz and not real.startswith(raiz + os.sep):
        raise FsError(400, "outside")
    if not os.path.lexists(real):
        raise FsError(404, "missing")
    return real


def fs_list(root, rel):
    """{"entries": [{name, type, size, mtime}], "truncated"}: folders first, then files, each by name."""
    pasta = confine(root, rel)
    if not os.path.isdir(pasta):
        raise FsError(400, "not a folder")
    itens = []
    try:
        with os.scandir(pasta) as it:
            for e in it:
                try:
                    st = e.stat(follow_symlinks=False)
                except OSError:
                    continue
                tipo = "link" if e.is_symlink() else "dir" if e.is_dir(follow_symlinks=False) else "file"
                itens.append({"name": os.fsdecode(e.name).encode("utf-8", "replace").decode(), "type": tipo,
                              "size": st.st_size if tipo == "file" else None, "mtime": int(st.st_mtime)})
    except PermissionError:
        raise FsError(403, "denied")
    itens.sort(key=lambda x: (x["type"] != "dir", x["name"].lower()))
    return {"entries": itens[:LIST_MAX], "truncated": len(itens) > LIST_MAX}


def fs_open(root, rel):
    """(open binary file, size) for a regular file under `root`; FsError otherwise."""
    caminho = confine(root, rel)
    try:
        fd = os.open(caminho, os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK)
    except PermissionError:
        raise FsError(403, "denied")
    except OSError:
        raise FsError(400, "not a file")
    st = os.fstat(fd)
    if not stat.S_ISREG(st.st_mode):         # a fifo or a device would block or leak
        os.close(fd)
        raise FsError(400, "not a file")
    return os.fdopen(fd, "rb"), st.st_size


def fs_preview(root, rel):
    """{"text", "size", "truncated"} for a file that is UTF-8 text; FsError(415) for anything else."""
    f, tamanho = fs_open(root, rel)
    with f:
        dados = f.read(PREVIEW_MAX + 1)
    cortado = len(dados) > PREVIEW_MAX
    dados = dados[:PREVIEW_MAX]
    if b"\0" in dados:
        raise FsError(415, "binary")
    try:
        texto = dados.decode("utf-8")
    except UnicodeDecodeError as e:
        if cortado and e.start >= len(dados) - 3:           # a character cut at the edge is not a binary file
            texto = dados[:e.start].decode("utf-8")
        else:
            raise FsError(415, "binary")
    return {"text": texto, "size": tamanho, "truncated": cortado}


# -- files: change them ---------------------------------------------------------------------------
# Everything here runs in `podman unshare`, where the user is root over the files a container wrote. What is created
# takes the owner of the folder it lands in, so the app that owns the folder can read it back.

def clean_name(nome):
    if not isinstance(nome, str) or not nome or nome in (".", "..") or "/" in nome or "\0" in nome or len(nome.encode()) > 255:
        raise FsError(400, "name")
    return nome


def _adopt(caminho, ref):
    """Give `caminho` (and what is under it) the owner of the folder `ref`, links themselves and not their targets."""
    st = os.stat(ref)
    for atual, pastas, arquivos in os.walk(caminho):
        os.lchown(atual, st.st_uid, st.st_gid)
        for n in arquivos + [d for d in pastas if os.path.islink(os.path.join(atual, d))]:
            os.lchown(os.path.join(atual, n), st.st_uid, st.st_gid)
    if os.path.isfile(caminho) or os.path.islink(caminho):
        os.lchown(caminho, st.st_uid, st.st_gid)


def unique(pasta, nome):
    """`nome`, or `nome (1)`, `nome (2)`... when it is taken (before the extension: `a (1).txt`)."""
    if not os.path.lexists(os.path.join(pasta, nome)):
        return nome
    base, ext = os.path.splitext(nome) if not nome.startswith(".") or nome.count(".") > 1 else (nome, "")
    n = 1
    while os.path.lexists(os.path.join(pasta, f"{base} ({n}){ext}")):
        n += 1
    return f"{base} ({n}){ext}"


def fs_mkdir(root, rel, nome):
    pai = confine(root, rel)
    if not os.path.isdir(pai):
        raise FsError(400, "not a folder")
    destino = os.path.join(pai, clean_name(nome))
    if os.path.lexists(destino):
        raise FsError(409, "exists")
    os.mkdir(destino, 0o755)
    _adopt(destino, pai)
    return {"name": nome}


def fs_rename(root, rel, novo):
    if not (rel or "").strip("/"):
        raise FsError(400, "root")
    atual = confine(root, rel, final_link=True)
    destino = os.path.join(os.path.dirname(atual), clean_name(novo))
    if os.path.lexists(destino):
        raise FsError(409, "exists")
    os.rename(atual, destino)
    return {"name": novo}


def fs_delete(root, rel):
    if not (rel or "").strip("/"):
        raise FsError(400, "root")              # the volume itself is the app's, not a file
    alvo = confine(root, rel, final_link=True)
    if os.path.isdir(alvo) and not os.path.islink(alvo):
        shutil.rmtree(alvo)                     # rmtree removes a link inside; it never follows it
    else:
        os.unlink(alvo)
    return {}


def _transfer(root, rel, droot, drel, mover):
    if not (rel or "").strip("/"):
        raise FsError(400, "root")
    origem = confine(root, rel, final_link=True)
    pasta = confine(droot, drel)
    if not os.path.isdir(pasta):
        raise FsError(400, "not a folder")
    real_origem = os.path.realpath(origem) if not os.path.islink(origem) else origem
    if os.path.isdir(real_origem) and (pasta == real_origem or pasta.startswith(real_origem + os.sep)):
        raise FsError(400, "into itself")
    nome = unique(pasta, os.path.basename(origem))
    destino = os.path.join(pasta, nome)
    if mover:
        shutil.move(origem, destino)
    elif os.path.isdir(origem) and not os.path.islink(origem):
        shutil.copytree(origem, destino, symlinks=True)
    else:
        shutil.copy2(origem, destino, follow_symlinks=False)
    _adopt(destino, pasta)
    return {"name": nome}


def fs_copy(root, rel, droot, drel):
    return _transfer(root, rel, droot, drel, False)


def fs_move(root, rel, droot, drel):
    return _transfer(root, rel, droot, drel, True)


def fs_write(root, rel, nome, origem, overwrite=False, expected=None):
    """Write the bytes of `origem` (a binary file object) as `nome` in the folder `rel`; the name is kept unless it is
    taken and `overwrite` is off. A cut upload leaves nothing under the real name: with `expected` (the length the
    sender announced) a stream that ends short is a cut one, not a small file."""
    pasta = confine(root, rel)
    if not os.path.isdir(pasta):
        raise FsError(400, "not a folder")
    nome = clean_name(nome)
    final = nome if overwrite else unique(pasta, nome)
    destino = os.path.join(pasta, final)
    if overwrite and os.path.lexists(destino) and (os.path.islink(destino) or not os.path.isfile(destino)):
        raise FsError(400, "not a file")
    parte = os.path.join(pasta, f".{final}.qhpart")
    try:
        fd = os.open(parte, os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW, 0o644)
    except FileExistsError:
        raise FsError(409, "busy")
    except PermissionError:
        raise FsError(403, "denied")
    try:
        with os.fdopen(fd, "wb") as out:
            shutil.copyfileobj(origem, out, 1 << 20)
        if expected is not None and os.path.getsize(parte) != expected:
            raise FsError(400, "cut")
        _adopt(parte, pasta)
        os.replace(parte, destino)
    except BaseException:
        if os.path.lexists(parte):
            os.unlink(parte)
        raise
    return {"name": final}


def _cli(argv):
    """`hostctl.py fs-<op> ROOT REL ...`: what the store runs inside `podman unshare`."""
    op, raiz, rel = argv[0], argv[1], argv[2] if len(argv) > 2 else ""
    try:
        if op == "fs-ls":
            sys.stdout.write(json.dumps(fs_list(raiz, rel)))
        elif op == "fs-preview":
            sys.stdout.write(json.dumps(fs_preview(raiz, rel)))
        elif op == "fs-cat":
            f, _ = fs_open(raiz, rel)
            with f:
                shutil.copyfileobj(f, sys.stdout.buffer, 1 << 20)
        elif op in ("fs-mkdir", "fs-rename"):
            sys.stdout.write(json.dumps((fs_mkdir if op == "fs-mkdir" else fs_rename)(raiz, rel, argv[3])))
        elif op == "fs-delete":
            sys.stdout.write(json.dumps(fs_delete(raiz, rel)))
        elif op in ("fs-copy", "fs-move"):
            sys.stdout.write(json.dumps((fs_copy if op == "fs-copy" else fs_move)(raiz, rel, argv[3], argv[4])))
        elif op == "fs-write":
            sys.stdout.write(json.dumps(fs_write(raiz, rel, argv[3], sys.stdin.buffer, argv[4:5] == ["1"],
                                                  int(argv[5]) if len(argv) > 5 else None)))
        else:
            return 2
    except FsError as e:
        # fs-cat has the file's bytes on stdout, so its error goes to stderr and the exit code says it failed
        (sys.stderr if op == "fs-cat" else sys.stdout).write(json.dumps({"error": str(e), "code": e.code}))
        return 3 if op == "fs-cat" else 0
    return 0


# -- selftest -----------------------------------------------------------------------------------

def selftest():
    class R:
        def __init__(self, out="", rc=0):
            self.stdout, self.returncode = out, rc

    with tempfile.TemporaryDirectory() as tmp:
        # usage: the number is the first field; a partial answer (rc 1) counts; a missing path is 0
        d = Path(tmp, "v"); d.mkdir()
        chamadas = []
        def du(cmd, **kw):
            chamadas.append(cmd)
            return R(f"1234\t{cmd[-1]}\n", 1)
        assert dir_bytes(d, du, unshare=True) == 1234 and chamadas[-1][:3] == ["podman", "unshare", "du"], chamadas
        assert dir_bytes(d, du, unshare=False) == 1234 and chamadas[-1][0] == "du"
        assert dir_bytes(Path(tmp, "nope"), du) == 0
        assert dir_bytes(d, lambda c, **k: R("", 1), unshare=False) == 0
        u = usage({"a": [d], "b": [d, d], "c": []}, du, unshare=False)
        assert [(x["app"], x["bytes"]) for x in u] == [("b", 2468), ("a", 1234), ("c", 0)], u

        # delays: minutes, or the next HH:MM; out of range or malformed is refused
        agora = time.mktime((2026, 11, 18, 10, 0, 0, 0, 0, -1))
        assert delay_of(minutes=15, now=agora) == 900
        assert delay_of(at="10:30", now=agora) == 1800
        assert delay_of(at="09:00", now=agora) == 23 * 3600, "an hour already past means tomorrow"
        assert delay_of(at="10:00", now=agora) == 24 * 3600, "now is too soon: tomorrow"
        for ruim in ({"minutes": 0}, {"minutes": 10 ** 6}, {"at": "25:00"}, {"at": "9"}, {"minutes": "5"}, {"minutes": True}, {}):
            try:
                delay_of(now=agora, **ruim)
            except ValueError:
                continue
            raise AssertionError(ruim)

        # schedule / state / cancel, with a systemd that answers
        ativo = {"v": False}
        log = []
        def systemd(cmd, **kw):
            log.append(cmd)
            if cmd[0] == "systemd-run":
                ativo["v"] = True
                return R()
            if cmd[:3] == ["systemctl", "--user", "stop"]:
                ativo["v"] = False
                return R()
            if cmd[:3] == ["systemctl", "--user", "is-active"]:
                return R("active\n" if ativo["v"] else "inactive\n", 0 if ativo["v"] else 3)
            return R()
        assert state(tmp, systemd, now=agora) is None
        e = schedule(tmp, "reboot", 900, systemd, now=agora)
        assert e == {"action": "reboot", "at": int(agora) + 900}
        run_cmd = next(c for c in log if c[0] == "systemd-run")
        assert run_cmd[-2:] == ["systemctl", "reboot"] and "--on-active=900s" in run_cmd and "--user" in run_cmd, run_cmd
        assert state(tmp, systemd, now=agora) == e
        e2 = schedule(tmp, "poweroff", 3600, systemd, now=agora)
        assert state(tmp, systemd, now=agora) == e2, "a second schedule replaces the first"
        ativo["v"] = False
        assert state(tmp, systemd, now=agora) is None and not state_file(tmp).exists(), "the timer is gone: the file goes too"
        schedule(tmp, "reboot", 900, systemd, now=agora)
        cancel(tmp, systemd)
        assert state(tmp, systemd, now=agora) is None
        assert schedule(tmp, "reboot", 900, lambda c, **k: R("", 1)) is None and not state_file(tmp).exists(), "refused: nothing kept"
        try:
            schedule(tmp, "halt", 900, systemd)
            raise AssertionError("an unknown verb")
        except ValueError:
            pass
    # files: nothing leaves the root, links are refused, text is told from binary
    with tempfile.TemporaryDirectory() as tmp:
        raiz = Path(tmp, "app"); (raiz / "data/sub").mkdir(parents=True)
        (raiz / "data/b.txt").write_text("hello\n"); (raiz / "data/A.bin").write_bytes(b"\x00\x01")
        (raiz / "data/sub/c.md").write_text("é" * 10)
        Path(tmp, "secret").write_text("host file")
        os.symlink(Path(tmp, "secret"), raiz / "data/escape")
        os.symlink(raiz / "data/sub", raiz / "data/linkdir")
        r = fs_list(raiz, "data")
        assert [(e["name"], e["type"]) for e in r["entries"]] == [("sub", "dir"), ("A.bin", "file"), ("b.txt", "file"), ("escape", "link"), ("linkdir", "link")], r
        assert next(e for e in r["entries"] if e["name"] == "b.txt")["size"] == 6
        assert fs_list(raiz, "")["entries"][0]["name"] == "data" and fs_list(raiz, "/data/")["entries"], "slashes are forgiven"
        for ruim, codigo in (("../secret", 400), ("data/../../secret", 400), ("data/escape", 400), ("data/linkdir", 400),
                             ("data/linkdir/c.md", 400), ("data/nope", 404), ("data/b.txt\0x", 400)):
            try:
                fs_list(raiz, ruim) if not ruim.endswith(".txt") and "\0" not in ruim else fs_preview(raiz, ruim)
                raise AssertionError(ruim)
            except FsError as e:
                assert e.code == codigo, (ruim, e.code)
        try:
            fs_list(raiz, "data/b.txt")
            raise AssertionError("a file is not a folder")
        except FsError as e:
            assert e.code == 400
        assert fs_preview(raiz, "data/b.txt") == {"text": "hello\n", "size": 6, "truncated": False}
        try:
            fs_preview(raiz, "data/A.bin")
            raise AssertionError("binary")
        except FsError as e:
            assert e.code == 415
        (raiz / "data/big.txt").write_text("é" * (PREVIEW_MAX // 2 + 10))      # cut in the middle of a character
        g = fs_preview(raiz, "data/big.txt")
        assert g["truncated"] and len(g["text"].encode()) <= PREVIEW_MAX, "a cut character is not a binary file"
        try:
            fs_open(raiz, "data/escape")
            raise AssertionError("a link is never opened")
        except FsError as e:
            assert e.code == 400
        os.mkfifo(raiz / "data/fifo")
        try:
            fs_open(raiz, "data/fifo")
            raise AssertionError("a fifo is not a file")
        except FsError as e:
            assert e.code == 400
        # change: create, rename, copy, move, write and delete, all inside the root
        def recusa(fn, *a, code=400):
            try:
                fn(*a)
            except FsError as e:
                assert e.code == code, (fn.__name__, a, e.code)
                return
            raise AssertionError((fn.__name__, a))
        assert fs_mkdir(raiz, "data", "novo") == {"name": "novo"} and (raiz / "data/novo").is_dir()
        recusa(fs_mkdir, raiz, "data", "novo", code=409)
        for ruim in ("", ".", "..", "a/b", "x\0y", "n" * 300):
            recusa(fs_mkdir, raiz, "data", ruim)
        recusa(fs_mkdir, raiz, "data/b.txt", "x")
        recusa(fs_mkdir, raiz, "data/escape", "x")
        assert fs_rename(raiz, "data/novo", "renomeado") == {"name": "renomeado"} and (raiz / "data/renomeado").is_dir()
        recusa(fs_rename, raiz, "data/renomeado", "sub", code=409)
        recusa(fs_rename, raiz, "", "x")
        recusa(fs_rename, raiz, "data/renomeado", "../fora")
        assert fs_rename(raiz, "data/escape", "link2") == {"name": "link2"} and os.path.islink(raiz / "data/link2"), "a link itself can be renamed"
        recusa(fs_rename, raiz, "data/link2/x", "y")
        # write: a new file, a taken name gets (1), overwrite replaces, a cut stream leaves nothing
        import io
        assert fs_write(raiz, "data/sub", "up.txt", io.BytesIO(b"abc")) == {"name": "up.txt"}
        assert fs_write(raiz, "data/sub", "up.txt", io.BytesIO(b"def")) == {"name": "up (1).txt"}
        assert (raiz / "data/sub/up.txt").read_bytes() == b"abc" and (raiz / "data/sub/up (1).txt").read_bytes() == b"def"
        assert fs_write(raiz, "data/sub", "up.txt", io.BytesIO(b"new"), overwrite=True) == {"name": "up.txt"} and (raiz / "data/sub/up.txt").read_bytes() == b"new"
        class Corta:
            def read(self, n=-1):
                raise OSError("connection cut")
        try:
            fs_write(raiz, "data/sub", "meio.txt", Corta())
            raise AssertionError("a cut upload")
        except OSError:
            pass
        assert not (raiz / "data/sub/meio.txt").exists() and not list((raiz / "data/sub").glob(".*qhpart")), "nothing is left half written"
        recusa(fs_write, raiz, "data/sub", "short.txt", io.BytesIO(b"12"), False, 5)
        assert not (raiz / "data/sub/short.txt").exists() and not list((raiz / "data/sub").glob(".*qhpart")), "a stream shorter than announced is a cut upload"
        assert fs_write(raiz, "data/sub", "whole.txt", io.BytesIO(b"12345"), False, 5) == {"name": "whole.txt"}
        recusa(fs_write, raiz, "data/sub", "../x", io.BytesIO(b""))
        recusa(fs_write, raiz, "data/sub/up.txt", "x", io.BytesIO(b""))
        recusa(fs_write, raiz, "data/linkdir", "x", io.BytesIO(b""))
        os.symlink(Path(tmp, "secret"), raiz / "data/sub/ln")
        recusa(fs_write, raiz, "data/sub", "ln", io.BytesIO(b"x"), True)
        assert Path(tmp, "secret").read_text() == "host file", "overwrite never writes through a link"
        # copy and move: collisions are renamed, a folder cannot go into itself, a move leaves nothing behind
        assert fs_copy(raiz, "data/sub/up.txt", raiz, "data/renomeado") == {"name": "up.txt"}
        assert fs_copy(raiz, "data/sub/up.txt", raiz, "data/renomeado") == {"name": "up (1).txt"}
        assert fs_copy(raiz, "data/sub", raiz, "data/renomeado") == {"name": "sub"} and (raiz / "data/renomeado/sub/c.md").exists()
        assert (raiz / "data/sub/c.md").exists(), "a copy keeps the original"
        recusa(fs_copy, raiz, "data/sub", raiz, "data/sub")
        recusa(fs_move, raiz, "data/renomeado", raiz, "data/renomeado/sub")
        assert fs_move(raiz, "data/renomeado/up.txt", raiz, "data/sub") == {"name": "up (2).txt"} and not (raiz / "data/renomeado/up.txt").exists()
        recusa(fs_move, raiz, "", raiz, "data")
        assert fs_copy(raiz, "data/link2", raiz, "data") == {"name": "link2 (1)"} and os.path.islink(raiz / "data/link2 (1)"), "a link is copied as a link, never followed"
        fs_delete(raiz, "data/link2 (1)")
        outra = Path(tmp, "outra"); outra.mkdir()
        assert fs_move(raiz, "data/sub/up (2).txt", outra, "") == {"name": "up (2).txt"} and (outra / "up (2).txt").exists(), "between two roots"
        # delete: a file, a folder with a link inside (the link goes, its target stays), never the root
        assert fs_delete(raiz, "data/sub/up (1).txt") == {}
        assert fs_delete(raiz, "data/sub") == {} and not (raiz / "data/sub").exists() and Path(tmp, "secret").exists()
        assert fs_delete(raiz, "data/link2") == {} and not os.path.lexists(raiz / "data/link2") and Path(tmp, "secret").exists()
        recusa(fs_delete, raiz, "")
        recusa(fs_delete, raiz, "data/nope", code=404)
        recusa(fs_delete, raiz, "../secret")
        # the command line the store runs under `podman unshare`
        j = json.loads(subprocess.run([sys.executable, __file__, "fs-ls", str(raiz), "data"], capture_output=True, text=True).stdout)
        assert j["entries"][0]["name"] == "renomeado"
        assert subprocess.run([sys.executable, __file__, "fs-cat", str(raiz), "data/b.txt"], capture_output=True).stdout == b"hello\n"
        bad = subprocess.run([sys.executable, __file__, "fs-cat", str(raiz), "data/escape"], capture_output=True)
        assert bad.returncode == 3 and bad.stdout == b"", "a refused file gives no bytes"
    print("hostctl selftest: ok")


if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1].startswith("fs-"):
        sys.exit(_cli(sys.argv[1:]))
    if "--selftest" in sys.argv:
        selftest()
    else:
        print(__doc__)
