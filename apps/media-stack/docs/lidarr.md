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
qh media-stack-lidarr --backup --apply --out ~/backups
```

The archive holds this unit's directories only. The folder's shared `.env` stays out, so restoring one app cannot hand an old copy back to the other eleven.

It stops this unit, packs it and starts it again. Cold on purpose: copying a
live database gives an archive that only fails when you restore it.

```bash
qh media-stack-lidarr --restore ~/backups/media-stack-lidarr-20260809-1200.tar.gz --apply
```

Restoring asks you to type `media-stack-lidarr` to confirm, because the current data is
deleted before the archive is unpacked.

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
