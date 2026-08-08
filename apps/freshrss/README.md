# FreshRSS — Podman Quadlet (rootless)

**[🇧🇷 Leia em português](./README.pt-BR.md)**

Deploy do [FreshRSS](https://freshrss.org) (agregador de feeds RSS/Atom
self-hosted, lightweight, with a Google Reader/Fever-compatible API for
mobile apps) via Podman Quadlet, using the official
[`freshrss/freshrss`](https://github.com/FreshRSS/FreshRSS/blob/edge/Docker/README.md)
(variante Alpine).

**The image is pulled from GHCR, not Docker Hub** — `docker.io/freshrss/freshrss`
returned an authentication error in practice (`unauthorized:
incorrect username or password`, mesmo anônimo/sem login configurado —
it looks like a registry-side problem, not this host's); `ghcr.io/freshrss/freshrss`
funcionou normal, mesma imagem/tag, publicada pelo mesmo projeto.

## Architecture

A single container, running as root internally (no `PUID`/`PGID`, no
`UserNS=keep-id` — the image manages permissions its own way).
Banco **SQLite embutido** no volume de dados, sem container de banco
separate — enough for personal use (the project itself documents
Postgres/MySQL as an alternative only for larger installations, outside the
escopo deste deploy).

**No automatic installation through env vars** — the image supports
`FRESHRSS_INSTALL`/`FRESHRSS_USER` pra criar o admin sem tocar no
navegador, mas isso significa embutir a senha em texto puro num
`EnvironmentFile=` (against [rule 2](../../docs/conventions.md) — secrets are
imperative). Instead, the admin account is created through the web wizard on
first access — the same pattern already used for
[ownCloud](../owncloud/)/[Immich](../immich/)/[Audiobookshelf](../audiobookshelf/).

The healthcheck uses the image's own `cli/health.php` (no output, just an
exit code) — no need for `wget`/`curl` against an HTTP endpoint.

## Files

```
freshrss.container      # main unit
```

## Prerequisites

- Rootless Podman with systemd `--user` working

## Installation

```bash
python3 install.py freshrss            # dry-run: shows what it will do
python3 install.py freshrss --apply
```

For the local network only, `--access local`; on the tailnet and the LAN,
`--access both`. Adding `--href-local` points the dashboard link at the LAN.
The script creates the directories, writes the `.env`, generates the secrets,
fixes the volumes' ownership, starts the service and prints the address at the
end — see [Installing and operating](../../docs/installing.md).

Open `http://<host-ip>:8104` (ou via [tsdproxy](../tsdproxy/) em
`https://freshrss.<your-tailnet>.ts.net`) e completar o assistente de
installation wizard on first access — choose **SQLite** as the database (it
is already selected by default) and create the admin account there.

<details>
<summary><b>Manual installation</b> (advanced) — the same steps, one at a time</summary>


```bash
# 1. Download the units (no need to clone the repository)
mkdir -p ~/.config/containers/systemd
wget -P ~/.config/containers/systemd/ \
  https://raw.githubusercontent.com/wallacepnts/quadlet-homelab/main/apps/freshrss/freshrss.container

# 2. Data directory — a bind mount requires it to exist before the start
mkdir -p ~/.config/containers/volumes/freshrss/data

# 3. Non-secret env — download the example, adjust TZ if needed
mkdir -p ~/.config/containers/env
wget -O ~/.config/containers/env/freshrss.env \
  https://raw.githubusercontent.com/wallacepnts/quadlet-homelab/main/apps/freshrss/.env.example

# 4. Start it
systemctl --user daemon-reload
systemctl --user start freshrss
```

Open `http://<host-ip>:8104` (ou via [tsdproxy](../tsdproxy/) em
`https://freshrss.<your-tailnet>.ts.net`) e completar o assistente de
installation wizard on first access — choose **SQLite** as the database (it
is already selected by default) and create the admin account there.

</details>

## Auto-update

No `AutoUpdate=` — an explicit tag (`1.29.1-alpine`), bumped by hand
([rule 9](../../docs/conventions.md)). The image has a real healthcheck
(`cli/health.php`) — `AutoUpdate=registry` could be enabled with working
rollback, but saved feeds and articles are the user's real data, the same
reasoning as [Radicale](../radicale/)/[vaultwarden](../vaultwarden/) — review
by hand before updating.

## Backup & recovery

```bash
systemctl --user stop freshrss
tar -czf freshrss-backup-$(date +%Y%m%d-%H%M%S).tar.gz \
  -C ~/.config/containers/volumes freshrss
systemctl --user start freshrss
```

## Useful commands

```bash
systemctl --user status freshrss
podman logs -f freshrss
podman exec freshrss php cli/health.php
podman exec --user www-data freshrss php cli/actualize-feeds.php   # force a manual refresh
```

## Credits

Quadlet deploy based on [FreshRSS](https://github.com/FreshRSS/FreshRSS)
(AGPL-3.0).
