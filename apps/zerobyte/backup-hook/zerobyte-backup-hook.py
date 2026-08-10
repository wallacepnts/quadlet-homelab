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
import subprocess
import sys
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

PORT = int(os.environ.get("ZEROBYTE_HOOK_PORT", "8765"))
TOKEN_PATH = os.environ.get(
    "ZEROBYTE_HOOK_TOKEN_FILE",
    os.path.expanduser("~/.config/zerobyte-backup-hook/token"),
)
SECRET_HEADER = "X-Zerobyte-Hook-Secret"

# Comma-separated unit names, without the .service suffix. Empty means the
# hook answers 404 to everything: nothing is stopped by default.
ALLOWED = {u.strip() for u in os.environ.get("ZEROBYTE_HOOK_UNITS", "").split(",") if u.strip()}


def load_token() -> str:
    with open(TOKEN_PATH) as f:
        return f.read().strip()


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
            self._send_json(200, {"ok": True})
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

        if parts[2] == "pre-backup":
            self._handle_pre(f"{unit}.service")
        else:
            self._handle_post(f"{unit}.service")

    def _handle_pre(self, unit: str) -> None:
        # Blocking on purpose: Zerobyte only runs Restic after a 2xx here,
        # so the response MUST wait for the stop to really finish
        # (systemctl --user stop already blocks until it has stopped).
        try:
            result = systemctl("stop", unit, timeout=45)
        except subprocess.TimeoutExpired:
            self._send_json(500, {"error": "timeout stopping units"})
            return
        if result.returncode != 0:
            print(f"stop failed: {result.stderr}", file=sys.stderr)
            self._send_json(500, {"error": "stop failed", "detail": result.stderr})
            return
        self._send_json(200, {"ok": True, "action": "stopped", "unit": unit})

    def _handle_post(self, unit: str) -> None:
        # Non-blocking on purpose: the container uses Notify=healthy, so
        # "systemctl start" only returns once the healthcheck passes — which
        # can exceed Zerobyte's default 60s WEBHOOK_TIMEOUT. A failure here
        # only becomes a warning in Zerobyte (it does not abort the backup,
        # which has already run), so it is better to answer straight away and
        # let the restart happen in the background than to risk the webhook
        # blowing the timeout with the container still stopped.
        subprocess.Popen(
            ["systemctl", "--user", "start", unit],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
        self._send_json(200, {"ok": True, "action": "start triggered", "unit": unit})

    def log_message(self, fmt: str, *args) -> None:
        sys.stderr.write("%s - %s\n" % (self.address_string(), fmt % args))


def main() -> None:
    load_token()  # fail early if the token is missing or unreadable
    server = ThreadingHTTPServer(("0.0.0.0", PORT), Handler)
    print(f"zerobyte backup hook on 0.0.0.0:{PORT} for: {', '.join(sorted(ALLOWED)) or '(nothing)'}")
    server.serve_forever()


if __name__ == "__main__":
    main()
