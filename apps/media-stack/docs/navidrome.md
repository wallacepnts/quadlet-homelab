# Navidrome

<img src="https://cdn.jsdelivr.net/gh/homarr-labs/dashboard-icons/svg/navidrome.svg" width="64" height="64" alt="">

**[🇧🇷 Leia em português](./pt-BR/navidrome.md)**

[< Media Stack](../README.md)

Plays the music Lidarr and Downtify put in the media root. It speaks the
Subsonic API, so any of its clients works on a phone, including offline sync —
which is the part Jellyfin does not do well.

Port **4533**, unit `media-stack-navidrome`.

The media root is mounted **read-only** at `/music`, and Navidrome scans all of
it. On a big library, point it at just the music with
`ND_MUSICFOLDER=/music/media/music` in `media-stack.env`.

The first account you create is the administrator. Scanning happens on start
and every hour after that.

## Install

```bash
qh media-stack-navidrome
qh media-stack-navidrome --apply
```

Installing the folder — `qh media-stack --apply` — brings this one along with
the rest.

## Files

```
media-stack-navidrome.container   unit
.env.example                      environment, shared with the whole folder
```

Data in `~/.config/containers/volumes/media-stack/navidrome/data`.

## Update

```bash
qh media-stack-navidrome --update --apply
```

Pinned to `0.63.2`. Nothing updates on its own — a new version is applied when
you run the command above.

## Backup

```bash
qh media-stack-navidrome --backup --apply --out ~/backups
```

The archive holds this unit's directory only — the play counts, the ratings
and the accounts. The music itself is in the media root, which is not this
unit's to pack.

```bash
qh media-stack-navidrome --restore ~/backups/media-stack-navidrome-20260810-1200.tar.gz --apply
```

## Remove

```bash
qh media-stack-navidrome --remove --apply           # stops it, keeps the data
qh media-stack-navidrome --remove --purge --apply   # and deletes its volume
```

Only what belongs to this unit: the shared `.env` and the music are left alone.

## Commands

```bash
systemctl --user status media-stack-navidrome
podman logs -f navidrome
qh media-stack-navidrome --update --apply
```

## Credits

[Navidrome](https://github.com/navidrome/navidrome) — GPL-3.0

[Official documentation](https://www.navidrome.org/docs/)
