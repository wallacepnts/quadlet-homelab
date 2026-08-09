# Jellyfin

<img src="https://cdn.jsdelivr.net/gh/homarr-labs/dashboard-icons/svg/jellyfin.svg" width="64" height="64" alt="">

**[🇧🇷 Leia em português](./pt-BR/jellyfin.md)**

[< Media Stack](../README.md)

Plays what the stack collected — films, series and music — in a browser, on a TV or on a phone.

Port **8096**, unit `media-stack-jellyfin`.

Open the port and run the wizard: create the administrator, then add one library per kind of content, pointing at the folders under `/data`.

The media root is mounted **read-only** here. Jellyfin plays and never writes, so a wrong click in the interface cannot delete the library — the *arr apps are what organise it.

## Install

```bash
qh media-stack-jellyfin
qh media-stack-jellyfin --apply
```

Installing the folder — `qh media-stack --apply` — brings this one along with the rest.

## Files

```
media-stack-jellyfin.container   unit
```

Data in `~/.config/containers/volumes/media-stack/jellyfin/config`, `~/.config/containers/volumes/media-stack/jellyfin/cache`.

## Update

```bash
qh media-stack-jellyfin --update --apply
```

Pinned to `10.11.11`. Nothing updates on its own — a new version is applied when
you run the command above.

## Backup

```bash
qh media-stack-jellyfin --backup --apply --out ~/backups
```

The archive holds this unit's directories, its secrets and its own `.env` — nothing a sibling also reads.

It stops this unit, packs it and starts it again. Cold on purpose: copying a
live database gives an archive that only fails when you restore it.

```bash
qh media-stack-jellyfin --restore ~/backups/media-stack-jellyfin-20260809-1200.tar.gz --apply
```

Restoring asks you to type `media-stack-jellyfin` to confirm, because the current data is
deleted before the archive is unpacked.

## Remove

```bash
qh media-stack-jellyfin --remove --apply           # stops it, keeps the data
qh media-stack-jellyfin --remove --purge --apply   # and deletes its volume
```

Only what belongs to this unit: the shared `.env` and the other apps of the
folder are left alone.

## Commands

```bash
systemctl --user status media-stack-jellyfin
podman logs -f jellyfin
qh media-stack-jellyfin --update --apply
```

## Credits

[Jellyfin](https://github.com/jellyfin/jellyfin) — GPL-2.0

[Official documentation](https://jellyfin.org/docs/)
