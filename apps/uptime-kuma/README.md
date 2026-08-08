# Uptime Kuma — Podman Quadlet (rootless)

**[🇧🇷 Leia em português](./README.pt-BR.md)**

Deploy do [Uptime Kuma](https://github.com/louislam/uptime-kuma) (monitor
de disponibilidade self-hosted) via Podman Quadlet, usando a imagem
oficial `docker.io/louislam/uptime-kuma`.

## Architecture

A single container (Node + embedded SQLite) — a single volume
(`/app/data`) holds the database, the uploads and the configuration.

**It is the most hardened service in the repository**: it took the maximum
level
testado — `ReadOnly=true`, `DropCapability=ALL` (zero capabilities) e
`User=1000`, that is, the process runs as non-root **inside** the
container e cai num uid de subuid (100999) **no host**, fora do seu
your own user. It is the only one in that band alongside beszel,
paperless-ngx and
immich-machine-learning.

The practical consequence: the volume has to belong to that mapped uid, and
that is done with `podman unshare chown` (step 2 of the installation) — an
ordinary `chown` on the host will not do, because the number 1000 inside the
namespace is not the 1000 outside it.

## Files

```
uptime-kuma.container   # main unit
```

## Prerequisites

- Rootless Podman with systemd `--user` working

## Installation

```bash
python3 install.py uptime-kuma            # dry-run: shows what it will do
python3 install.py uptime-kuma --apply
```

For the local network only, `--access local`; on the tailnet and the LAN,
`--access both`. Adding `--href-local` points the dashboard link at the LAN.
The script creates the directories, writes the `.env`, generates the secrets,
fixes the volumes' ownership, starts the service and prints the address at the
end — see [Installing and operating](../../docs/installing.md).

Open `http://<host-ip>:3005` (or through [tsdproxy](../tsdproxy/) at
`https://uptime-kuma.<your-tailnet>.ts.net`) — the first screen creates the
administrator account. **Create it before exposing anything**, the
installation stays open until you do.

<details>
<summary><b>Manual installation</b> (advanced) — the same steps, one at a time</summary>


```bash
# 1. Download the units (no need to clone the repository)
mkdir -p ~/.config/containers/systemd
wget -P ~/.config/containers/systemd/ \
  https://raw.githubusercontent.com/wallacepnts/quadlet-homelab/main/apps/uptime-kuma/uptime-kuma.container

# 2. Data directory, with the owner matching the unit's User=1000.
#    `podman unshare` runs the chown INSIDE the user namespace, which is
#    where the container's 1000 exists (on the host that becomes 100999).
mkdir -p ~/.config/containers/volumes/uptime-kuma/data
podman unshare chown -R 1000:1000 ~/.config/containers/volumes/uptime-kuma/data

# 3. Start it
systemctl --user daemon-reload
systemctl --user start uptime-kuma
```

Open `http://<host-ip>:3005` (or through [tsdproxy](../tsdproxy/) at
`https://uptime-kuma.<your-tailnet>.ts.net`) — the first screen creates the
administrator account. **Create it before exposing anything**, the
installation stays open until you do.

</details>

## Monitoring this repository's services

Every service here already publishes a port on the host and has a healthcheck
of its own.
Dois jeitos de apontar o monitor:

- **HTTP(s)** em `http://<ip-do-host>:<porta>` — usa a porta publicada da
  table in the [conventions](../../docs/conventions.md). It works for
  anything serving HTTP, and it is what gives a real response time.
- **HTTP(s)** na URL da tailnet (`https://<app>.<your-tailnet>.ts.net`) —
  tests the full path, tsdproxy included ([tsdproxy](../tsdproxy/)). It only
  works if the Uptime Kuma host is on the same tailnet (here it is — the same
  machine).

Monitorar pela porta local detecta "o container caiu"; monitorar pela
the tailnet URL also detects "tsdproxy went down" — worth having both on the
services that matter.

## Auto-update

No `AutoUpdate=` — an explicit tag (`2.5.0`), bumped by hand
(rule 9 of the [conventions](../../docs/conventions.md)). There is an extra reason here: a monitor that updates itself and breaks is
precisely the thing that will not tell you it broke.

## Backup & recovery

```bash
systemctl --user stop uptime-kuma
tar -czf uptime-kuma-backup-$(date +%Y%m%d-%H%M%S).tar.gz \
  -C ~/.config/containers/volumes uptime-kuma
systemctl --user start uptime-kuma
```

When restoring on another machine, redo step 2's `podman unshare chown`
after extracting — tar preserves the old uid, which may not be the
mesmo mapeamento no destino.

## Useful commands

```bash
systemctl --user status uptime-kuma
podman logs -f uptime-kuma
podman exec uptime-kuma extra/healthcheck && echo OK
```

## Credits

Quadlet deploy based on
[Uptime Kuma](https://github.com/louislam/uptime-kuma) de
[louislam](https://github.com/louislam) (MIT).
