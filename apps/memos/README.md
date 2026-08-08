# Memos — Podman Quadlet (rootless)

**[🇧🇷 Leia em português](./README.pt-BR.md)**

A [Memos](https://usememos.com) (self-hosted, markdown-native, lightweight
quick notes) deploy via Podman Quadlet, using the official
[`neosmemo/memos`](https://github.com/usememos/memos) image.

## Architecture

A single container, running as root internally (no `PUID`/`PGID`, no
`UserNS=keep-id` — the image adjusts the volume's owner itself on the first
start, the same pattern as several other apps here).
**Embedded SQLite** — a single volume holds the entire database
(`/var/opt/memos`).

The healthcheck uses the image's own endpoint (`/healthz`, tested in
practice) — no generic HTTP check needed.

## Files

```
memos.container       # main unit
```

## Prerequisites

- Rootless Podman with systemd `--user` working

## Installation

```bash
python3 install.py memos            # dry-run: shows what it will do
python3 install.py memos --apply
```

For the local network only, `--access local`; on the tailnet and the LAN,
`--access both`. Adding `--href-local` points the dashboard link at the LAN.
The script creates the directories, writes the `.env`, generates the secrets,
fixes the volumes' ownership, starts the service and prints the address at the
end — see [Installing and operating](../../docs/installing.md).

Open `http://<host-ip>:5230` (ou via [tsdproxy](../tsdproxy/) em
`https://memos.<your-tailnet>.ts.net`) e criar a conta no primeiro
access — **the first user to sign up automatically becomes admin**, with no
email confirmation (unlike [Monica](../monica/)). Once that account exists,
turn open signup off in Settings → (the admin section) → "Allow user signup",
otherwise anyone who reaches the URL can create an account of their own.

<details>
<summary><b>Manual installation</b> (advanced) — the same steps, one at a time</summary>


```bash
# 1. Download the units (no need to clone the repository)
mkdir -p ~/.config/containers/systemd
wget -P ~/.config/containers/systemd/ \
  https://raw.githubusercontent.com/wallacepnts/quadlet-homelab/main/apps/memos/memos.container

# 2. Data directory — a bind mount requires it to exist before the start
mkdir -p ~/.config/containers/volumes/memos/data
podman unshare chown -R 1000:1000 ~/.config/containers/volumes/memos   # a unit usa User=1000

# 3. Non-secret env
mkdir -p ~/.config/containers/env
wget -O ~/.config/containers/env/memos.env \
  https://raw.githubusercontent.com/wallacepnts/quadlet-homelab/main/apps/memos/.env.example

# 4. Start it
systemctl --user daemon-reload
systemctl --user start memos
```

Open `http://<host-ip>:5230` (ou via [tsdproxy](../tsdproxy/) em
`https://memos.<your-tailnet>.ts.net`) e criar a conta no primeiro
access — **the first user to sign up automatically becomes admin**, with no
email confirmation (unlike [Monica](../monica/)). Once that account exists,
turn open signup off in Settings → (the admin section) → "Allow user signup",
otherwise anyone who reaches the URL can create an account of their own.

</details>

## Auto-update

No `AutoUpdate=` — an explicit tag (`0.30.0`), bumped by hand
(rule 9 of the [conventions](../../docs/conventions.md)). The image has `wget` and a real healthcheck (`/healthz`) —
`AutoUpdate=registry` could be enabled with working rollback, but notes are
the user's real data, the same reasoning as
[vaultwarden](../vaultwarden/)/[radicale](../radicale/) — review by hand
before updating.

## Backup & recovery

```bash
systemctl --user stop memos
tar -czf memos-backup-$(date +%Y%m%d-%H%M%S).tar.gz \
  -C ~/.config/containers/volumes memos
systemctl --user start memos
```

## Useful commands

```bash
systemctl --user status memos
podman logs -f memos
podman exec memos wget -qO- http://127.0.0.1:5230/healthz
```

## Credits

Quadlet deploy based on [Memos](https://github.com/usememos/memos)
(MIT).
