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
qh media-stack --backup --apply --out ~/backups
```

Backup acts on the whole folder, not on one unit — naming `media-stack-deluge` here is
refused. The archive holds every app of `media-stack`, and restoring it is
`qh media-stack --restore <file> --apply`.

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
