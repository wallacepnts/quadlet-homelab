# Radarr

<img src="https://cdn.jsdelivr.net/gh/homarr-labs/dashboard-icons/svg/radarr.svg" width="64" height="64" alt="">

**[🇧🇷 Leia em português](./pt-BR/radarr.md)**

[< Media Stack](../README.md)

The same as Sonarr, for films.

Port **7878**, unit `media-stack-radarr`.

Same setup: a root folder inside `/data` (`/data/media/movies`), a download client, and the indexers coming from Prowlarr.

Sonarr and Radarr are separate on purpose — a film and a series are named and organised by different rules.

## Install

```bash
qh media-stack-radarr
qh media-stack-radarr --apply
```

Installing the folder — `qh media-stack --apply` — brings this one along with the rest.

## Files

```
media-stack-radarr.container   unit
.env.example                   environment, shared with the whole folder
```

Data in `~/.config/containers/volumes/media-stack/radarr/config`.

## Update

```bash
qh media-stack-radarr --update --apply
```

Pinned to `6.3.0`. Nothing updates on its own — a new version is applied when
you run the command above.

## Backup

```bash
qh media-stack-radarr --backup --apply --out ~/backups
```

The archive holds this unit's directories only. The folder's shared `.env` stays out, so restoring one app cannot hand an old copy back to the other eleven.

It stops this unit, packs it and starts it again. Cold on purpose: copying a
live database gives an archive that only fails when you restore it.

```bash
qh media-stack-radarr --restore ~/backups/media-stack-radarr-20260809-1200.tar.gz --apply
```

Restoring asks you to type `media-stack-radarr` to confirm, because the current data is
deleted before the archive is unpacked.

## Remove

```bash
qh media-stack-radarr --remove --apply           # stops it, keeps the data
qh media-stack-radarr --remove --purge --apply   # and deletes its volume
```

Only what belongs to this unit: the shared `.env` and the other apps of the
folder are left alone.

## Commands

```bash
systemctl --user status media-stack-radarr
podman logs -f radarr
qh media-stack-radarr --update --apply
```

## Credits

[Radarr](https://github.com/Radarr/Radarr) — GPL-3.0

[Official documentation](https://wiki.servarr.com/radarr)
