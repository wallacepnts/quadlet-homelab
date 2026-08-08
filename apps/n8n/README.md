# n8n — Podman Quadlet (rootless)

**[🇧🇷 Leia em português](./README.pt-BR.md)**

An [n8n](https://n8n.io) (workflow automation through a visual node editor —
a self-hosted Zapier/IFTTT of sorts) deploy via Podman Quadlet, following the
[official Docker installation guide](https://docs.n8n.io/deploy/host-n8n/install-options/install-with-docker/).

## Architecture

A single container, with an **embedded SQLite** database in
`/home/node/.n8n` (the official default — it can be swapped for Postgres
later, see Variants, but that is not the setup here). Single-instance mode,
with no queue (Redis) — enough for personal use; queue mode is only needed at
scale (many workflows
concorrentes).

The image runs as a fixed `node` user, with no internal usermod (the same
case
do Jellyfin/Seerr no [media-stack](../media-stack/)) — por isso
`UserNS=keep-id` no `.container`, mapeando o container pro mesmo uid do
user running Podman. Without it, the container does not own the bind mount
created by the host (see Troubleshooting).

## Files

```
n8n.container   # main unit
```

## Prerequisites

- Rootless Podman with systemd `--user` working
- `openssl` (to generate the secret)

## Installation

```bash
python3 install.py n8n            # dry-run: shows what it will do
python3 install.py n8n --apply
```

For the local network only, `--access local`; on the tailnet and the LAN,
`--access both`. Adding `--href-local` points the dashboard link at the LAN.
The script creates the directories, writes the `.env`, generates the secrets,
fixes the volumes' ownership, starts the service and prints the address at the
end — see [Installing and operating](../../docs/installing.md).

Reach it through [tsdproxy](../tsdproxy/) (tailnet) at
`https://n8n.<your-tailnet>.ts.net`, or locally at `http://localhost:5678`.
Create the first account through the UI itself (there is no default username or password).

<details>
<summary><b>Manual installation</b> (advanced) — the same steps, one at a time</summary>


```bash
# 1. Download the unit (no need to clone the repository)
mkdir -p ~/.config/containers/systemd
wget -P ~/.config/containers/systemd/ \
  https://raw.githubusercontent.com/wallacepnts/quadlet-homelab/main/apps/n8n/n8n.container

# 2. Data directory — a bind mount requires it to exist before the start
mkdir -p ~/.config/containers/volumes/n8n/data

# 3. Secret — the encryption key for the credentials saved in workflows
#    (API tokens, passwords and so on). Generate it explicitly rather than
#    letting n8n generate one on the first start, so the value is documented.
mkdir -p ~/.config/containers/secrets/n8n
openssl rand -hex 32 | tr -d '\n' > ~/.config/containers/secrets/n8n/encryption-key.txt
chmod 600 ~/.config/containers/secrets/n8n/encryption-key.txt
podman secret create n8n-encryption-key ~/.config/containers/secrets/n8n/encryption-key.txt

# 4. Non-secret env — download the example
mkdir -p ~/.config/containers/env
wget -O ~/.config/containers/env/n8n.env \
  https://raw.githubusercontent.com/wallacepnts/quadlet-homelab/main/apps/n8n/.env.example

# 5. Start it
systemctl --user daemon-reload
systemctl --user start n8n
```

Reach it through [tsdproxy](../tsdproxy/) (tailnet) at
`https://n8n.<your-tailnet>.ts.net`, ou local em `http://localhost:5678`.
Create the first account through the UI itself (there is no default username or password).

**If you will use production webhooks** called by services outside this
host, set `WEBHOOK_URL` in `n8n.env` to the public/tailnet address — without
it, n8n uses the local address, which is not reachable from outside.

</details>

## Auto-update

No `AutoUpdate=` — an explicit tag (`2.33.6`), bumped by hand
(rule 9 of the [conventions](../../docs/conventions.md)). The image has `wget` and a real healthcheck (it could be enabled with
genuine rollback), but the saved workflows and credentials are the user's real
data — review by hand before updating, the same reasoning as vaultwarden.

## Backup & recovery

```bash
systemctl --user stop n8n
tar -czf n8n-backup-$(date +%Y%m%d-%H%M%S).tar.gz \
  -C ~/.config/containers/volumes n8n
systemctl --user start n8n
```

The secret (`~/.config/containers/secrets/n8n/`) needs a separate backup too
— without the same `N8N_ENCRYPTION_KEY`, the credentials saved in workflows
(tokens, other services' passwords) become unreadable when restored onto a new
host.

## Variants

The official guide also documents swapping SQLite for Postgres
(`DB_TYPE=postgresdb` + `DB_POSTGRESDB_*`) — deliberately not used here, the
same reasoning as paperless-ngx: avoid another external database with no real
need at the expected usage level.

## Troubleshooting

**`toomanyrequests: You have reached your unauthenticated pull rate
limit`** when pulling the image — tested in practice: the official guide
recommends `docker.n8n.io/n8nio/n8n`, but that mirror hits Docker Hub's
anonymous rate limit behind the scenes. Running `podman login docker.io`
**does not help**, because it is a separate registry — the authentication does
not propagate to the mirror. The fix: use `docker.io/n8nio/n8n` directly (the
same image, the same tag), where authentication genuinely works. That is
already what this `.container` uses.

**`Error: EACCES: permission denied, open '/home/node/.n8n/config'`** no
on the first start — the image runs as a fixed `node` user (a fixed internal
uid, with no LSIO-style usermod). Without `UserNS=keep-id`, the bind mount
created by the host (`mkdir -p`, owned by your uid) is not accessible to
`node`'s uid inside the container. `UserNS=keep-id` fixes it by mapping the
container to the same uid as whoever runs Podman — already included in this
repository's `.container`, documented here in case it turns up again on
another host.

## Useful commands

```bash
systemctl --user status n8n
podman logs -f n8n
podman exec n8n wget -qO- http://127.0.0.1:5678/healthz
```

## Credits

Quadlet deploy based on [n8n](https://github.com/n8n-io/n8n).
Original licence: the Sustainable Use License (fair-code, not pure open
source — personal and internal use is free; reselling the software hosted by
third parties is not).
