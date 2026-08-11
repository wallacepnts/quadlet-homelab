# Ferdium Server

<img src="https://cdn.jsdelivr.net/gh/homarr-labs/dashboard-icons/svg/ferdium.svg" width="64" height="64" alt="">

**[🇧🇷 Leia em português](./README.pt-BR.md)**

The server half of [Ferdium](https://github.com/ferdium/ferdium-app), the
desktop app that puts WhatsApp, Telegram, Slack and the rest into one window.
This is what keeps your list of services and your workspaces in sync between
machines — the job a Franz account would do, on your own hardware.

The desktop app itself is not here: it is an Electron program you install on
each machine, and it is what talks to this.

## Install

```bash
qh ferdium-server            # shows the plan
qh ferdium-server --apply
```

Then, in the Ferdium desktop app: **Settings → Ferdium account → Use custom
server**, pointing at `https://ferdium.<your-tailnet>.ts.net`. Create your
account, then set `IS_REGISTRATION_ENABLED=false` in the `.env` and run
`qh ferdium-server --update --apply` so nobody else can.

<details>
<summary><b>Manual install (advanced)</b></summary>

```bash
mkdir -p ~/.config/containers/systemd ~/.config/containers/env
mkdir -p ~/.config/containers/volumes/ferdium-server/data
mkdir -p ~/.config/containers/volumes/ferdium-server/recipes

wget -P ~/.config/containers/systemd/ \
  https://raw.githubusercontent.com/wallacepnts/quadlet-homelab/main/apps/ferdium-server/ferdium-server.container
wget -O ~/.config/containers/env/ferdium-server.env \
  https://raw.githubusercontent.com/wallacepnts/quadlet-homelab/main/apps/ferdium-server/.env.example
# edit ~/.config/containers/env/ferdium-server.env: APP_URL

systemctl --user daemon-reload
systemctl --user start ferdium-server
```

</details>

## Files

```
ferdium-server.container   unit
.env.example               environment
```

Two volumes. `data/` holds the SQLite database and the JWT keys the server
generates on first start — `FERDIUM_APP_KEY.txt` and the PEM pair. Lose those
and every client has to log in again, which is why they are on a volume and not
in the image.

`recipes/` is a git clone of
[ferdium-recipes](https://github.com/ferdium/ferdium-recipes), the definitions
of each service the app can embed. The entrypoint clones it on first start and
pulls on later ones, so the first boot takes about a minute and a half.

## The first start is slow

`TimeoutStartSec=300` is not padding: before serving anything the entrypoint
installs pnpm, clones the recipes and runs the database migrations. Around 90
seconds on a cold volume, and `HealthStartPeriod=180s` covers it.

## Hardening

`DropCapability=ALL` as root. Two rungs above that were tried and refused:

- `ReadOnly=true` — the entrypoint clones the recipes with git and writes
  `/home/node/.gitconfig`: `could not create work tree dir 'recipes':
  Read-only file system`.
- `User=1000` — it installs pnpm globally on every start:
  `EACCES: permission denied, mkdir '/usr/local/lib/node_modules/pnpm'`.

## Update

```bash
qh ferdium-server --update --apply
```

Pinned to `2.0.13`.

## Backup

```bash
qh ferdium-server --backup --apply --out ~/backups
```

Stops it, packs both volumes and the `.env`, starts it again. The recipes are a
git clone and would come back on their own, but the database and the keys are
the account itself.

To restore, over the current data:

```bash
qh ferdium-server --restore ~/backups/ferdium-server-20260811-1200.tar.gz --apply
```

## Remove

```bash
qh ferdium-server --remove --apply           # stops it, keeps the accounts
qh ferdium-server --remove --purge --apply   # and deletes both volumes
```

## Commands

```bash
systemctl --user status ferdium-server
podman logs -f ferdium-server

# how many accounts exist
podman exec ferdium-server sh -c \
  "sqlite3 /data/ferdium.sqlite 'select count(*) from users'" 2>/dev/null
```

## Credits

[ferdium/ferdium-server](https://github.com/ferdium/ferdium-server) — MIT.

[Official documentation](https://github.com/ferdium/ferdium-server#readme)
