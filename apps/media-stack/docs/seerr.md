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
qh media-stack --backup --apply --out ~/backups
```

Backup acts on the whole folder, not on one unit — naming `media-stack-seerr` here is
refused. The archive holds every app of `media-stack`, and restoring it is
`qh media-stack --restore <file> --apply`.

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
