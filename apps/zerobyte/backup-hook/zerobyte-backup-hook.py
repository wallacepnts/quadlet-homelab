#!/usr/bin/env python3
"""Receives Zerobyte's pre/post-backup hooks and stops the unit around the copy.

Restic copying a database while it is being written to produces an archive
that only reveals itself as broken when you restore it. This stops the unit
before Restic runs and starts it again afterwards, which is what makes the
copy cold.

The unit comes from the URL and must be in ALLOWED — an open endpoint that
stops anything by name is a denial of service with a nice API. Stdlib only on
purpose: it runs on the host's python, because a unit cannot stop itself from
inside the container being stopped.
"""
import hmac
import json
import os
import sqlite3
import subprocess
import sys
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

PORT = int(os.environ.get("ZEROBYTE_HOOK_PORT", "8766"))
TOKEN_PATH = os.environ.get(
    "ZEROBYTE_HOOK_TOKEN_FILE",
    os.path.expanduser("~/.config/zerobyte-backup-hook/token"),
)
SECRET_HEADER = "X-Zerobyte-Hook-Secret"

# `unit[:mode[:dir]]`, comma-separated, unit without the .service suffix.
# Empty means the hook answers 404 to everything: it acts on nothing by
# default. Modes:
#
#   stop     stop the unit before Restic and start it after (the default)
#   sqlite   copy each database with SQLite's online backup API and leave the
#            unit running — consistent without any downtime, which `stop` does
#            NOT give you on its own: Restic still reads the .db and its -wal
#            as two separate files.
#
# `dir` overrides where the databases are looked for; it defaults to
# ~/.config/containers/volumes/<unit>.
# Must exceed the unit's own TimeoutStopSec, or this gives up while systemd is
# still legitimately stopping it and reports a failure that is not one.
# any-sync-bundle asks for 120s, following upstream's stop_grace_period.
STOP_TIMEOUT = int(os.environ.get("ZEROBYTE_HOOK_STOP_TIMEOUT", "150"))
VOLUMES = os.path.expanduser("~/.config/containers/volumes")
COPY_DIR = ".dbbackup"          # inside the volume, so Restic already covers it


def _parse_units(raw: str) -> dict:
    out = {}
    for entry in raw.split(","):
        entry = entry.strip()
        if not entry:
            continue
        parts = entry.split(":")
        unit = parts[0].strip()
        mode = parts[1].strip() if len(parts) > 1 and parts[1].strip() else "stop"
        path = parts[2].strip() if len(parts) > 2 else os.path.join(VOLUMES, unit)
        if mode not in ("stop", "sqlite"):
            print(f"unknown mode {mode!r} for {unit}, using stop", file=sys.stderr)
            mode = "stop"
        out[unit] = (mode, path)
    return out


ALLOWED = _parse_units(os.environ.get("ZEROBYTE_HOOK_UNITS", ""))


def load_token() -> str:
    with open(TOKEN_PATH) as f:
        return f.read().strip()


def units_for(name: str) -> list:
    """The units this name stands for.

    Usually one, of the same name. media-stack is the exception the whole
    repository is built around: rule 1 makes every unit of a stack start with
    the app's name, so twelve `media-stack-*` units share one volume folder and
    there is no `media-stack.service` to stop. Stopping the prefix covers them
    without naming each one here, and a name that owns nothing stops nothing.
    """
    name = name[:-len(".service")] if name.endswith(".service") else name
    exato = systemctl("list-unit-files", f"{name}.service", "--no-legend", timeout=15)
    if f"{name}.service" in exato.stdout:
        return [name]
    achadas = systemctl("list-unit-files", f"{name}-*.service", "--no-legend", timeout=15)
    return [l.split()[0][:-len(".service")] for l in achadas.stdout.splitlines() if l.strip()]


def systemctl(*args: str, timeout: int) -> subprocess.CompletedProcess:
    return subprocess.run(
        ["systemctl", "--user", *args],
        capture_output=True,
        text=True,
        timeout=timeout,
    )


class Handler(BaseHTTPRequestHandler):
    server_version = "zerobyte-backup-hook/1"

    def _send_json(self, status: int, body: dict) -> None:
        payload = json.dumps(body).encode()
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(payload)))
        self.end_headers()
        self.wfile.write(payload)

    def _authorized(self) -> bool:
        got = self.headers.get(SECRET_HEADER, "")
        try:
            want = load_token()
        except OSError:
            print(f"token file not readable: {TOKEN_PATH}", file=sys.stderr)
            return False
        return hmac.compare_digest(got, want)

    def _read_body(self) -> None:
        length = int(self.headers.get("Content-Length", 0))
        if length:
            self.rfile.read(length)

    def do_GET(self) -> None:
        if self.path == "/healthz":
            # The allowlist is reported, not just liveness: an empty one answers
            # 404 to every job, and the only other way to notice is a night of
            # failed backups. `qh --zerobyte` reads this and says what is
            # missing. Unit names only — no token, no paths.
            self._send_json(200, {"ok": True, "units": sorted(f"{u}:{v[0]}" for u, v in ALLOWED.items())})
            return
        self._send_json(404, {"error": "not found"})

    def do_POST(self) -> None:
        self._read_body()

        # /hooks/<unit>/pre-backup — the unit is checked against the allowlist
        # BEFORE the token, so an unknown name looks the same to a caller with
        # a valid token as to one without: 404 either way.
        parts = self.path.strip("/").split("/")
        if len(parts) != 3 or parts[0] != "hooks" or parts[2] not in ("pre-backup", "post-backup"):
            self._send_json(404, {"error": "not found"})
            return
        unit = parts[1]
        if unit not in ALLOWED:
            self._send_json(404, {"error": "unknown unit", "unit": unit})
            return

        if not self._authorized():
            self._send_json(401, {"error": "unauthorized"})
            return

        mode, folder = ALLOWED[unit]
        if parts[2] == "pre-backup":
            if mode == "sqlite":
                feitos, erros = self._sqlite_copies(folder)
                for e in erros:
                    print(f"sqlite backup: {e}", file=sys.stderr)
                self._send_json(200, {"ok": True, "action": "sqlite copied",
                                      "unit": unit, "databases": feitos,
                                      "errors": erros})
                return
            self._handle_pre(f"{unit}.service")
        else:
            if mode == "sqlite":
                self._send_json(200, {"ok": True, "action": "nothing to undo", "unit": unit})
                return
            self._handle_post(f"{unit}.service")

    def _sqlite_copies(self, folder: str) -> tuple[int, list]:
        """A consistent copy of every database under `folder`, into COPY_DIR.

        `Connection.backup()` is SQLite's own online backup: it reads inside a
        transaction and restarts the copy if a writer gets in the way, so the
        result is a point-in-time database and not a torn file. The copy also
        arrives without the free pages, which is why it is usually smaller than
        the original.
        """
        destino = os.path.join(folder, COPY_DIR)
        os.makedirs(destino, exist_ok=True)
        feitos, erros = 0, []
        for raiz, dirs, arquivos in os.walk(folder):
            if COPY_DIR in dirs:
                dirs.remove(COPY_DIR)          # never copy the copies
            for nome in arquivos:
                if not nome.endswith((".db", ".sqlite", ".sqlite3")):
                    continue
                origem = os.path.join(raiz, nome)
                alvo = os.path.join(destino, os.path.relpath(origem, folder).replace(os.sep, "_"))
                try:
                    src = sqlite3.connect(f"file:{origem}?mode=ro", uri=True)
                    dst = sqlite3.connect(alvo)
                    with dst:
                        src.backup(dst)
                    dst.close(); src.close()
                    feitos += 1
                except sqlite3.Error as e:
                    # Not every .db is SQLite, and one unreadable file must not
                    # sink the whole backup.
                    erros.append(f"{origem}: {e}")
        return feitos, erros

    def _handle_pre(self, unit: str) -> None:
        # Blocking on purpose: Zerobyte only runs Restic after a 2xx here,
        # so the response MUST wait for the stop to really finish
        # (systemctl --user stop already blocks until it has stopped).
        alvos = units_for(unit)
        if not alvos:
            self._send_json(500, {"error": "no unit to stop", "unit": unit})
            return
        try:
            result = systemctl("stop", *alvos, timeout=STOP_TIMEOUT)
        except subprocess.TimeoutExpired:
            self._send_json(500, {"error": "timeout stopping units"})
            return
        if result.returncode != 0:
            print(f"stop failed: {result.stderr}", file=sys.stderr)
            self._send_json(500, {"error": "stop failed", "detail": result.stderr})
            return
        self._send_json(200, {"ok": True, "action": "stopped", "units": alvos})

    def _handle_post(self, unit: str) -> None:
        # Non-blocking on purpose: the container uses Notify=healthy, so
        # "systemctl start" only returns once the healthcheck passes — which
        # can exceed Zerobyte's default 60s WEBHOOK_TIMEOUT. A failure here
        # only becomes a warning in Zerobyte (it does not abort the backup,
        # which has already run), so it is better to answer straight away and
        # let the restart happen in the background than to risk the webhook
        # blowing the timeout with the container still stopped.
        alvos = units_for(unit)
        subprocess.Popen(
            ["systemctl", "--user", "start", *alvos],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
        self._send_json(200, {"ok": True, "action": "start triggered", "units": alvos})

    def log_message(self, fmt: str, *args) -> None:
        sys.stderr.write("%s - %s\n" % (self.address_string(), fmt % args))


def main() -> None:
    load_token()  # fail early if the token is missing or unreadable
    server = ThreadingHTTPServer(("0.0.0.0", PORT), Handler)
    print(f"zerobyte backup hook on 0.0.0.0:{PORT} for: {', '.join(sorted(ALLOWED)) or '(nothing)'}")
    server.serve_forever()


if __name__ == "__main__":
    main()
