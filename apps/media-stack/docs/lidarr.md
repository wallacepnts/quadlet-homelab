# Lidarr

<img src="https://cdn.jsdelivr.net/gh/homarr-labs/dashboard-icons/svg/lidarr.svg" width="64" height="64" alt="">

**[🇧🇷 Leia em português](./pt-BR/lidarr.md)**

[< Media Stack](../README.md)

The same as Sonarr, for music: follows artists and fetches what comes out.

Port **8686**, unit `media-stack-lidarr`.

Same setup: a root folder inside `/data` (`/data/media/music`), a download client, and Prowlarr for indexers.

For grabbing one album or one track without following an artist, Downtify is the shorter path.

## Install

```bash
qh media-stack-lidarr
qh media-stack-lidarr --apply
```

Installing the folder — `qh media-stack --apply` — brings this one along with the rest.

## Files

```
media-stack-lidarr.container   unit
.env.example                   environment, shared with the whole folder
```

Data in `~/.config/containers/volumes/media-stack/lidarr/config`.

## Update

```bash
qh media-stack-lidarr --update --apply
```

Pinned to `3.1.0`. Nothing updates on its own — a new version is applied when
you run the command above.

## Backup

```bash
qh media-stack --backup --apply --out ~/backups
```

Backup acts on the whole folder, not on one unit — naming `media-stack-lidarr` here is
refused. The archive holds every app of `media-stack`, and restoring it is
`qh media-stack --restore <file> --apply`.

## Remove

```bash
qh media-stack-lidarr --remove --apply           # stops it, keeps the data
qh media-stack-lidarr --remove --purge --apply   # and deletes its volume
```

Only what belongs to this unit: the shared `.env` and the other apps of the
folder are left alone.

## Commands

```bash
systemctl --user status media-stack-lidarr
podman logs -f lidarr
qh media-stack-lidarr --update --apply
```

## Credits

[Lidarr](https://github.com/Lidarr/Lidarr) — GPL-3.0

[Official documentation](https://wiki.servarr.com/lidarr)
