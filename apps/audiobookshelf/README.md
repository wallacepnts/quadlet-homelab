# Audiobookshelf — Podman Quadlet (rootless)

**[🇧🇷 Leia em português](./README.pt-BR.md)**

Deploy do [Audiobookshelf](https://audiobookshelf.org) (servidor de
audiolivros e podcasts, com progresso de leitura sincronizado entre
dispositivos) via Podman Quadlet, seguindo o
[guia oficial de Docker](https://audiobookshelf.org/docs/documentation/install/docker/).

## Architecture

A single container, running as root internally (the image does not support
`PUID`/`PGID` — unlike most of the LSIO/Alpine images here, that is by the
project's own design). Four volumes:

- `config` — the SQLite database and the migration scripts.
- `metadata` — book metadata, covers and author images, logs, backups.
- `audiobooks` / `podcasts` — the media libraries themselves (two examples
  from the official guide; other folders can be pointed at later through the
  UI, as long as they are local bind mounts too).

**A warning from the official documentation**: `config`/`metadata` have to be
on the host's own local disk, never on a network share (NFS/SMB) — it "can
cause performance issues and database corruption". This repository's local
bind mount already satisfies that; it only needs revisiting if those paths
ever move off the local disk.

## Files

```
audiobookshelf.container     # main unit
```

## Prerequisites

- Rootless Podman with systemd `--user` working

## Installation

```bash
python3 install.py audiobookshelf            # dry-run: shows what it will do
python3 install.py audiobookshelf --apply
```

For the local network only, `--access local`; on the tailnet and the LAN,
`--access both`. Adding `--href-local` points the dashboard link at the LAN.
The script creates the directories, writes the `.env`, generates the secrets,
fixes the volumes' ownership, starts the service and prints the address at the
end — see [Installing and operating](../../docs/installing.md).

Open it at `http://<host-ip>:13378` (ou via [tsdproxy](../tsdproxy/)
em `https://audiobookshelf.<your-tailnet>.ts.net`) e criar a conta admin
no primeiro acesso.

<details>
<summary><b>Manual installation</b> (advanced) — the same steps, one at a time</summary>


```bash
# 1. Download the units (no need to clone the repository)
mkdir -p ~/.config/containers/systemd
wget -P ~/.config/containers/systemd/ \
  https://raw.githubusercontent.com/wallacepnts/quadlet-homelab/main/apps/audiobookshelf/audiobookshelf.container

# 2. Data directories — a bind mount requires them to exist before the start
mkdir -p ~/.config/containers/volumes/audiobookshelf/{config,metadata,audiobooks,podcasts}

# 3. Non-secret env — download the example, adjust TZ if needed
mkdir -p ~/.config/containers/env
wget -O ~/.config/containers/env/audiobookshelf.env \
  https://raw.githubusercontent.com/wallacepnts/quadlet-homelab/main/apps/audiobookshelf/.env.example

# 4. Start it
systemctl --user daemon-reload
systemctl --user start audiobookshelf
```

Open it at `http://<host-ip>:13378` (ou via [tsdproxy](../tsdproxy/)
em `https://audiobookshelf.<your-tailnet>.ts.net`) e criar a conta admin
no primeiro acesso.

Copiar os audiolivros/podcasts pra dentro de
`~/.config/containers/volumes/audiobookshelf/{audiobooks,podcasts}` e
create the matching libraries in the UI (Settings → Libraries).

</details>

## Auto-update

No `AutoUpdate=` — an explicit tag (`2.36.0`), bumped by hand
(rule 9 of the [conventions](../../docs/conventions.md)). The image has `wget` and a real healthcheck (its own `/healthcheck`
endpoint, tested in practice) — `AutoUpdate=registry` could be enabled with
genuine rollback, but it is kept manual as this repository's default.

## Backup & recovery

```bash
systemctl --user stop audiobookshelf
tar -czf audiobookshelf-backup-$(date +%Y%m%d-%H%M%S).tar.gz \
  -C ~/.config/containers/volumes audiobookshelf
systemctl --user start audiobookshelf
```

`audiobooks/` and `podcasts/` tend to be large — consider excluding them
from the tarball and backing them up separately if only the progress and
metadata matter for the routine backup.

## Useful commands

```bash
systemctl --user status audiobookshelf
podman logs -f audiobookshelf
podman exec audiobookshelf wget -qO- http://127.0.0.1:80/healthcheck
```

## Credits

Quadlet deploy based on
[Audiobookshelf](https://github.com/advplyr/audiobookshelf) (GPL-3.0).
