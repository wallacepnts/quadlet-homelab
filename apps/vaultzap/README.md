# VaultZap — Podman Quadlet (rootless)

**[🇧🇷 Leia em português](./README.pt-BR.md)**

Deploy do [VaultZap](https://github.com/wallacepnts/vaultzap) (arquivo
a local, browsable archive of exported WhatsApp conversations — full-text
search, a media gallery, a calendar) via Podman Quadlet.

**The unit comes from the project itself**
([`deploy/vaultzap.container`](https://github.com/wallacepnts/vaultzap/blob/main/deploy/vaultzap.container)),
which already publishes an official Quadlet and documents it in
[`docs/quadlet.md`](https://github.com/wallacepnts/vaultzap/blob/main/docs/quadlet.md).
Here it only gains what is convention in this repository: `ContainerName=`,
labels de [tsdproxy](../tsdproxy/) e [homepage](../homepage/), e
`Notify=healthy`. The rest is upstream — in a conflict, upstream wins.

## Architecture

A single container (a Go binary + SQLite), **one of the most locked down
here** — all of this comes from upstream:

```ini
UserNS=keep-id:uid=65532,gid=65532   # nonroot, mapped to your uid
ReadOnly=true                         # read-only root filesystem
Tmpfs=/tmp
NoNewPrivileges=true
DropCapability=ALL                    # no capabilities at all
```

Two volumes: `data/` (the `vaultzap.db` database plus imported media) and
`inbox/` (where you drop the `.zip` files exported from WhatsApp; the service
imports them and moves them to `.imported/`).

**With `AutoUpdate=registry` on** — the third case in this repository,
alongside [actual-budget](../actual-budget/) and [homepage](../homepage/). It
satisfies [rule 9](../../docs/conventions.md): it has a real `HealthCmd` (the
binary's own `healthcheck` subcommand), and here the "do not trust a third
party's release" criterion does not apply — the releases are yours. That is
also why it carries no `wud.watch`: auto-update already covers it.

## Files

```
vaultzap.container   # the unit (a copy of upstream + this repo's conventions)
.env.example         # the environment, from upstream's deploy/vaultzap.env.example
install.ini          # the upstream override for updates.py
```

## Prerequisites

- Rootless Podman with systemd `--user` working
- `TAILNET` set (see [homepage](../homepage/)), if you will use the
  dashboard

## Installation

```bash
python3 install.py vaultzap            # dry-run: shows what it will do
python3 install.py vaultzap --apply
```

For the local network only, `--access local`; on the tailnet and the LAN,
`--access both`. Adding `--href-local` points the dashboard link at the LAN.
The script creates the directories, writes the `.env`, fixes the volumes'
ownership, starts the service and prints the address at the end — see [Installing and operating](../../docs/installing.md).

Open `http://<host-ip>:8927` (or through [tsdproxy](../tsdproxy/) at
`https://vaultzap.<your-tailnet>.ts.net`) and **set the username and password
right away** — the first visit shows a setup screen, and until someone fills it
in, whoever reaches the port first can. Then drop the WhatsApp exports into
`~/.config/containers/volumes/vaultzap/inbox/` — the service imports them by
itself.

<details>
<summary><b>Manual installation</b> (advanced) — the same steps, one at a time</summary>


```bash
# 1. Download the unit (a single file -> it goes loose in systemd/)
mkdir -p ~/.config/containers/systemd
wget -P ~/.config/containers/systemd/ \
  https://raw.githubusercontent.com/wallacepnts/quadlet-homelab/main/apps/vaultzap/vaultzap.container

# 2. Directories — a bind mount requires them to exist before the start
mkdir -p ~/.config/containers/volumes/vaultzap/{data,inbox}

# 3. Env
mkdir -p ~/.config/containers/env
wget -O ~/.config/containers/env/vaultzap.env \
  https://raw.githubusercontent.com/wallacepnts/quadlet-homelab/main/apps/vaultzap/.env.example

# 4. The dashboard icon (the project has its own; there is no equivalent in
#    dashboard-icons)
mkdir -p ~/.config/containers/volumes/homepage/icons
wget -O ~/.config/containers/volumes/homepage/icons/vaultzap.svg \
  https://raw.githubusercontent.com/wallacepnts/vaultzap/main/internal/web/static/img/favicon.svg
systemctl --user restart homepage   # it only picks up a new icon after a restart

# 5. Start it
systemctl --user daemon-reload
systemctl --user start vaultzap
```

Open `http://<host-ip>:8927` (or through [tsdproxy](../tsdproxy/) at
`https://vaultzap.<your-tailnet>.ts.net`). Drop the WhatsApp exports into
`~/.config/containers/volumes/vaultzap/inbox/` — the service imports them by
itself.

</details>

## How access is protected

**A login screen, and it is upstream's default.** Nothing is configured here:
on the first visit to a new database the app shows a setup screen where you
pick a username and password. Only the hash is stored (PBKDF2-HMAC-SHA256,
with its own salt). After that the setup screen is gone, and the password is
changed under **Your profile → Change password**.

> **Set it up right after the first start.** Until someone does, whoever
> reaches the port first can. That is a real window, even narrowed to the
> tailnet. If you do not need it reachable from the network at all, publish on
> localhost only — `PublishPort=127.0.0.1:8927:8927`.

**There is no attempt limiter**, and upstream says why: a per-IP limiter behind
a reverse proxy either locks everyone out together (every request arrives with
the proxy's IP) or is sidestepped by changing a header. What protects the
archive is a good password.

### Lost the password

The binary handles it, without opening anything over the network:

```bash
podman exec vaultzap /vaultzap reset-password
```

It prints a new password, keeps the username and ends every open session.

### Turning authentication off

Only when something in front already guards the port. Uncomment in
`vaultzap.env`:

```
VAULTZAP_AUTH=off
```

### Basic Auth instead

The login screen replaced Basic Auth as the default, but Basic Auth still
works and **takes precedence** when its variable is set. This deploy shipped
that way until upstream added the login screen; the unit keeps the line
commented out for anyone who prefers the HTTP header to a session cookie.

```bash
mkdir -p ~/.config/containers/secrets/vaultzap
printf 'user:strong-password' > ~/.config/containers/secrets/vaultzap/basic-auth.txt
chmod 600 ~/.config/containers/secrets/vaultzap/basic-auth.txt
podman secret create vaultzap-basic-auth ~/.config/containers/secrets/vaultzap/basic-auth.txt
```

Then uncomment the `Secret=` line in the unit and restart.

Three things about that path are measured and still true:

**`printf`, not `echo`.** Upstream accepts `VAULTZAP_BASIC_AUTH` (the value)
and `VAULTZAP_BASIC_AUTH_FILE` (a path), and refuses both together rather than
letting one silently win. The `_FILE` form trims whitespace, the direct one
does not — and this unit uses the direct one, so an `echo` leaves a `\n` at
the end of the password. The login then fails forever with the right password
typed, and no message says why.

Setting `VAULTZAP_BASIC_AUTH` to an **empty** value is now an error at boot
rather than silently disabling authentication. To run without a password, leave
the variable out and use `VAULTZAP_AUTH=off`.

**`type=env`, not `type=mount`.** The natural way would be mounting the secret
as a file and using the `_FILE` form. It **does not work with `ReadOnly=true`**,
and not even a `Tmpfs=/run` fixes it — Podman creates the mountpoint against
the rootfs before the tmpfs takes effect:

```
error mounting ... to rootfs at "/run/secrets/vaultzap_basic_auth":
make mountpoint: read-only file system
```

Tested both ways. `type=env` delivers the value without touching the
filesystem, and `podman inspect` shows only the secret's name, not its value.
Upstream's own quadlet suggests the `_FILE` form in its commented block; that
is the form to avoid here.

**The healthcheck keeps working either way.** `/healthz` sits **outside** the
authentication middleware on purpose — in upstream's `main.go` it is registered
on the outer mux, and the authenticated handler is mounted at `/`.
`HealthCmd=["/vaultzap", "healthcheck"]` hits exactly that URL, with no
credentials, so no authentication mode breaks `Notify=healthy`.

## Auto-update

**On** (`AutoUpdate=registry` + the `latest` tag) — see "Architecture" above
for why. It depends on the host's timer, enabled once:

```bash
systemctl --user enable --now podman-auto-update.timer
podman auto-update --dry-run   # a preview, applying nothing
```

To pin to a specific version, change `Image=` to an exact tag and remove the
`AutoUpdate=` line.

## Backup & recovery

```bash
systemctl --user stop vaultzap
tar -czf vaultzap-backup-$(date +%Y%m%d-%H%M%S).tar.gz \
  -C ~/.config/containers/volumes vaultzap
systemctl --user start vaultzap
```

`data/vaultzap.db` is ordinary SQLite — it can be opened with `sqlite3`
directly, without the service running.

## Useful commands

```bash
systemctl --user status vaultzap
podman logs -f vaultzap
podman exec vaultzap /vaultzap healthcheck
```

## Credits

[VaultZap](https://github.com/wallacepnts/vaultzap) (AGPL-3.0), de
[wallacepnts](https://github.com/wallacepnts) — the unit in this directory is
the project's official one, with this repository's conventions layered on
top.
