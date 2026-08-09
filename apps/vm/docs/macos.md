# macOS

<img src="https://cdn.simpleicons.org/macos/888888" width="64" height="64" alt="">

**[🇧🇷 Leia em português](./pt-BR/macos.md)**

[< VMs](../README.md)

A macOS VM in the browser, from Big Sur to Sequoia.

Web viewer on **8008**, VNC on **5900**. Unit `vm-macos`.

The install asks which release. The recovery image is fetched from Apple on the first boot, and the installation itself is done by hand inside the viewer — Disk Utility to erase the virtual disk, then the installer.

There is no viewer password: whoever reaches port 8008 is inside the machine. The account is the one you create during macOS setup.

Apple's licence only permits macOS on Apple hardware. Running it here is your call, and the reason this VM ships no automation for it.

All of these need `/dev/kvm` on the host — without hardware virtualisation
the VM either refuses to start or crawls. `RAM_SIZE` is reserved for the whole
life of the VM, so leave the host enough to breathe; `DISK_SIZE` is a ceiling
and grows on demand.

## Install

```bash
qh vm-macos
qh vm-macos --apply
```

Installing the folder — `qh vm --apply` — brings this one along with the rest.

## Files

```
vm-macos.container     unit
vm-macos.env.example   environment
```

Data in `~/.config/containers/volumes/vm/macos/storage`.

## Update

```bash
qh vm-macos --update --apply
```

Pinned to `3.09`. Nothing updates on its own — a new version is applied when
you run the command above.

## Backup

```bash
qh vm --backup --apply --out ~/backups
```

Backup acts on the whole folder, not on one unit — naming `vm-macos` here is
refused. The archive holds every app of `vm`, and restoring it is
`qh vm --restore <file> --apply`.

## Remove

```bash
qh vm-macos --remove --apply           # stops it, keeps the data
qh vm-macos --remove --purge --apply   # and deletes its volume
```

Only the volumes of this VM. `vm-macos.env` is kept even though nothing else
reads it — a per-unit purge does not touch the environment file.

## Commands

```bash
systemctl --user status vm-macos
podman logs -f vm-macos
qh vm-macos --update --apply
```

## Credits

[macOS](https://github.com/dockur/macos) — MIT

[Official documentation](https://github.com/dockur/macos#readme)
