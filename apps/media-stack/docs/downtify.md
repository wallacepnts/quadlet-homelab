# Downtify

<img src="https://cdn.jsdelivr.net/gh/homarr-labs/dashboard-icons/png/downtify.png" width="64" height="64" alt="">

**[🇧🇷 Leia em português](./pt-BR/downtify.md)**

[< Media Stack](../README.md)

Paste a Spotify link and the music lands on disk.

Port **8000**, unit `media-stack-downtify`.

Writes straight into `/data/downloads`, the same folder the download clients use. It does not pass through Lidarr and nothing renames the result — it is the shortcut for one album, not a library.

That subdirectory has to exist before the first start, because it is bind-mounted on its own. The install creates it.

## Install

```bash
qh media-stack-downtify
qh media-stack-downtify --apply
```

Installing the folder — `qh media-stack --apply` — brings this one along with the rest.

## Files

```
media-stack-downtify.container   unit
```

Data in `~/.config/containers/volumes/media-stack/downtify/data`.

## Update

```bash
qh media-stack-downtify --update --apply
```

Pinned to `2.9.1`. Nothing updates on its own — a new version is applied when
you run the command above.

## Backup

```bash
qh media-stack --backup --apply --out ~/backups
```

Backup acts on the whole folder, not on one unit — naming `media-stack-downtify` here is
refused. The archive holds every app of `media-stack`, and restoring it is
`qh media-stack --restore <file> --apply`.

## Remove

```bash
qh media-stack-downtify --remove --apply           # stops it, keeps the data
qh media-stack-downtify --remove --purge --apply   # and deletes its volume
```

Only what belongs to this unit: the shared `.env` and the other apps of the
folder are left alone.

## Commands

```bash
systemctl --user status media-stack-downtify
podman logs -f downtify
qh media-stack-downtify --update --apply
```

## Credits

[Downtify](https://github.com/henriquesebastiao/downtify) — GPL-3.0

[Official documentation](https://github.com/henriquesebastiao/downtify#readme)
