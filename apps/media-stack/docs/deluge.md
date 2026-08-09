# Deluge

<img src="https://cdn.jsdelivr.net/gh/homarr-labs/dashboard-icons/svg/deluge.svg" width="64" height="64" alt="">

**[🇧🇷 Leia em português](./pt-BR/deluge.md)**

[< Media Stack](../README.md)

Downloads torrents. Runs on its own; the VPN is a separate choice.

Port **8112**, unit `media-stack-deluge`.

The web interface asks for a password on the first visit — upstream's default is `deluge`, and it asks you to change it. Set the download folder to `/data/downloads`.

Port 6881 is published, TCP and UDP, so other peers can connect in. Without it downloads still work, but slower.

To send its traffic through a VPN, swap the commented lines in `media-stack-deluge.container` and `media-stack-gluetun.container`. It is a swap and not an addition: the two cannot publish 8112 at the same time.

## Install

```bash
qh media-stack-deluge
qh media-stack-deluge --apply
```

Installing the folder — `qh media-stack --apply` — brings this one along with the rest.

## Files

```
media-stack-deluge.container   unit
.env.example                   environment, shared with the whole folder
```

Data in `~/.config/containers/volumes/media-stack/deluge/config`.

## Update

```bash
qh media-stack-deluge --update --apply
```

Pinned to `2.2.0`. Nothing updates on its own — a new version is applied when
you run the command above.

## Backup

```bash
qh media-stack-deluge --backup --apply --out ~/backups
```

The archive holds this unit's directories only. The folder's shared `.env` stays out, so restoring one app cannot hand an old copy back to the other eleven.

It stops this unit, packs it and starts it again. Cold on purpose: copying a
live database gives an archive that only fails when you restore it.

```bash
qh media-stack-deluge --restore ~/backups/media-stack-deluge-20260809-1200.tar.gz --apply
```

Restoring asks you to type `media-stack-deluge` to confirm, because the current data is
deleted before the archive is unpacked.

## Remove

```bash
qh media-stack-deluge --remove --apply           # stops it, keeps the data
qh media-stack-deluge --remove --purge --apply   # and deletes its volume
```

Only what belongs to this unit: the shared `.env` and the other apps of the
folder are left alone.

## Commands

```bash
systemctl --user status media-stack-deluge
podman logs -f deluge
qh media-stack-deluge --update --apply
```

## Credits

[Deluge](https://github.com/deluge-torrent/deluge) — GPL-3.0

[Official documentation](https://deluge.readthedocs.io/)
