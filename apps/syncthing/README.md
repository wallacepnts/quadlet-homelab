# Syncthing — Podman Quadlet (rootless)

**[🇧🇷 Leia em português](./README.pt-BR.md)**

A [Syncthing](https://syncthing.net) (P2P file sync
P2P entre dispositivos, sem servidor central/nuvem de terceiros) via
Podman Quadlet, seguindo o
[guia oficial de Docker](https://github.com/syncthing/syncthing/blob/main/README-Docker.md).

## Architecture

A single container. PUID/PGID (the LSIO-like default, with no
`UserNS=keep-id` — the image adjusts the volume's owner on the first start). A
single volume (`/var/syncthing`) holds the config, the keys and — by default —
the synced folders themselves (`Sync/` inside it); additional folders from
outside can be pointed at later through the UI.

**A bridge network, not `host`**: the official guide recommends
`network_mode: host` so LAN peer discovery works over broadcast — the same
trade-off already
feita pro [Home Assistant](../home-assistant/)/Jellyfin (no
[media-stack](../media-stack/)): it loses automatic LAN discovery and keeps
this repository's default network isolation. **Global** discovery (over the
internet, via Syncthing's own discovery server) keeps working normally; a
direct connection to a LAN peer still works if you configure the address by
hand on the remote device, it just is not automatic.

## Files

```
syncthing.container   # main unit
```

## Prerequisites

- Rootless Podman with systemd `--user` working

## Installation

```bash
python3 install.py syncthing            # dry-run: shows what it will do
python3 install.py syncthing --apply
```

For the local network only, `--access local`; on the tailnet and the LAN,
`--access both`. Adding `--href-local` points the dashboard link at the LAN.
The script creates the directories, writes the `.env`, generates the secrets,
fixes the volumes' ownership, starts the service and prints the address at the
end — see [Installing and operating](../../docs/installing.md).

Reach it through [tsdproxy](../tsdproxy/) (tailnet) at
`https://syncthing.<your-tailnet>.ts.net`, ou local em
`http://localhost:8384`.

<details>
<summary><b>Manual installation</b> (advanced) — the same steps, one at a time</summary>


```bash
# 1. Download the unit (no need to clone the repository)
mkdir -p ~/.config/containers/systemd
wget -P ~/.config/containers/systemd/ \
  https://raw.githubusercontent.com/wallacepnts/quadlet-homelab/main/apps/syncthing/syncthing.container

# 2. Data directory — a bind mount requires it to exist before the start
mkdir -p ~/.config/containers/volumes/syncthing/data
podman unshare chown -R 1000:1000 ~/.config/containers/volumes/syncthing   # a unit usa User=1000

# 3. Non-secret env — download the example
#    que roda o Podman (mesmo dono do volume acima)
mkdir -p ~/.config/containers/env
wget -O ~/.config/containers/env/syncthing.env \
  https://raw.githubusercontent.com/wallacepnts/quadlet-homelab/main/apps/syncthing/.env.example
sed -i "s/^PUID=.*/PUID=$(id -u)/;s/^PGID=.*/PGID=$(id -g)/" \
  ~/.config/containers/env/syncthing.env

# 4. Start it
systemctl --user daemon-reload
systemctl --user start syncthing
```

Reach it through [tsdproxy](../tsdproxy/) (tailnet) at
`https://syncthing.<your-tailnet>.ts.net`, ou local em
`http://localhost:8384`.

</details>

## Protecting the GUI (mandatory, right on first access)

**The official image has no environment variable to preconfigure the GUI's
username and password** (an open request since
[syncthing/syncthing#8791](https://github.com/syncthing/syncthing/issues/8791),
with no timeline) — Syncthing comes up with **no authentication at all** by
default, listening on `0.0.0.0`. Configure it straight in the UI as soon as
you first open it: **Actions → Settings → GUI**, fill in the username and
password, save (it restarts itself). Until you do, anyone who reaches port
8384 (the whole tailnet, not just you) has full access
— inclusive pra adicionar pastas/dispositivos.

## Auto-update

No `AutoUpdate=` — an explicit tag (`2.1.3`), bumped by hand
(rule 9 of the [conventions](../../docs/conventions.md)). A imagem tem `curl`/healthcheck real (daria pra habilitar
with genuine rollback), but the synced files are the user's real data —
review by hand before updating, the same reasoning as
[ownCloud](../owncloud/).

## Backup & recovery

```bash
systemctl --user stop syncthing
tar -czf syncthing-backup-$(date +%Y%m%d-%H%M%S).tar.gz \
  -C ~/.config/containers/volumes syncthing
systemctl --user start syncthing
```

`data/` includes both Syncthing's own config and keys and whatever synced
folders live inside it (`data/Sync/` by default) — if you point at folders
outside the volume through the UI, back those up separately.

## Useful commands

```bash
systemctl --user status syncthing
podman logs -f syncthing
podman exec syncthing curl -fkLsS -m 2 127.0.0.1:8384/rest/noauth/health
```

## Credits

Quadlet deploy based on [Syncthing](https://github.com/syncthing/syncthing).
Original licence: MPL-2.0.
