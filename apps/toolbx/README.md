# Toolbx

<img src="https://cdn.jsdelivr.net/gh/containers/containertoolbx.org@main/apple-touch-icon.png" width="64" height="64" alt="">

**[🇧🇷 Leia em português](./README.pt-BR.md)**

Disposable Arch, Fedora, RHEL and Ubuntu shells, on the official Toolbx images — somewhere to install a one-off tool that is not the host.

## Install

```bash
qh toolbx            # shows the plan
qh toolbx --apply
```

## Files

```
toolbx-arch.container
toolbx-fedora.container
toolbx-rhel.container
toolbx-ubuntu.container
install.ini
```

Units in this stack:

- `toolbx-arch`
- `toolbx-fedora`
- `toolbx-rhel`
- `toolbx-ubuntu`

## Update

```bash
qh toolbx --update --apply
```

Pinned to `10.2`, `26.04`, `38d89c96265cfa7d6795c2e6f4b5b803df3e1f3d934fcfbabb346153aabdf985`. Nothing updates on its own — a new version is applied
when you run the command above.

## Backup

```bash
qh toolbx --backup --apply --out ~/backups
```

It stops the service, packs the data, the `.env` and the secrets, and starts
it again. Cold on purpose: copying a live database gives an archive that only
fails when you restore it.

To restore, over the current data:

```bash
qh toolbx --restore ~/backups/toolbx-20260809-1200.tar.gz --apply
```

It asks you to type `toolbx` to confirm, because the current data is deleted
before the archive is unpacked.

## Remove

```bash
qh toolbx --remove --apply           # stops it, keeps the data
qh toolbx --remove --purge --apply   # and deletes volumes, secrets and .env
```

`--purge` asks for the typed name too. The tailnet node is not deregistered by
this — that is done in the Tailscale admin.

## Commands

```bash
systemctl --user status toolbx
podman logs -f toolbx
```

## Credits

[containers/toolbox](https://containertoolbx.org/) — Apache-2.0

[Official documentation](https://containertoolbx.org/)
