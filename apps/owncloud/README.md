# ownCloud — Podman Quadlet (rootless)

**[🇧🇷 Leia em português](./README.pt-BR.md)**

A deploy of [ownCloud](https://owncloud.com) Server (file sync and
compartilhamento de arquivos self-hosted) via Podman Quadlet, seguindo o
[official Docker installation guide](https://doc.owncloud.com/server/latest/admin_manual/installation/docker/index.html).

## SQLite — for evaluation, not production

Running on **SQLite** on purpose (an explicit request) — no
`OWNCLOUD_DB_TYPE`/`OWNCLOUD_DB_*` variable is set in the `.container`, and
SQLite is what the image uses by default in that case. The ownCloud project
itself **does not support SQLite in production**. Switch to MySQL/MariaDB or
Postgres later if usage justifies it (the same container pattern
extra usado no [immich](../immich/)).

## Architecture

A single container, with no Redis (the official production compose includes
Redis for caching and locking — dropped here because SQLite is already the
"evaluation" mode, and bringing in just one piece of the production stack
makes no sense). It exposes `8080`
(mapeado pra `8094` no host).

## Files

```
owncloud.container   # main unit
```

## Prerequisites

- Rootless Podman with systemd `--user` working
- `openssl` (to generate the secret)

## Installation

```bash
python3 install.py owncloud            # dry-run: shows what it will do
python3 install.py owncloud --apply
```

For the local network only, `--access local`; on the tailnet and the LAN,
`--access both`. Adding `--href-local` points the dashboard link at the LAN.
The script creates the directories, writes the `.env`, generates the secrets,
fixes the volumes' ownership, starts the service and prints the address at the
end — see [Installing and operating](../../docs/installing.md).

Reach it through [tsdproxy](../tsdproxy/) (tailnet) at
`https://owncloud.<your-tailnet>.ts.net`, ou local em
`http://localhost:8094`. Login com `OWNCLOUD_ADMIN_USERNAME` (default
`admin`) e a senha gerada no passo 3.

<details>
<summary><b>Manual installation</b> (advanced) — the same steps, one at a time</summary>


```bash
# 1. Download the unit (no need to clone the repository)
mkdir -p ~/.config/containers/systemd
wget -P ~/.config/containers/systemd/ \
  https://raw.githubusercontent.com/wallacepnts/quadlet-homelab/main/apps/owncloud/owncloud.container

# 2. Data directory — a bind mount requires it to exist before the start
mkdir -p ~/.config/containers/volumes/owncloud/data

# 3. Secret — the admin password (created on the first start)
mkdir -p ~/.config/containers/secrets/owncloud
openssl rand -base64 18 | tr -d '\n' > ~/.config/containers/secrets/owncloud/admin-password.txt
chmod 600 ~/.config/containers/secrets/owncloud/admin-password.txt
podman secret create owncloud-admin-password ~/.config/containers/secrets/owncloud/admin-password.txt

# 4. Non-secret env — download the example
#    OWNCLOUD_TRUSTED_DOMAINS with your tailnet domain
mkdir -p ~/.config/containers/env
wget -O ~/.config/containers/env/owncloud.env \
  https://raw.githubusercontent.com/wallacepnts/quadlet-homelab/main/apps/owncloud/.env.example
# edit ~/.config/containers/env/owncloud.env

# 5. Start it
systemctl --user daemon-reload
systemctl --user start owncloud
```

Reach it through [tsdproxy](../tsdproxy/) (tailnet) at
`https://owncloud.<your-tailnet>.ts.net`, ou local em
`http://localhost:8094`. Login com `OWNCLOUD_ADMIN_USERNAME` (default
`admin`) e a senha gerada no passo 3.

</details>

## Troubleshooting

**A CSRF/trusted-proxy error when reaching it over the tailnet** — the app
thinks it is on plain HTTP, but tsdproxy terminates TLS in front of it. The
`.env.example` already ships `OWNCLOUD_OVERWRITE_PROTOCOL=https` to avoid that
from the outset — if it still happens, check `OWNCLOUD_TRUSTED_DOMAINS` (it
has to include the exact hostname used in the browser).

## Auto-update

No `AutoUpdate=` — an explicit tag (`11.0.0-20260802`), bumped by hand
([rule 9](../../docs/conventions.md)). Synced files are the user's real data —
review by hand before updating, the same reasoning as immich. All the more
relevant here running on SQLite (a mode not officially supported in
production).

## Backup & recovery

```bash
systemctl --user stop owncloud
tar -czf owncloud-backup-$(date +%Y%m%d-%H%M%S).tar.gz \
  -C ~/.config/containers/volumes owncloud
systemctl --user start owncloud
```

## Useful commands

```bash
systemctl --user status owncloud
podman logs -f owncloud
podman exec owncloud /usr/bin/healthcheck
```

## Credits

Quadlet deploy based on [ownCloud](https://github.com/owncloud/core)
Server, usando a imagem oficial
[owncloud/server](https://github.com/owncloud-docker/server).
Original licence: AGPL-3.0.
