# Dispatcharr

<img src="https://cdn.jsdelivr.net/gh/homarr-labs/dashboard-icons/svg/dispatcharr.svg" width="64" height="64" alt="">

**[🇧🇷 Leia em português](./pt-BR/dispatcharr.md)**

[< Media Stack](../README.md)

IPTV: organises channel lists, the guide and video on demand.

Port **9191**, unit `media-stack-dispatcharr`.

Apart from the chain: it does not use Prowlarr, the *arr apps or the download clients, and it keeps its own data instead of writing to the media root.

Add the M3U list and the EPG source in the interface. It carries Postgres and Redis inside the same container, which is why it is one unit and not three.

## Install

```bash
qh media-stack-dispatcharr
qh media-stack-dispatcharr --apply
```

Installing the folder — `qh media-stack --apply` — brings this one along with the rest.

## Files

```
media-stack-dispatcharr.container   unit
```

Data in `~/.config/containers/volumes/media-stack/dispatcharr/data`.

## Update

```bash
qh media-stack-dispatcharr --update --apply
```

Pinned to `latest`. Nothing updates on its own — a new version is applied when
you run the command above.

## Backup

```bash
qh media-stack-dispatcharr --backup --apply --out ~/backups
```

The archive holds this unit's directories, its secrets and its own `.env` — nothing a sibling also reads.

It stops this unit, packs it and starts it again. Cold on purpose: copying a
live database gives an archive that only fails when you restore it.

```bash
qh media-stack-dispatcharr --restore ~/backups/media-stack-dispatcharr-20260809-1200.tar.gz --apply
```

Restoring asks you to type `media-stack-dispatcharr` to confirm, because the current data is
deleted before the archive is unpacked.

## Remove

```bash
qh media-stack-dispatcharr --remove --apply           # stops it, keeps the data
qh media-stack-dispatcharr --remove --purge --apply   # and deletes its volume
```

Only what belongs to this unit: the shared `.env` and the other apps of the
folder are left alone.

## Commands

```bash
systemctl --user status media-stack-dispatcharr
podman logs -f dispatcharr
qh media-stack-dispatcharr --update --apply
```

## Credits

[Dispatcharr](https://github.com/Dispatcharr/Dispatcharr) — CC-BY-NC-SA-4.0

[Official documentation](https://dispatcharr.github.io/Dispatcharr-Docs/)
