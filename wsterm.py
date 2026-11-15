#!/usr/bin/env python3
"""A WebSocket (RFC 6455) and a pty, with the standard library only: a console in a container.

The store's page sends keystrokes, the server runs `podman exec -it <container> sh` on a
pseudo-terminal and sends the output back. The WebSocket here is the small part of the
protocol a text console needs: the handshake, text frames in both directions, ping/pong,
close, fragmentation. No extensions, no binary frames, no compression.

    python3 wsterm.py --selftest
"""

import base64
import codecs
import fcntl
import hashlib
import json
import os
import select
import signal
import struct
import subprocess
import sys
import termios
import time

GUID = "258EAFA5-E914-47DA-95CA-C5AB0DC85B11"
MAX_PAYLOAD = 64 * 1024
IDLE_LIMIT = 15 * 60                # a console nobody types in for this long is closed
PING_EVERY = 20
# bash when the image has it, sh when not. `command -v` first: a failed `exec` ends a POSIX shell.
SHELL_CMD = "command -v bash >/dev/null 2>&1 && exec bash || exec sh"

OP_CONT, OP_TEXT, OP_BIN, OP_CLOSE, OP_PING, OP_PONG = 0x0, 0x1, 0x2, 0x8, 0x9, 0xA


def accept_key(chave):
    """Sec-WebSocket-Accept for a client's Sec-WebSocket-Key."""
    return base64.b64encode(hashlib.sha1((chave + GUID).encode()).digest()).decode()


def frame(opcode, payload=b""):
    """One unmasked server frame (a server never masks)."""
    n = len(payload)
    cab = bytes([0x80 | opcode])
    if n < 126:
        cab += bytes([n])
    elif n < 1 << 16:
        cab += bytes([126]) + struct.pack(">H", n)
    else:
        cab += bytes([127]) + struct.pack(">Q", n)
    return cab + payload


class ProtocolError(Exception):
    pass


class Parser:
    """Feed it bytes from the socket; it returns the complete messages as (opcode, payload).

    Client frames must be masked (RFC 6455 §5.1) and payloads stay under MAX_PAYLOAD; anything else
    is a ProtocolError and the connection is dropped. Fragmented text is reassembled."""

    def __init__(self):
        self.buf = b""
        self.partes, self.op_partes = [], None

    def feed(self, dados):
        self.buf += dados
        saida = []
        while True:
            if len(self.buf) < 2:
                break
            b0, b1 = self.buf[0], self.buf[1]
            fin, op, mascarado, n = bool(b0 & 0x80), b0 & 0x0F, bool(b1 & 0x80), b1 & 0x7F
            if b0 & 0x70:
                raise ProtocolError("reserved bits")
            pos = 2
            if n == 126:
                if len(self.buf) < 4:
                    break
                n, pos = struct.unpack(">H", self.buf[2:4])[0], 4
            elif n == 127:
                if len(self.buf) < 10:
                    break
                n, pos = struct.unpack(">Q", self.buf[2:10])[0], 10
            if not mascarado:
                raise ProtocolError("unmasked client frame")
            if n > MAX_PAYLOAD:
                raise ProtocolError("frame too large")
            if len(self.buf) < pos + 4 + n:
                break
            mascara = self.buf[pos:pos + 4]
            corpo = bytes(c ^ mascara[i % 4] for i, c in enumerate(self.buf[pos + 4:pos + 4 + n]))
            self.buf = self.buf[pos + 4 + n:]
            if op >= 0x8:                              # control frames are never fragmented
                if not fin or n > 125:
                    raise ProtocolError("bad control frame")
                saida.append((op, corpo))
                continue
            if op == OP_CONT:
                if self.op_partes is None:
                    raise ProtocolError("continuation with nothing to continue")
            elif self.op_partes is not None:
                raise ProtocolError("new message in the middle of one")
            else:
                self.op_partes = op
            self.partes.append(corpo)
            if sum(len(p) for p in self.partes) > MAX_PAYLOAD:
                raise ProtocolError("message too large")
            if fin:
                saida.append((self.op_partes, b"".join(self.partes)))
                self.partes, self.op_partes = [], None
        return saida


def set_size(fd, colunas, linhas):
    colunas, linhas = max(20, min(int(colunas), 400)), max(5, min(int(linhas), 200))
    fcntl.ioctl(fd, termios.TIOCSWINSZ, struct.pack("HHHH", linhas, colunas, 0, 0))


def spawn(cmd, colunas=100, linhas=28):
    """(process, master fd): `cmd` with a pseudo-terminal for stdin, stdout and stderr."""
    mestre, escravo = os.openpty()
    set_size(mestre, colunas, linhas)
    try:
        proc = subprocess.Popen(cmd, stdin=escravo, stdout=escravo, stderr=escravo,
                                start_new_session=True, close_fds=True)
    finally:
        os.close(escravo)
    return proc, mestre


def stop(proc, mestre):
    """Closes the terminal and makes sure the process is gone: hang up, ask, then insist."""
    try:
        os.close(mestre)
    except OSError:
        pass
    if proc.poll() is None:
        for sinal, espera in ((signal.SIGHUP, 1.0), (signal.SIGTERM, 2.0), (signal.SIGKILL, 2.0)):
            try:
                os.killpg(proc.pid, sinal)
            except (ProcessLookupError, PermissionError):
                break
            try:
                proc.wait(timeout=espera)
                break
            except subprocess.TimeoutExpired:
                continue


def reap_cmd(token):
    """The shell snippet that kills, inside the container, everything started with QH_CONSOLE=<token> in
    its environment: the shell and what it launched. Closing the local `podman exec` does not hang up
    the terminal on the container's side, so without this a closed tab leaves its shell running."""
    return ("for d in /proc/[0-9]*; do p=${d#/proc/}; "
            f"tr '\\0' '\\n' < $d/environ 2>/dev/null | grep -qx 'QH_CONSOLE={token}' && kill -KILL $p 2>/dev/null; done; true")


def close_session(proc, mestre, limpar=None):
    """Ends a console the polite way first (Ctrl-C, `exit`), then by `limpar()`, then the local process."""
    if proc.poll() is None:
        try:
            os.write(mestre, b"\x03")
            time.sleep(0.2)
            os.write(mestre, b"exit\r\x04")
        except OSError:
            pass
        try:
            proc.wait(timeout=1.5)
        except subprocess.TimeoutExpired:
            if limpar:
                try:
                    limpar()
                except Exception:
                    pass
    stop(proc, mestre)


def serve(sock, cmd, relogio=time.time, limpar=None):
    """Runs the console for one upgraded connection until either side ends it. Returns why, in a word.

    Messages from the page are JSON text: {"t": "in", "d": "<keys>"} or {"t": "size", "c": 100, "r": 28}.
    What the process prints goes back as text frames, decoded as UTF-8 piece by piece so a character
    split between two reads is not mangled."""
    proc, mestre = spawn(cmd)
    parser, decoder = Parser(), codecs.getincrementaldecoder("utf-8")("replace")
    ultimo_uso, ultimo_ping, motivo = relogio(), relogio(), "closed"
    respondeu_fecho = False            # the close handshake is one frame each way, not two from us
    try:
        while True:
            prontos, _, _ = select.select([sock, mestre], [], [], 5)
            agora = relogio()
            if sock in prontos:
                dados = sock.recv(65536)
                if not dados:
                    motivo = "gone"
                    break
                for op, corpo in parser.feed(dados):
                    if op == OP_CLOSE:
                        sock.sendall(frame(OP_CLOSE, corpo[:2]))
                        respondeu_fecho = True
                        return "closed"
                    if op == OP_PING:
                        sock.sendall(frame(OP_PONG, corpo))
                    elif op == OP_TEXT:
                        try:
                            msg = json.loads(corpo.decode("utf-8"))
                        except ValueError:
                            raise ProtocolError("not JSON")
                        if msg.get("t") == "in" and isinstance(msg.get("d"), str):
                            os.write(mestre, msg["d"].encode("utf-8")[:MAX_PAYLOAD])
                            ultimo_uso = agora
                        elif msg.get("t") == "size":
                            set_size(mestre, msg.get("c", 100), msg.get("r", 28))
            if mestre in prontos:
                try:
                    saida = os.read(mestre, 65536)
                except OSError:
                    saida = b""
                if not saida:
                    motivo = "exited"
                    break
                texto = decoder.decode(saida)
                if texto:
                    sock.sendall(frame(OP_TEXT, texto.encode("utf-8")))
            elif proc.poll() is not None:
                motivo = "exited"
                break
            if agora - ultimo_uso > IDLE_LIMIT:
                motivo = "idle"
                break
            if agora - ultimo_ping > PING_EVERY:          # a write that fails is how a dead peer is noticed
                sock.sendall(frame(OP_PING))
                ultimo_ping = agora
    except (ProtocolError, OSError, ValueError) as e:
        motivo = f"error: {e}"
    finally:
        if not respondeu_fecho:
            try:
                sock.sendall(frame(OP_CLOSE, struct.pack(">H", 1000)))
            except OSError:
                pass
        close_session(proc, mestre, limpar)
    return motivo


# -- selftest ---------------------------------------------------------------------------------

def _mascarado(op, payload, fin=True):
    """A client frame, masked, for the tests."""
    mascara = b"\x01\x02\x03\x04"
    n = len(payload)
    cab = bytes([(0x80 if fin else 0) | op])
    cab += bytes([0x80 | n]) if n < 126 else bytes([0x80 | 126]) + struct.pack(">H", n)
    return cab + mascara + bytes(c ^ mascara[i % 4] for i, c in enumerate(payload))


def selftest():
    import socket
    assert accept_key("dGhlIHNhbXBsZSBub25jZQ==") == "s3pPLMBiTxaQ9kYGzzhZRbK+xOo=", "RFC 6455 §1.3's example"
    assert frame(OP_TEXT, b"hi") == b"\x81\x02hi"
    assert frame(OP_TEXT, b"x" * 200)[:4] == b"\x81\x7e\x00\xc8"
    p = Parser()
    assert p.feed(_mascarado(OP_TEXT, b"hello")) == [(OP_TEXT, b"hello")]
    quadro = _mascarado(OP_TEXT, b"split")
    assert p.feed(quadro[:3]) == [] and p.feed(quadro[3:]) == [(OP_TEXT, b"split")], "a frame in two reads"
    assert p.feed(_mascarado(OP_TEXT, b"ab", fin=False) + _mascarado(OP_CONT, b"cd")) == [(OP_TEXT, b"abcd")], "fragments"
    assert p.feed(_mascarado(OP_PING, b"x")) == [(OP_PING, b"x")]
    assert p.feed(_mascarado(OP_TEXT, b"a") + _mascarado(OP_TEXT, b"b")) == [(OP_TEXT, b"a"), (OP_TEXT, b"b")], "two in one read"
    for ruim in (frame(OP_TEXT, b"unmasked"), b"\xc1\x80\0\0\0\0", _mascarado(OP_CONT, b"orphan"),
                 _mascarado(OP_PING, b"x", fin=False), b"\x81\xff" + struct.pack(">Q", MAX_PAYLOAD + 1) + b"\0" * 4):
        try:
            Parser().feed(ruim)
            raise AssertionError(f"accepted {ruim[:8]!r}")
        except ProtocolError:
            pass

    # a console against `cat` on a real pty: what is typed is echoed by the terminal and by cat
    cliente, servidor = socket.socketpair()
    import threading
    resultado = []
    t = threading.Thread(target=lambda: resultado.append(serve(servidor, ["cat"])))
    t.start()
    cliente.sendall(_mascarado(OP_TEXT, json.dumps({"t": "size", "c": 80, "r": 24}).encode()))
    cliente.sendall(_mascarado(OP_TEXT, json.dumps({"t": "in", "d": "olá\r"}).encode()))
    recebido, fim = b"", time.time() + 5
    cliente.settimeout(1)
    while time.time() < fim and "olá".encode() not in recebido:
        try:
            recebido += cliente.recv(4096)
        except socket.timeout:
            pass
    assert "olá".encode() in recebido, recebido
    cliente.sendall(_mascarado(OP_CLOSE, struct.pack(">H", 1000)))
    t.join(5)
    assert resultado == ["closed"] and not t.is_alive(), resultado
    cliente.close()
    servidor.close()
    print("wsterm selftest: ok")
    return 0


if __name__ == "__main__":
    if "--selftest" not in sys.argv:
        print("usage: wsterm.py --selftest", file=sys.stderr)
        raise SystemExit(2)
    sys.exit(selftest())
