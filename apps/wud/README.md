# WUD (What's Up Docker) — Podman Quadlet (rootless)

**[🇧🇷 Leia em português](./README.pt-BR.md)**

Deploy do [What's Up Docker](https://getwud.github.io/wud/) via Podman
Quadlet — observa as imagens de todos os containers do host e avisa
when a newer version exists, **applying nothing by itself**.

## Why this, when `podman-auto-update` exists?

They are different things. `AutoUpdate=registry` only works on **floating**
tags (`:latest`, `:2`) and only knows how to compare the same tag's digest —
it does not exist for pinned tags. Most services in this repo deliberately sit
on a pinned tag plus a manual bump (see the "Services in this repository"
section and [rule 9](../../docs/conventions.md)) — WUD covers exactly that
ponto cego: ele detecta que existe uma tag `v2.15.1` mesmo quando o
the container is pinned at `v2.9.3`, and it only reports. Deciding whether
and when
atualizar continua manual.

## Architecture

A single container. It reads the Podman socket (via `podman.socket`, the
same mechanism [tsdproxy](../tsdproxy/) and [Homepage](../homepage/) already
use) purely to list containers and images — **read-only** access (`:ro`). It
keeps its history and config in `/store` (its own volume, which has to persist
across restarts).

## Files

```
wud.container   # main unit
```

## Prerequisites

- Rootless Podman with systemd `--user` working
- `podman.socket` enabled (already required if
  [tsdproxy](../tsdproxy/)/[homepage](../homepage/) are installed — the same
  socket, reused)

## Installation

```bash
python3 install.py wud            # dry-run: shows what it will do
python3 install.py wud --apply
```

For the local network only, `--access local`; on the tailnet and the LAN,
`--access both`. Adding `--href-local` points the dashboard link at the LAN.
The script creates the directories, writes the `.env`, generates the secrets,
fixes the volumes' ownership, starts the service and prints the address at the
end — see [Installing and operating](../../docs/installing.md).

Acessar em `http://localhost:8085` ou, via tailnet,
`https://wud.<your-tailnet>.ts.net`.

<details>
<summary><b>Manual installation</b> (advanced) — the same steps, one at a time</summary>


```bash
# 1. Download the unit (no need to clone the repository)
mkdir -p ~/.config/containers/systemd
wget -P ~/.config/containers/systemd/ \
  https://raw.githubusercontent.com/wallacepnts/quadlet-homelab/main/apps/wud/wud.container

# 2. Data directory — a bind mount requires it to exist before the start
mkdir -p ~/.config/containers/volumes/wud/store

# 3. Env — download the example. The check schedule (cron): WUD's own
#    default is hourly; daily is enough for most homelabs and generates far
#    less traffic against the registries.
mkdir -p ~/.config/containers/env
wget -O ~/.config/containers/env/wud.env \
  https://raw.githubusercontent.com/wallacepnts/quadlet-homelab/main/apps/wud/.env.example

# 4. The Podman socket
systemctl --user enable --now podman.socket

# 5. Start it
systemctl --user daemon-reload
systemctl --user start wud
```

Open it at `http://localhost:8085` or, over the tailnet, at
`https://wud.<your-tailnet>.ts.net`.

</details>

## Authentication

With no `WUD_AUTH_BASIC_*` configured, WUD itself logs a warning
("Anonymous authentication is enabled") e libera acesso sem senha —
the same trust model Homepage already uses here (no authentication of its
own, protected only by being on the tailnet). To switch to basic
authentication, see
[WUD's auth documentation](https://getwud.github.io/wud/#/configuration/authentications/basic).

## Non-semver tags are not watched

Containers on a non-semver floating tag (`:latest`, say) show up in the log as
"not a semver and digest watching is disabled" — WUD cannot tell whether there
is an update in that case unless `wud.watch.digest=true`
seja setado como label no container observado (compara digest em vez de
the version). It is not needed for this repo's services, which almost all
sit on a pinned semver tag — it is just a case to bear in mind if some new
service uses `:latest`.

## Filtrando quais containers observar (`wud.watch`)

By default WUD watches everything. To restrict it to what matters (the
services deliberately left without `AutoUpdate=`, say — see the table in the
[conventions](../../docs/conventions.md)), invert the default in `wud.env`:

```
WUD_WATCHER_LOCAL_WATCHBYDEFAULT=false
```

And mark each container you want with `Label=wud.watch=true` in its own
`.container` (not here — in the watched service).

## `wud.tag.include`/`wud.tag.transform`: no backslash in the value

Tags with a variant suffix (`0.10.1-nginx-php8.2` from
[vaultwarden](../vaultwarden/), say) fool WUD's semver parser — it treats the
suffix as a "prerelease" and a suffixless tag (`0.10.1`, a different variant
of the same image) shows up as "newer". The fix is to restrict the candidates
with `wud.tag.include` (a regex), but **Quadlet's** own parser does not accept
a backslash in `Label=` (`quadlet-generator: unsupported escape char` in the
journal — the entire line is silently discarded, with no visible error in
`systemctl cat` or `podman inspect`). Write the regex without `\d`/`\.` — use
`[0-9]` in place of `\d`, and leave the `.` unescaped (it matches any
character there, harmless for this kind of filter):

```ini
Label=wud.tag.include=^[0-9]+.[0-9]+.[0-9]+-nginx-php[0-9.]+$
```

## Auto-update

No `AutoUpdate=` — an explicit tag (`8.3.1`), bumped by hand
(rule 9 of the [conventions](../../docs/conventions.md)). Irony aside (this is the update-watching tool itself), this repository's
default is the same for everything: review by hand before changing version.

## Useful commands

```bash
systemctl --user status wud
podman logs -f wud
```

## Credits

Quadlet deploy based on [What's Up Docker](https://github.com/getwud/wud),
de [fmartinou](https://github.com/fmartinou). Original licence: MIT.
