# Gitea — Podman Quadlet (rootless)

**[🇧🇷 Leia em português](./README.pt-BR.md)**

A [Gitea](https://gitea.com) (self-hosted Git forge) deploy via
Podman Quadlet, baseado no [guia oficial de Docker](https://docs.gitea.com/installation/install-with-docker).

## This deploy's decisions

- **Embedded SQLite**, not an external Postgres. Unlike
  [immich](../immich/), this is personal/homelab use — SQLite is what Gitea
  itself recommends for that scenario; Postgres only earns the extra
  complexity (another container, more secrets) in production with several
  concurrent users.
- **No Git over SSH** — HTTP/HTTPS only. The container's port `22` (Gitea's
  internal SSH) is not published; it simplifies the setup and avoids a
  long-term
  gerenciar mais uma porta exposta. Clone/push funcionam normalmente via
  HTTPS with a username and password, or a token.

## Architecture

A single container, Alpine + s6-overlay. A single volume (`/data`) holds the
SQLite database, the repositories, the configuration (`app.ini`) and the
attachments.

## Files

```
gitea.container   # main unit
```

## Prerequisites

- Rootless Podman with systemd `--user` working

## Installation

```bash
python3 install.py gitea            # dry-run: shows what it will do
python3 install.py gitea --apply
```

For the local network only, `--access local`; on the tailnet and the LAN,
`--access both`. Adding `--href-local` points the dashboard link at the LAN.
The script creates the directories, writes the `.env`, generates the secrets,
fixes the volumes' ownership, starts the service and prints the address at the
end — see [Installing and operating](../../docs/installing.md).

Reach it through [tsdproxy](../tsdproxy/) (tailnet) at
`https://gitea.<your-tailnet>.ts.net`, or locally at
`http://localhost:3002` — the root redirects to the installation wizard the
first time (like [owncloud](../owncloud/)); with `DB_TYPE`/`DOMAIN`/`ROOT_URL`
already prefilled by the env, all that is left is creating the admin account.

<details>
<summary><b>Manual installation</b> (advanced) — the same steps, one at a time</summary>


```bash
# 1. Download the unit (no need to clone the repository)
mkdir -p ~/.config/containers/systemd
wget -P ~/.config/containers/systemd/ \
  https://raw.githubusercontent.com/wallacepnts/quadlet-homelab/main/apps/gitea/gitea.container

# 2. Data directory — a bind mount requires it to exist before the start
mkdir -p ~/.config/containers/volumes/gitea/data

# 3. Secrets — generated with the image itself; Gitea uses its own format
#    (this is not a generic openssl rand)
mkdir -p ~/.config/containers/secrets/gitea
podman run --rm docker.io/gitea/gitea:1.27.1 gitea generate secret SECRET_KEY \
  > ~/.config/containers/secrets/gitea/secret-key.txt
podman run --rm docker.io/gitea/gitea:1.27.1 gitea generate secret INTERNAL_TOKEN \
  > ~/.config/containers/secrets/gitea/internal-token.txt
chmod 600 ~/.config/containers/secrets/gitea/*.txt

podman secret create gitea-secret-key ~/.config/containers/secrets/gitea/secret-key.txt
podman secret create gitea-internal-token ~/.config/containers/secrets/gitea/internal-token.txt

# 4. Non-secret env — download the example
#    installation: the DB and the domain come out right, all that is left
#    is creating the admin account in the UI)
mkdir -p ~/.config/containers/env
wget -O ~/.config/containers/env/gitea.env \
  https://raw.githubusercontent.com/wallacepnts/quadlet-homelab/main/apps/gitea/.env.example
# edit ~/.config/containers/env/gitea.env: GITEA__server__DOMAIN and
# GITEA__server__ROOT_URL

# 5. Start it
systemctl --user daemon-reload
systemctl --user start gitea
```

Reach it through [tsdproxy](../tsdproxy/) (tailnet) at
`https://gitea.<your-tailnet>.ts.net`, or locally at
`http://localhost:3002` — the root redirects to the installation wizard the
first time (like [owncloud](../owncloud/)); with `DB_TYPE`/`DOMAIN`/`ROOT_URL`
already prefilled by the env, all that is left is creating the admin account.

**Local access only (no tsdproxy)?** Change `GITEA__server__DOMAIN` and
`GITEA__server__ROOT_URL` in `gitea.env` to
`localhost`/`http://localhost:3002/` before the first start — just like
[karakeep](../karakeep/)'s `NEXTAUTH_URL`, `ROOT_URL` gets written into
`app.ini` after the installation; changing it later means editing that file
directly (see
`~/.config/containers/volumes/gitea/data/gitea/conf/app.ini`).

</details>

## Enabling Git over SSH later, if you change your mind

Add to the `.container`:

```ini
PublishPort=2222:22
```

E no `gitea.env`:

```
GITEA__server__SSH_DOMAIN=gitea.<your-tailnet>.ts.net
GITEA__server__SSH_PORT=2222
```

`2222`, not `22` — the host's standard port stays free for a real sshd, if
one is ever enabled (the same caution as the rest of this repo).

## Auto-update

No `AutoUpdate=` — an explicit tag (`1.27.1`), bumped by hand
(rule 9 of the [conventions](../../docs/conventions.md)). An Alpine image with `wget` and a real `HealthCmd` configured — genuine
auto-update could be enabled, but Gitea releases sometimes require a database
migration on the way up (the same kind of caution as
[immich](../immich/)); review by hand before changing version.

## Backup & recovery

A single volume, but with SQLite live — stopping the container first avoids
copying the database mid-write (the same reasoning as the incident documented
in [any-sync-bundle's README](../any-sync-bundle/README.md)):

```bash
systemctl --user stop gitea
tar -czf gitea-backup-$(date +%Y%m%d-%H%M%S).tar.gz \
  -C ~/.config/containers/volumes gitea
systemctl --user start gitea
```

The secrets (`~/.config/containers/secrets/gitea/`) need a separate backup
too — without the original `SECRET_KEY`/`INTERNAL_TOKEN`, user passwords and
access tokens stored in the restored database cannot be decrypted.

## Useful commands

```bash
systemctl --user status gitea
podman logs -f gitea
podman exec gitea gitea admin user list
```

## Credits

Quadlet deploy based on [Gitea](https://github.com/go-gitea/gitea).
Original licence: MIT.
