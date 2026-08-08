# LubeLogger — Podman Quadlet (rootless)

**[🇧🇷 Leia em português](./README.pt-BR.md)**

A [LubeLogger](https://lubelogger.com) (vehicle maintenance tracking)
veicular self-hosted) via Podman Quadlet, migrado do `docker-compose.yml`
oficial.

## Architecture

A single container, with an embedded database by default (no Postgres — it
can be configured via `POSTGRES_CONNECTION` if you want, not used here). It
exposes `8080` internally (mapped to `8083` on the host — `8080`/`8082` are
already taken
por [tsdproxy](../tsdproxy/)/[vaultwarden](../vaultwarden/) neste
in this repository).

Dois volumes, como no compose oficial:
- `/App/data` — the application's data
- `/root/.aspnet/DataProtection-Keys` — ASP.NET's encryption keys
  (cookies/sessions); losing them invalidates active sessions, which is not
  destructive to the data but is worth avoiding needlessly

## Files

```
lubelogger.container   # main unit
```

## Prerequisites

- Rootless Podman with systemd `--user` working

## Installation

```bash
python3 install.py lubelogger            # dry-run: shows what it will do
python3 install.py lubelogger --apply
```

For the local network only, `--access local`; on the tailnet and the LAN,
`--access both`. Adding `--href-local` points the dashboard link at the LAN.
The script creates the directories, writes the `.env`, generates the secrets,
fixes the volumes' ownership, starts the service and prints the address at the
end — see [Installing and operating](../../docs/installing.md).

Reach it through [tsdproxy](../tsdproxy/) (tailnet) at
`https://lubelogger.<your-tailnet>.ts.net`, ou local em
`http://localhost:8083`.

<details>
<summary><b>Manual installation</b> (advanced) — the same steps, one at a time</summary>


```bash
# 1. Download the unit (no need to clone the repository)
mkdir -p ~/.config/containers/systemd
wget -P ~/.config/containers/systemd/ \
  https://raw.githubusercontent.com/wallacepnts/quadlet-homelab/main/apps/lubelogger/lubelogger.container

# 2. Data directories — a bind mount requires them to exist before the start
mkdir -p ~/.config/containers/volumes/lubelogger/{data,keys}

# 3. Env — download the example and edit the domain
mkdir -p ~/.config/containers/env
wget -O ~/.config/containers/env/lubelogger.env \
  https://raw.githubusercontent.com/wallacepnts/quadlet-homelab/main/apps/lubelogger/.env.example
# edit ~/.config/containers/env/lubelogger.env: LUBELOGGER_DOMAIN

# 4. Start it
systemctl --user daemon-reload
systemctl --user start lubelogger
```

Reach it through [tsdproxy](../tsdproxy/) (tailnet) at
`https://lubelogger.<your-tailnet>.ts.net`, ou local em
`http://localhost:8083`.

</details>

## Security — enabling authentication is manual, and it is not automatic

**By default, LubeLogger requires no login at all** — anyone who reaches the
URL has full read/write access, with no password. The documentation itself
confirms it: "LubeLogger does not require authentication by
default".

There is a way to preconfigure this through env vars
(`EnableAuth`/`UserNameHash`/`UserPasswordHash`, the SHA256 hash of the
username and password), but the docs themselves mark that method as no longer
recommended, and SHA256 without a salt or iterations is a weak hash for a
password — **that approach is not used here**. The official and safer route is
through the interface itself:

1. Open the instance for the first time
2. Ir em **Settings → Enable Authentication**
3. Set the Root/Super User's username and password right there

**Do this immediately after the first start**, before entering any real data
— even being on the tailnet alone (not exposed to the public internet), "only"
means "any device with access to that tailnet", which is still more exposure
than zero authentication deserves.

## Auto-update

No `AutoUpdate=` — an explicit tag (`v1.7.0`), bumped by hand
(rule 9 of the [conventions](../../docs/conventions.md)). The image is Ubuntu but has no `curl` or `wget` — the `HealthCmd` uses a raw
TCP check via bash (rule 13, `/dev/tcp` instead of an HTTP client).

## Backup & recovery

```bash
systemctl --user stop lubelogger
tar -czf lubelogger-backup-$(date +%Y%m%d-%H%M%S).tar.gz \
  -C ~/.config/containers/volumes lubelogger
systemctl --user start lubelogger
```

## Useful commands

```bash
systemctl --user status lubelogger
podman logs -f lubelogger
```

## Credits

Quadlet deploy based on [LubeLogger](https://github.com/hargata/lubelog).
Original licence: MIT.
