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
qh media-stack --backup --apply --out ~/backups
```

Backup acts on the whole folder, not on one unit — naming `media-stack-jellyfin` here is
refused. The archive holds every app of `media-stack`, and restoring it is
`qh media-stack --restore <file> --apply`.

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
