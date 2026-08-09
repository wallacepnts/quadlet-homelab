# Seerr

<img src="https://cdn.jsdelivr.net/gh/homarr-labs/dashboard-icons/svg/seerr.svg" width="64" height="64" alt="">

**[🇧🇷 Leia em português](./pt-BR/seerr.md)**

[< Media Stack](../README.md)

Where a title is asked for. It hands the request to Sonarr or Radarr and reports back when it lands.

Port **5055**, unit `media-stack-seerr`.

The wizard asks for Jellyfin first (`http://jellyfin:8096`), then for Sonarr and Radarr. Each of those wants its API key, in Settings -> General of the app itself.

This is the piece to hand to someone who should ask for things without touching the rest. It is the only one in the stack meant for more than one person.

## Install

```bash
qh media-stack-seerr
qh media-stack-seerr --apply
```

Installing the folder — `qh media-stack --apply` — brings this one along with the rest.

## Files

```
media-stack-seerr.container   unit
.env.example                  environment, shared with the whole folder
```

Data in `~/.config/containers/volumes/media-stack/seerr/config`.

## Update

```bash
qh media-stack-seerr --update --apply
```

Pinned to `v3.4.1`. Nothing updates on its own — a new version is applied when
you run the command above.

## Backup

```bash
qh media-stack-seerr --backup --apply --out ~/backups
```

The archive holds this unit's directories only. The folder's shared `.env` stays out, so restoring one app cannot hand an old copy back to the other eleven.

It stops this unit, packs it and starts it again. Cold on purpose: copying a
live database gives an archive that only fails when you restore it.

```bash
qh media-stack-seerr --restore ~/backups/media-stack-seerr-20260809-1200.tar.gz --apply
```

Restoring asks you to type `media-stack-seerr` to confirm, because the current data is
deleted before the archive is unpacked.

## Remove

```bash
qh media-stack-seerr --remove --apply           # stops it, keeps the data
qh media-stack-seerr --remove --purge --apply   # and deletes its volume
```

Only what belongs to this unit: the shared `.env` and the other apps of the
folder are left alone.

## Commands

```bash
systemctl --user status media-stack-seerr
podman logs -f seerr
qh media-stack-seerr --update --apply
```

## Credits

[Seerr](https://github.com/seerr-team/seerr) — MIT

[Official documentation](https://docs.seerr.dev/)
