#!/usr/bin/env python3
"""Receives Zerobyte's pre/post-backup webhooks for any-sync-bundle.

It stops the container (AIO mode — embedded Mongo/Redis, a single systemd
unit) before Restic runs and brings it back afterwards — see
any-sync-bundle/README.md and zerobyte/README.md. Stdlib only on purpose (no
dependencies to install for a script that runs straight on the host, outside
a container).
"""
import hmac
import json
import os
import subprocess
import sys
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

PORT = int(os.environ.get("ANY_SYNC_BUNDLE_WEBHOOK_PORT", "8765"))
TOKEN_PATH = os.environ.get(
    "ANY_SYNC_BUNDLE_WEBHOOK_TOKEN_FILE",
    os.path.expanduser("~/.config/any-sync-bundle-webhook/token"),
)
SECRET_HEADER = "X-Zerobyte-Hook-Secret"

UNIT = "any-sync-bundle.service"


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
    server_version = "any-sync-bundle-webhook/1"

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

        if self.path not in ("/hooks/any-sync-bundle/pre-backup", "/hooks/any-sync-bundle/post-backup"):
            self._send_json(404, {"error": "not found"})
            return

        if not self._authorized():
            self._send_json(401, {"error": "unauthorized"})
            return

        if self.path == "/hooks/any-sync-bundle/pre-backup":
            self._handle_pre()
        else:
            self._handle_post()

    def _handle_pre(self) -> None:
        # Blocking on purpose: Zerobyte only runs Restic after a 2xx here,
        # so the response MUST wait for the stop to really finish
        # (systemctl --user stop already blocks until it has stopped).
        try:
            result = systemctl("stop", UNIT, timeout=45)
        except subprocess.TimeoutExpired:
            self._send_json(500, {"error": "timeout stopping units"})
            return
        if result.returncode != 0:
            print(f"stop failed: {result.stderr}", file=sys.stderr)
            self._send_json(500, {"error": "stop failed", "detail": result.stderr})
            return
        self._send_json(200, {"ok": True, "action": "stopped"})

    def _handle_post(self) -> None:
        # Non-blocking on purpose: the container uses Notify=healthy, so
        # "systemctl start" only returns once the healthcheck passes — which
        # can exceed Zerobyte's default 60s WEBHOOK_TIMEOUT. A failure here
        # only becomes a warning in Zerobyte (it does not abort the backup,
        # which has already run), so it is better to answer straight away and
        # let the restart happen in the background than to risk the webhook
        # blowing the timeout with the container still stopped.
        subprocess.Popen(
            ["systemctl", "--user", "start", UNIT],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
        self._send_json(200, {"ok": True, "action": "start triggered"})

    def log_message(self, fmt: str, *args) -> None:
        sys.stderr.write("%s - %s\n" % (self.address_string(), fmt % args))


def main() -> None:
    load_token()  # fail early if the token is missing or unreadable
    server = ThreadingHTTPServer(("0.0.0.0", PORT), Handler)
    print(f"any-sync-bundle webhook listening on 0.0.0.0:{PORT}")
    server.serve_forever()


if __name__ == "__main__":
    main()
