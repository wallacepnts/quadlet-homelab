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
qh media-stack --backup --apply --out ~/backups
```

Backup acts on the whole folder, not on one unit — naming `media-stack-sabnzbd` here is
refused. The archive holds every app of `media-stack`, and restoring it is
`qh media-stack --restore <file> --apply`.

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
