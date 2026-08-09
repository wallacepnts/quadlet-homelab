# Bazarr

<img src="https://cdn.jsdelivr.net/gh/homarr-labs/dashboard-icons/svg/bazarr.svg" width="64" height="64" alt="">

**[🇧🇷 Leia em português](./pt-BR/bazarr.md)**

[< Media Stack](../README.md)

Fetches subtitles for what Sonarr and Radarr brought in.

Port **6767**, unit `media-stack-bazarr`.

Settings -> Sonarr and Settings -> Radarr, with the address (`http://sonarr:8989`) and the API key of each. Then Settings -> Languages, choose the languages, and Settings -> Providers, choose where to look.

It reads the library through the *arr apps, so it only sees what they know about. A file dropped into the folder by hand does not show up.

## Install

```bash
qh media-stack-bazarr
qh media-stack-bazarr --apply
```

Installing the folder — `qh media-stack --apply` — brings this one along with the rest.

## Files

```
media-stack-bazarr.container   unit
.env.example                   environment, shared with the whole folder
```

Data in `~/.config/containers/volumes/media-stack/bazarr/config`.

## Update

```bash
qh media-stack-bazarr --update --apply
```

Pinned to `1.6.0`. Nothing updates on its own — a new version is applied when
you run the command above.

## Backup

```bash
qh media-stack-bazarr --backup --apply --out ~/backups
```

The archive holds this unit's directories only. The folder's shared `.env` stays out, so restoring one app cannot hand an old copy back to the other eleven.

It stops this unit, packs it and starts it again. Cold on purpose: copying a
live database gives an archive that only fails when you restore it.

```bash
qh media-stack-bazarr --restore ~/backups/media-stack-bazarr-20260809-1200.tar.gz --apply
```

Restoring asks you to type `media-stack-bazarr` to confirm, because the current data is
deleted before the archive is unpacked.

## Remove

```bash
qh media-stack-bazarr --remove --apply           # stops it, keeps the data
qh media-stack-bazarr --remove --purge --apply   # and deletes its volume
```

Only what belongs to this unit: the shared `.env` and the other apps of the
folder are left alone.

## Commands

```bash
systemctl --user status media-stack-bazarr
podman logs -f bazarr
qh media-stack-bazarr --update --apply
```

## Credits

[Bazarr](https://github.com/morpheus65535/bazarr) — GPL-3.0

[Official documentation](https://wiki.bazarr.media/)
