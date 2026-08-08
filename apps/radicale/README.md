# Radicale — Podman Quadlet (rootless)

**[🇧🇷 Leia em português](./README.pt-BR.md)**

A [Radicale](https://radicale.org) (a light, minimal CalDAV/CardDAV server —
calendars and contacts) deploy via Podman Quadlet, using the
[tomsquest/docker-radicale](https://github.com/tomsquest/docker-radicale)
image (far more hardened than average: a read-only root filesystem,
capabilities cut to the minimum, no new privileges).

It is this repository's CalDAV/CardDAV service: calendars and contacts synced
between phone, desktop and any client that speaks the protocol.

## Architecture

A single container. A **read-only** root filesystem — only `/data` (the
data: calendars, contacts) is writable; `/config` is mounted `:ro` on purpose
(the config itself should not change at run time). Capabilities:
`DropCapability=all` plus only `chown`/`setuid`/`setgid` (the entrypoint
adjusts `/data`'s owner on the first start) and `kill` (the internal
supervisor) — all of it replicated from the official compose, which is already
deliberately restrictive.

Authentication through **htpasswd** (`/config/config` + `/config/users`) —
without it, Radicale runs with **no authentication at all** by default
(`auth type = none`), so configuring that from the first start matters —
Radicale has no installation wizard forcing an account to be created.

**`config/config` has to be the complete file**, not just the `[auth]`
section — mounting it at `/config/config` **replaces** the image's default
config entirely, it does not merge. The image only works because its built-in
default has `filesystem_folder = /data/collections` (inside the only writable
volume); a custom `config/config` without that line makes Radicale fall back
to the software default (`/var/lib/radicale/collections`), which is on the
read-only root filesystem — tested in practice, it hangs with `[Errno 30]
Read-only file system` at start. This repository's `config/config` is already
the complete file, with only the `[auth]` section changed from `type = none`
to `htpasswd`.

## Files

```
radicale.container   # main unit

config/
└── config            # the complete config file (not just auth) — from this repo

birthday-calendar/
└── create_birthday_calendar.py   # a vendored script, see Credits

birthday-sync/
├── radicale-birthday-sync.service # runs the script above via "podman exec"
└── radicale-birthday-sync.timer   # fires the service periodically
```

`config/users` (the password hash) does **not** come from the repository — it
is generated in step 3 of the installation and never versioned
([rule 2](../../docs/conventions.md)).

## Prerequisites

- Rootless Podman with systemd `--user` working
- `python3` with the `bcrypt` module (`pip3 install --user bcrypt`) — only to
  generate the password hash during installation

## Installation

```bash
python3 install.py radicale            # dry-run: shows what it will do
python3 install.py radicale --apply
```

For the local network only, `--access local`; on the tailnet and the LAN,
`--access both`. Adding `--href-local` points the dashboard link at the LAN.
The script creates the directories, writes the `.env`, generates the secrets,
fixes the volumes' ownership, starts the service and prints the address at the
end — see [Installing and operating](../../docs/installing.md).

Reach it through [tsdproxy](../tsdproxy/) (tailnet) at
`https://radicale.<your-tailnet>.ts.net`, or locally at
`http://localhost:5232` — it asks for the username and password created in
step 3. The CalDAV/CardDAV addresses for clients:
`https://radicale.<your-tailnet>.ts.net/<user>/<collection-name>/` (the web UI
itself, reachable at the root, creates calendars and address books and shows
each one's exact link).

<details>
<summary><b>Manual installation</b> (advanced) — the same steps, one at a time</summary>


```bash
# 1. Download the unit (no need to clone the repository)
mkdir -p ~/.config/containers/systemd
wget -P ~/.config/containers/systemd/ \
  https://raw.githubusercontent.com/wallacepnts/quadlet-homelab/main/apps/radicale/radicale.container

# 2. Data directories — a bind mount requires them to exist before the start
mkdir -p ~/.config/containers/volumes/radicale/{data,config}
wget -O ~/.config/containers/volumes/radicale/config/config \
  https://raw.githubusercontent.com/wallacepnts/quadlet-homelab/main/apps/radicale/config/config

# 3. Username and password — a bcrypt hash generated locally, in htpasswd
#    format (user:hash, one per line). The /config/users file has to be
#    readable by any uid (world-readable) because the container runs with a
#    fixed internal uid (2999) that is not yours — with no UserNS=keep-id on
#    this image (see Architecture), that is the only way it can see the file.
read -p "Radicale username: " RADICALE_USER
read -s -p "Radicale password: " RADICALE_PW; echo
RADICALE_USER="$RADICALE_USER" RADICALE_PW="$RADICALE_PW" python3 -c "
import bcrypt, os
user = os.environ['RADICALE_USER']
pw = os.environ['RADICALE_PW'].encode()
h = bcrypt.hashpw(pw, bcrypt.gensalt()).decode()
print(f'{user}:{h}')
" > ~/.config/containers/volumes/radicale/config/users
unset RADICALE_PW
chmod 644 ~/.config/containers/volumes/radicale/config/users

# 4. Non-secret env — download the example
mkdir -p ~/.config/containers/env
wget -O ~/.config/containers/env/radicale.env \
  https://raw.githubusercontent.com/wallacepnts/quadlet-homelab/main/apps/radicale/.env.example

# 5. Start it
systemctl --user daemon-reload
systemctl --user start radicale
```

Reach it through [tsdproxy](../tsdproxy/) (tailnet) at
`https://radicale.<your-tailnet>.ts.net`, or locally at
`http://localhost:5232` — it asks for the username and password created in
step 3. The CalDAV/CardDAV addresses for clients:
`https://radicale.<your-tailnet>.ts.net/<user>/<collection-name>/` (the web UI
itself, reachable at the root, creates calendars and address books and shows
each one's exact link).

</details>

## Adding more users later

Repeat step 3 in append mode (`>>` instead of `>`), one line per user — the
`htpasswd_filename` accepts several lines, one account per line.

## An automatic birthday calendar

Based on
[iBigQ/radicale-birthday-calendar](https://github.com/iBigQ/radicale-birthday-calendar)
(MIT) — a script that reads the contacts with a birthday (`BDAY`) from all of
a user's address books and keeps a `birthdays` calendar permanently up to
date, recurring every year.

**Not through a hook** — the original project is designed around Radicale's
hook mechanism (`[storage] hook = <command>`, fired on every write), but this
version of Radicale (3.7.6) **removed** that generic mechanism: the hook
system is now plugin-based with only three built-in types
(`none`/`rabbitmq`/`email`), with no "run an arbitrary command" option —
tested in practice, and confirmed by reading the image's own source
(`radicale/hook/__init__.py`). Instead, this repository uses a **periodic
timer** (every 30 minutes, `radicale-birthday-sync.timer`) that sweeps all the
contacts via `podman exec` and regenerates the calendar — simpler, and it does
not depend on Radicale's internal (undocumented) hook API, at the cost of not
being instantaneous.

```bash
# 1. Download the script and the Python packages it needs (once only — they
#    cannot be installed into the default site-packages, since the root
#    filesystem is read-only, so they go into /data, referenced through the
#    PYTHONPATH already present in the .container)
mkdir -p ~/.config/containers/volumes/radicale/data/birthday-calendar
wget -O ~/.config/containers/volumes/radicale/data/birthday-calendar/create_birthday_calendar.py \
  https://raw.githubusercontent.com/wallacepnts/quadlet-homelab/main/apps/radicale/birthday-calendar/create_birthday_calendar.py
podman run --rm \
  -v ~/.config/containers/volumes/radicale/data:/data:Z \
  --entrypoint pip3 \
  docker.io/tomsquest/docker-radicale:3.7.6.0 \
  install --target=/data/python-libs --no-cache-dir vobject python-dateutil

# 2. Download and enable the timer (ordinary systemd, outside Quadlet)
wget -P ~/.config/systemd/user/ \
  https://raw.githubusercontent.com/wallacepnts/quadlet-homelab/main/apps/radicale/birthday-sync/radicale-birthday-sync.service \
  https://raw.githubusercontent.com/wallacepnts/quadlet-homelab/main/apps/radicale/birthday-sync/radicale-birthday-sync.timer
systemctl --user daemon-reload
systemctl --user enable --now radicale-birthday-sync.timer

# Test it by hand (no need to wait the 30 minutes)
systemctl --user start radicale-birthday-sync.service
```

Every user with a contact that has `BDAY` filled in gets a `birthdays`
calendar automatically on the first run — visible alongside the others at the
account's root, and syncable like any other CalDAV calendar.

**Optional variables** (`radicale.env`, see `.env.example`):
`BIRTHDAY_CALENDAR_COLOR` (the calendar's colour; without it, a random one is
picked on the first run) and `BIRTHDAY_REMINDER_AT_HOUR` (a reminder N hours
before midnight on the birthday).

## Troubleshooting

**`error setting cgroup config ... memory.swap.max: no such file or
directory`** — the official compose limits it to `256M` of RAM
(`--memory=256m`), but that depends on the `memory` controller being delegated
to the user's cgroup (`systemd`/`logind`), which is not guaranteed under
rootless — tested in practice: on this host only `pids` is delegated (check
with `cat /sys/fs/cgroup/user.slice/user-$(id -u).slice/user@$(id -u).service/cgroup.controllers`).
That is why this repository's `.container` does **not** set `--memory`, only
`--pids-limit` (which does work). If your host has `memory` delegated, adding
`PodmanArgs=--memory=256m` back is safe.

## Auto-update

No `AutoUpdate=` — an explicit tag (`3.7.6.0`), bumped by hand
(rule 9 of the [conventions](../../docs/conventions.md)). The image has `curl` and a real healthcheck (it could be enabled with
genuine rollback), but calendars and contacts are the user's real data —
review by hand before updating, the same reasoning as vaultwarden.

## Backup & recovery

```bash
systemctl --user stop radicale
tar -czf radicale-backup-$(date +%Y%m%d-%H%M%S).tar.gz \
  -C ~/.config/containers/volumes radicale
systemctl --user start radicale
```

`config/users` is already included (it lives inside `volumes/radicale/`,
alongside `data/`).

## Useful commands

```bash
systemctl --user status radicale
podman logs -f radicale
podman exec radicale curl -fs http://127.0.0.1:5232
```

## Credits

A Quadlet deploy using the
[tomsquest/docker-radicale](https://github.com/tomsquest/docker-radicale)
image (MIT), of the [Radicale](https://github.com/Kozea/Radicale) project
(GPL-3.0). The birthday calendar is based on
[iBigQ/radicale-birthday-calendar](https://github.com/iBigQ/radicale-birthday-calendar)
(MIT).
