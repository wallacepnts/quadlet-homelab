# Omni Tools — Podman Quadlet (rootless)

**[🇧🇷 Leia em português](./README.pt-BR.md)**

Deploy do [Omni Tools](https://github.com/iib0011/omni-tools) (caixa de
ferramentas offline) via Podman Quadlet, usando a imagem oficial
`docker.io/iib0011/omni-tools`.

Converters, generators, calculators, image manipulation, JSON, text, dates,
hashes. It replaces those utility sites where you paste data — sometimes
sensitive data — into somebody else's server.

## Architecture

A single container, nginx serving a static app. **No volume and no
database, on purpose**: everything runs in the browser and the server only
delivers the files. Nothing you convert goes through the server — that is the
project's point, and it is what makes this service's backup "none".

### Hardening: herda os limites do nginx

Tested in practice, and the result is the same as this repository's
[nginx](../nginx/):

- `DropCapability=ALL` on its own is refused — `chown("/var/cache/nginx/client_temp", 101) failed (1: Operation not permitted)`
- `ReadOnly=true` is refused — `10-listen-on-ipv6-by-default.sh: can not modify /etc/nginx/conf.d/default.conf`

The nginx image's entrypoint rewrites config at start; it is the classic
case
citado na [regra 20](../../docs/conventions.md). O kit de 4 capabilities
(`CHOWN`, `SETUID`, `SETGID`, `NET_BIND_SERVICE`) is the minimum that comes
up.

### The tag is on Docker Hub, not on ghcr

`ghcr.io/iib0011/omni-tools` publishes **only `latest`** — the ghcr tag
listing returns a single entry. The numbered versions (`0.6.0`, `0.5.0`…) are
on Docker Hub, which is where this unit pulls from, so it can be pinned as
manda a regra 9.

## Files

```
omni-tools.container   # main unit
```

## Installation

```bash
python3 install.py omni-tools            # dry-run: shows what it will do
python3 install.py omni-tools --apply
```

For the local network only, `--access local`; on the tailnet and the LAN,
`--access both`. Adding `--href-local` points the dashboard link at the LAN.
The script creates the directories, writes the `.env`, generates the secrets,
fixes the volumes' ownership, starts the service and prints the address at the
end — see [Installing and operating](../../docs/installing.md).

Open `http://<host-ip>:8101` (ou via [tsdproxy](../tsdproxy/) em
`https://omni-tools.<your-tailnet>.ts.net`).

<details>
<summary><b>Manual installation</b> (advanced) — the same steps, one at a time</summary>


```bash
# 1. Download the unit (no need to clone the repository)
mkdir -p ~/.config/containers/systemd
wget -P ~/.config/containers/systemd/ \
  https://raw.githubusercontent.com/wallacepnts/quadlet-homelab/main/apps/omni-tools/omni-tools.container

# 2. Start it — sem mkdir, sem secret, sem env
systemctl --user daemon-reload
systemctl --user start omni-tools
```

Open `http://<host-ip>:8101` (ou via [tsdproxy](../tsdproxy/) em
`https://omni-tools.<your-tailnet>.ts.net`).

</details>

## Why this and not IT-Tools

[IT-Tools](https://github.com/CorentinTh/it-tools) is the better-known project
in this category, but it has stalled: its last release was in October 2024.
Omni Tools is the maintained alternative, with the same proposition.

## Auto-update

No `AutoUpdate=` — an explicit tag (`0.6.0`), bumped by hand
(rule 9 of the [conventions](../../docs/conventions.md)). This is one of the few where turning auto-update on would be defensible: no
state, no database migrations, and the HTTP healthcheck covers the rollback.
It still stays manual, for consistency (conventions, "Why most of it is
off").

## Backup & recovery

None. There is no state — reinstalling *is* the restore.

## Useful commands

```bash
systemctl --user status omni-tools
podman logs -f omni-tools
```

## Credits

Quadlet deploy based on
[Omni Tools](https://github.com/iib0011/omni-tools) de
[iib0011](https://github.com/iib0011) (MIT).
