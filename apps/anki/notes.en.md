The install ends by printing the user and password. In each client, point sync at `https://anki.<your-tailnet>.ts.net/` and log in with them:

- **Anki (desktop)**: Preferences → Syncing → *Self-hosted sync server*.
- **AnkiDroid**: Settings → Sync → *Custom sync server*.
- **AnkiMobile**: Settings → Syncing → *Custom server*.

The first sync after switching is a full one: upload from the device that has the collection you want to keep, download on the others.

**There is no web page**: the address shows `404 Not Found` and that is the server running. Use the HTTPS tailnet address (AnkiMobile refuses a server without TLS); the phone needs Tailscale running.

To choose the password: `qh anki --reinstall --ask-secrets --apply` and type **`anki:your-password`**, user and password together. Keep the user name `anki`: collections live in a folder named after it.
