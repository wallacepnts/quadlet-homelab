# Prowlarr

<img src="https://cdn.jsdelivr.net/gh/homarr-labs/dashboard-icons/svg/prowlarr.svg" width="64" height="64" alt="">

**[🇧🇷 Leia em português](./pt-BR/prowlarr.md)**

[< Media Stack](../README.md)

Holds the indexer list in one place and pushes it to Sonarr, Radarr and Lidarr.

Port **9696**, unit `media-stack-prowlarr`.

Add the indexers here, then Settings -> Apps, one entry per *arr app with its address (`http://sonarr:8989`) and its API key. From then on an indexer added here appears in all of them.

Configure this one first. Doing the *arr apps before it means adding every indexer three times, and then again whenever one changes.

## Install

```bash
qh media-stack-prowlarr
qh media-stack-prowlarr --apply
```

Installing the folder — `qh media-stack --apply` — brings this one along with the rest.

## Files

```
media-stack-prowlarr.container   unit
.env.example                     environment, shared with the whole folder
```

Data in `~/.config/containers/volumes/media-stack/prowlarr/config`.

## Update

```bash
qh media-stack-prowlarr --update --apply
```

Pinned to `2.5.2`. Nothing updates on its own — a new version is applied when
you run the command above.

## Backup

```bash
qh media-stack --backup --apply --out ~/backups
```

Backup acts on the whole folder, not on one unit — naming `media-stack-prowlarr` here is
refused. The archive holds every app of `media-stack`, and restoring it is
`qh media-stack --restore <file> --apply`.

## Remove

```bash
qh media-stack-prowlarr --remove --apply           # stops it, keeps the data
qh media-stack-prowlarr --remove --purge --apply   # and deletes its volume
```

Only what belongs to this unit: the shared `.env` and the other apps of the
folder are left alone.

## Commands

```bash
systemctl --user status media-stack-prowlarr
podman logs -f prowlarr
qh media-stack-prowlarr --update --apply
```

## Credits

[Prowlarr](https://github.com/Prowlarr/Prowlarr) — GPL-3.0

[Official documentation](https://wiki.servarr.com/prowlarr)
