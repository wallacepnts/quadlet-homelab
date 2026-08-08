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
The script creates the directories, writes the `.env`, generates the secrets,
fixes the volumes' ownership, starts the service and prints the address at the
end — see [Installing and operating](../../docs/installing.md).

Open `http://<host-ip>:8927` (or through [tsdproxy](../tsdproxy/) at
`https://vaultzap.<your-tailnet>.ts.net`). Drop the WhatsApp exports into
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

## Protecting it with a password (enabled)

**It is enabled in this deploy.** Access asks for a username and password
through the dialog
nativo do navegador (`WWW-Authenticate: Basic realm="vaultzap"`), tanto
em `http://<ip-do-host>:8927` quanto pela tailnet — o
[tsdproxy](../tsdproxy/) forwards the `Authorization` header with no extra
configuration.

```bash
mkdir -p ~/.config/containers/secrets/vaultzap
printf 'user:strong-password' > ~/.config/containers/secrets/vaultzap/basic-auth.txt
chmod 600 ~/.config/containers/secrets/vaultzap/basic-auth.txt
podman secret create vaultzap-basic-auth ~/.config/containers/secrets/vaultzap/basic-auth.txt
```

### `printf`, not `echo`

Upstream accepts two forms, `VAULTZAP_BASIC_AUTH` (the value directly) and
`VAULTZAP_BASIC_AUTH_FILE` (a path), and **refuses both together** — it exits
with `set VAULTZAP_BASIC_AUTH or VAULTZAP_BASIC_AUTH_FILE, not both`, rather
than letting one silently win.

The difference that bites: **the `_FILE` form trims whitespace, the direct one
does not.** This unit uses the direct one (`type=env`, see below), so an
`echo` in place of the `printf` puts a `\n` at the end of the password — and
then the login fails forever with the right password typed, with no helpful
message.

The format is `user:password`, split at the first `:`; either side being empty
takes the start down with `invalid VAULTZAP_BASIC_AUTH`.

### Why `type=env` and not `type=mount`

The "natural" way would be mounting the secret as a file and using the `_FILE`
form. **It does not work with `ReadOnly=true`**, and not even a `Tmpfs=/run`
fixes it — Podman creates the mountpoint against the rootfs before the tmpfs
takes effect:

```
error mounting ... to rootfs at "/run/secrets/vaultzap_basic_auth":
make mountpoint: read-only file system
```

Tested both ways. `type=env` delivers the value without touching the
filesystem, and `podman inspect` shows only the secret's name, not its value.

### The healthcheck keeps working

`/healthz` sits **outside** the authentication middleware on purpose — in
upstream's `main.go` it is registered on the outer mux, and the authenticated
handler is mounted at `/`. `HealthCmd=["/vaultzap", "healthcheck"]` hits
exactly that URL, with no credentials, so turning Basic Auth on does not break
`Notify=healthy`. Confirmed after enabling it: `healthy`.

### Changing the password

```bash
printf 'user:new-password' > ~/.config/containers/secrets/vaultzap/basic-auth.txt
podman secret rm vaultzap-basic-auth
podman secret create vaultzap-basic-auth ~/.config/containers/secrets/vaultzap/basic-auth.txt
systemctl --user restart vaultzap
```

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
