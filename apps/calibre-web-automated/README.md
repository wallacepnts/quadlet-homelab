# Calibre-Web-Automated — Podman Quadlet (rootless)

**[🇧🇷 Leia em português](./README.pt-BR.md)**

Deploy do [Calibre-Web-Automated](https://github.com/crocodilestick/Calibre-Web-Automated)
(a self-hosted ebook library — web reading plus automatic conversion and
metadata via Calibre) via Podman Quadlet, using the official image from
projeto.

## Architecture

A single container, on an image based on `linuxserver/baseimage-ubuntu` — it
uses
`PUID`/`PGID` (usermod interno, precisa rodar como root de verdade dentro
inside the container's own namespace), **not** `UserNS=keep-id`: the same
mecanismo dos containers LinuxServer.io do [media-stack](../media-stack/),
misturar os dois quebra a imagem.

Three volumes:
- `/config` — the application's configuration plus the database
  (`metadata.db`)
- `/cwa-book-ingest` — an **inbox** folder, not storage: anything dropped
  here is processed and imported into the library automatically,
  depois **removido** dessa pasta
- `/calibre-library` — a biblioteca de verdade; se estiver vazia no
  primeiro start, a imagem cria uma nova ali

It is deliberately kept out of the [media-stack](../media-stack/)'s shared
media root — there, the single root exists because Sonarr/Radarr/Lidarr
**movem** arquivo de `downloads/` pra `media/` (precisa ser o mesmo
filesystem, see the dedicated section in that README for why); here there is
no indexer or torrent feeding `/cwa-book-ingest` automatically, it is a manual
drop — the same cross-mount problem does not arise.

## Files

```
calibre-web-automated.container   # main unit
```

## Prerequisites

- Rootless Podman with systemd `--user` working
- If you already have an existing Calibre library: stop the old instance
  first and copy the folder into `volumes/.../library` (see Installation)

## Installation

```bash
python3 install.py calibre-web-automated            # dry-run: shows what it will do
python3 install.py calibre-web-automated --apply
```

For the local network only, `--access local`; on the tailnet and the LAN,
`--access both`. Adding `--href-local` points the dashboard link at the LAN.
The script creates the directories, writes the `.env`, generates the secrets,
fixes the volumes' ownership, starts the service and prints the address at the
end — see [Installing and operating](../../docs/installing.md).

Reach it through [tsdproxy](../tsdproxy/) (tailnet) at
`https://calibre-web.<your-tailnet>.ts.net`, ou local em
`http://localhost:8105`. The default username and password on first access:
`admin`/`admin123` — change it straight away in Settings.

<details>
<summary><b>Manual installation</b> (advanced) — the same steps, one at a time</summary>


```bash
# 1. Download the unit (no need to clone the repository)
mkdir -p ~/.config/containers/systemd
wget -P ~/.config/containers/systemd/ \
  https://raw.githubusercontent.com/wallacepnts/quadlet-homelab/main/apps/calibre-web-automated/calibre-web-automated.container

# 2. Data directories — a bind mount requires them to exist before the start
mkdir -p ~/.config/containers/volumes/calibre-web-automated/{config,ingest,library}

# 3. Non-secret env — download the example
#    que roda o Podman (mesmo dono dos volumes acima)
mkdir -p ~/.config/containers/env
wget -O ~/.config/containers/env/calibre-web-automated.env \
  https://raw.githubusercontent.com/wallacepnts/quadlet-homelab/main/apps/calibre-web-automated/.env.example
sed -i "s/^PUID=.*/PUID=$(id -u)/;s/^PGID=.*/PGID=$(id -g)/" \
  ~/.config/containers/env/calibre-web-automated.env

# 4. Start it
systemctl --user daemon-reload
systemctl --user start calibre-web-automated
```

Reach it through [tsdproxy](../tsdproxy/) (tailnet) at
`https://calibre-web.<your-tailnet>.ts.net`, ou local em
`http://localhost:8105`. The default username and password on first access:
`admin`/`admin123` — change it straight away in Settings.

**Migrating from a "plain" Calibre-Web**: stop the old instance and copy
a pasta de config dela pra dentro de `volumes/calibre-web-automated/config/`
before this one's first start — it loads the existing users and config.

**Plugins do Calibre** (opcional, WIP segundo o projeto): montar um quarto
volume `.../plugins:/config/.config/calibre/plugins:Z` e copiar
`customize.py.json` into `config/.config/calibre/` — not included by default
in this unit, as it is an advanced use case.

</details>

## Auto-update

No `AutoUpdate=` — an explicit tag (`v4.0.6`), bumped by hand
(rule 9 of the [conventions](../../docs/conventions.md)). A imagem tem `curl`/healthcheck real (daria pra habilitar
com rollback de verdade), mas a biblioteca inteira (banco `metadata.db` +
files) is the user's real data — review by hand before changing version, the
same reasoning as vaultwarden.

## Backup & recovery

```bash
systemctl --user stop calibre-web-automated
tar -czf calibre-web-automated-backup-$(date +%Y%m%d-%H%M%S).tar.gz \
  -C ~/.config/containers/volumes calibre-web-automated
systemctl --user start calibre-web-automated
```

`config/` (the database plus preferences) is what really matters;
`library/` tends to be the largest in size — consider separate backups if
the
biblioteca for grande.

## Useful commands

```bash
systemctl --user status calibre-web-automated
podman logs -f calibre-web-automated
```

## Credits

Deploy Quadlet usando a imagem oficial
[crocodilestick/Calibre-Web-Automated](https://github.com/crocodilestick/Calibre-Web-Automated)
(GPL-3.0).
