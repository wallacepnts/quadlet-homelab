# Gluetun

<img src="https://cdn.jsdelivr.net/gh/homarr-labs/dashboard-icons/svg/gluetun.svg" width="64" height="64" alt="">

**[🇧🇷 Leia em português](./pt-BR/gluetun.md)**

[< Media Stack](../README.md)

**Optional.** A VPN tunnel to put Deluge inside. Nothing in the stack depends on it.

Unit `media-stack-gluetun`.

Installed with the folder and idle until configured. Fill `~/.config/containers/env/media-stack-gluetun.env` with the provider, the key and the server — the file that ships is an example, and `WIREGUARD_ADDRESSES` has a placeholder that has to be replaced.

Then uncomment the ports and the labels in this unit and comment the matching ones in `media-stack-deluge.container`. Deluge stops having an interface of its own: it reuses this container's network stack, and the address on the host becomes Gluetun's.

It runs `--privileged` because it creates a network interface and rewrites the routing table. It is the only container in this repository that does.

## Install

```bash
qh media-stack-gluetun
qh media-stack-gluetun --apply
```

Installing the folder — `qh media-stack --apply` — brings this one along with the rest.

## Files

```
media-stack-gluetun.container     unit
media-stack-gluetun.env.example   environment
```

## Update

```bash
qh media-stack-gluetun --update --apply
```

Pinned to `latest`. Nothing updates on its own — a new version is applied when
you run the command above.

## Backup

```bash
qh media-stack-gluetun --backup --apply --out ~/backups
```

The archive holds this unit's directories, its secrets and its own `.env` — nothing a sibling also reads.

It stops this unit, packs it and starts it again. Cold on purpose: copying a
live database gives an archive that only fails when you restore it.

```bash
qh media-stack-gluetun --restore ~/backups/media-stack-gluetun-20260809-1200.tar.gz --apply
```

Restoring asks you to type `media-stack-gluetun` to confirm, because the current data is
deleted before the archive is unpacked.

## Remove

```bash
qh media-stack-gluetun --remove --apply
```

It owns no volume, so `--purge` has nothing extra to delete here. The shared
`.env` and the other apps of the folder are left alone.

## Commands

```bash
systemctl --user status media-stack-gluetun
podman logs -f gluetun
qh media-stack-gluetun --update --apply
```

## Credits

[Gluetun](https://github.com/qdm12/gluetun) — MIT

[Official documentation](https://github.com/qdm12/gluetun/wiki)
