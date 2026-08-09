# SABnzbd

<img src="https://cdn.jsdelivr.net/gh/homarr-labs/dashboard-icons/svg/sabnzbd.svg" width="64" height="64" alt="">

**[🇧🇷 Leia em português](./pt-BR/sabnzbd.md)**

[< Media Stack](../README.md)

Downloads from Usenet. Needs a paid provider — Usenet is not free.

Port **8081**, unit `media-stack-sabnzbd`.

The wizard asks for the provider's server, user and password. Then set the folders to `/data/downloads`, so the *arr apps file the result with a rename instead of a copy.

The interface is on 8081 on the host and on 8080 inside the container — that is the address the *arr apps want.

## Install

```bash
qh media-stack-sabnzbd
qh media-stack-sabnzbd --apply
```

Installing the folder — `qh media-stack --apply` — brings this one along with the rest.

## Files

```
media-stack-sabnzbd.container   unit
.env.example                    environment, shared with the whole folder
```

Data in `~/.config/containers/volumes/media-stack/sabnzbd/config`.

## Update

```bash
qh media-stack-sabnzbd --update --apply
```

Pinned to `version-5.0.4`. Nothing updates on its own — a new version is applied when
you run the command above.

## Backup

```bash
qh media-stack-sabnzbd --backup --apply --out ~/backups
```

The archive holds this unit's directories only. The folder's shared `.env` stays out, so restoring one app cannot hand an old copy back to the other eleven.

It stops this unit, packs it and starts it again. Cold on purpose: copying a
live database gives an archive that only fails when you restore it.

```bash
qh media-stack-sabnzbd --restore ~/backups/media-stack-sabnzbd-20260809-1200.tar.gz --apply
```

Restoring asks you to type `media-stack-sabnzbd` to confirm, because the current data is
deleted before the archive is unpacked.

## Remove

```bash
qh media-stack-sabnzbd --remove --apply           # stops it, keeps the data
qh media-stack-sabnzbd --remove --purge --apply   # and deletes its volume
```

Only what belongs to this unit: the shared `.env` and the other apps of the
folder are left alone.

## Commands

```bash
systemctl --user status media-stack-sabnzbd
podman logs -f sabnzbd
qh media-stack-sabnzbd --update --apply
```

## Credits

[SABnzbd](https://github.com/sabnzbd/sabnzbd) — GPL-2.0

[Official documentation](https://sabnzbd.org/wiki/)
