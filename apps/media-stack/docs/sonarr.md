# Sonarr

<img src="https://cdn.jsdelivr.net/gh/homarr-labs/dashboard-icons/svg/sonarr.svg" width="64" height="64" alt="">

**[🇧🇷 Leia em português](./pt-BR/sonarr.md)**

[< Media Stack](../README.md)

Series: follows what you add, downloads new episodes and files them under the library.

Port **8989**, unit `media-stack-sonarr`.

Settings -> Media Management, add a root folder inside `/data` (for example `/data/media/tv`). Settings -> Download Clients, add SABnzbd (`sabnzbd:8080`) or Deluge (`deluge:8112`). The indexers arrive from Prowlarr.

Downloads land in `/data/downloads` and the library is under the same `/data`. That is the point of mounting the whole root once: filing a finished episode is a rename on the same filesystem, not a copy of several gigabytes.

## Install

```bash
qh media-stack-sonarr
qh media-stack-sonarr --apply
```

Installing the folder — `qh media-stack --apply` — brings this one along with the rest.

## Files

```
media-stack-sonarr.container   unit
.env.example                   environment, shared with the whole folder
```

Data in `~/.config/containers/volumes/media-stack/sonarr/config`.

## Update

```bash
qh media-stack-sonarr --update --apply
```

Pinned to `4.0.19`. Nothing updates on its own — a new version is applied when
you run the command above.

## Backup

```bash
qh media-stack --backup --apply --out ~/backups
```

Backup acts on the whole folder, not on one unit — naming `media-stack-sonarr` here is
refused. The archive holds every app of `media-stack`, and restoring it is
`qh media-stack --restore <file> --apply`.

## Remove

```bash
qh media-stack-sonarr --remove --apply           # stops it, keeps the data
qh media-stack-sonarr --remove --purge --apply   # and deletes its volume
```

Only what belongs to this unit: the shared `.env` and the other apps of the
folder are left alone.

## Commands

```bash
systemctl --user status media-stack-sonarr
podman logs -f sonarr
qh media-stack-sonarr --update --apply
```

## Credits

[Sonarr](https://github.com/Sonarr/Sonarr) — GPL-3.0

[Official documentation](https://wiki.servarr.com/sonarr)
