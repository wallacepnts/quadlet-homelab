# QEMU

<img src="https://cdn.jsdelivr.net/gh/homarr-labs/dashboard-icons/svg/qemu.svg" width="64" height="64" alt="">

**[🇧🇷 Leia em português](./pt-BR/qemu.md)**

[< VMs](../README.md)

Any operating system in a VM, chosen at install time.

Web viewer on **8007**. Unit `vm-qemu`.

The install lists twenty-three systems, from Alpine at 60 MB to CentOS at 7 GB. The ISO is downloaded on the first boot and the installer runs in the viewer.

Alpine is the quick way to prove KVM works on the host before committing a bigger download to it.

This is the general-purpose one: no password, no RDP, no integration. It boots an ISO and shows you the screen.

All of these need `/dev/kvm` on the host — without hardware virtualisation
the VM either refuses to start or crawls. `RAM_SIZE` is reserved for the whole
life of the VM, so leave the host enough to breathe; `DISK_SIZE` is a ceiling
and grows on demand.

## Install

```bash
qh vm-qemu
qh vm-qemu --apply
```

Installing the folder — `qh vm --apply` — brings this one along with the rest.

## Systems

The install asks, and writes the answer to the `.env`. It only matters on the
first boot: the image is downloaded once, and changing the value later does
nothing to a disk already written.

`BOOT` — Which OS to install (downloaded on first boot).

| | Value | What it is |
| --- | --- | --- |
| <img src="https://cdn.simpleicons.org/alpinelinux" width="20" height="20" alt=""> | `alpine` | Alpine Linux — 60 MB, the quickest way to prove KVM works |
| <img src="https://cdn.simpleicons.org/opensuse" width="20" height="20" alt=""> | `suse` | openSUSE — 1.0 GB |
| <img src="https://cdn.simpleicons.org/archlinux" width="20" height="20" alt=""> | `arch` | Arch Linux — 1.2 GB |
| <img src="https://cdn.jsdelivr.net/gh/selfhst/icons/svg/zimaos.svg" width="20" height="20" alt=""> | `zima` | ZimaOS — 1.4 GB |
| <img src="https://cdn.simpleicons.org/tails" width="20" height="20" alt=""> | `tails` | Tails — 1.5 GB |
| <img src="https://cdn.simpleicons.org/rockylinux" width="20" height="20" alt=""> | `rocky` | Rocky Linux — 2.1 GB |
| <img src="https://cdn.simpleicons.org/almalinux" width="20" height="20" alt=""> | `alma` | Alma Linux — 2.2 GB |
| <img src="https://cdn.simpleicons.org/mxlinux" width="20" height="20" alt=""> | `mx` | MX Linux — 2.2 GB |
| <img src="https://cdn.simpleicons.org/fedora" width="20" height="20" alt=""> | `fedora` | Fedora — 2.3 GB |
| <img src="https://cdn.simpleicons.org/nixos" width="20" height="20" alt=""> | `nixos` | NixOS — 2.4 GB |
| <img src="https://cdn.simpleicons.org/cachyos" width="20" height="20" alt=""> | `cachy` | CachyOS — 2.6 GB |
| <img src="https://cdn.simpleicons.org/linuxmint" width="20" height="20" alt=""> | `mint` | Linux Mint — 2.8 GB, upstream's own default |
| <img src="https://cdn.simpleicons.org/ubuntu" width="20" height="20" alt=""> | `ubuntus` | Ubuntu Server — 3.0 GB |
| <img src="https://cdn.simpleicons.org/debian" width="20" height="20" alt=""> | `debian` | Debian — 3.3 GB |
| <img src="https://cdn.simpleicons.org/gentoo" width="20" height="20" alt=""> | `gentoo` | Gentoo — 3.6 GB |
| <img src="https://cdn.simpleicons.org/slackware" width="20" height="20" alt=""> | `slack` | Slackware — 3.7 GB |
| <img src="https://cdn.simpleicons.org/kalilinux" width="20" height="20" alt=""> | `kali` | Kali Linux — 3.8 GB |
| <img src="https://cdn.simpleicons.org/zorin" width="20" height="20" alt=""> | `zorin` | Zorin OS — 3.8 GB |
| <img src="https://cdn.simpleicons.org/xubuntu" width="20" height="20" alt=""> | `xubuntu` | Xubuntu — 4.0 GB |
| <img src="https://cdn.simpleicons.org/manjaro" width="20" height="20" alt=""> | `manjaro` | Manjaro — 4.1 GB |
| <img src="https://cdn.simpleicons.org/kubuntu" width="20" height="20" alt=""> | `kubuntu` | Kubuntu — 4.4 GB |
| <img src="https://cdn.simpleicons.org/ubuntu" width="20" height="20" alt=""> | `ubuntu` | Ubuntu Desktop — 6.0 GB |
| <img src="https://cdn.simpleicons.org/centos" width="20" height="20" alt=""> | `centos` | CentOS — 7.0 GB |

## Files

```
vm-qemu.container     unit
vm-qemu.env.example   environment
```

Data in `~/.config/containers/volumes/vm/qemu/storage`.

## Update

```bash
qh vm-qemu --update --apply
```

Pinned to `7.44`. Nothing updates on its own — a new version is applied when
you run the command above.

## Backup

```bash
qh vm-qemu --backup --apply --out ~/backups
```

The archive holds this unit's directories, its secrets and its own `.env` — nothing a sibling also reads.

It stops this unit, packs it and starts it again. Cold on purpose: copying a
live database gives an archive that only fails when you restore it.

```bash
qh vm-qemu --restore ~/backups/vm-qemu-20260809-1200.tar.gz --apply
```

Restoring asks you to type `vm-qemu` to confirm, because the current data is
deleted before the archive is unpacked.

## Remove

```bash
qh vm-qemu --remove --apply           # stops it, keeps the data
qh vm-qemu --remove --purge --apply   # and deletes its volume
```

Only the volumes of this VM. `vm-qemu.env` is kept even though nothing else
reads it — a per-unit purge does not touch the environment file.

## Commands

```bash
systemctl --user status vm-qemu
podman logs -f vm-qemu
qh vm-qemu --update --apply
```

## Credits

[QEMU](https://github.com/qemus/qemu) — MIT

[Official documentation](https://github.com/qemus/qemu#readme)
