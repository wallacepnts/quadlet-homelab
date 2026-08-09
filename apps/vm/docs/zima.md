# ZimaOS

<img src="https://cdn.jsdelivr.net/gh/dockur/zima@master/assets/20241126-153324.png" width="64" height="64" alt="">

**[🇧🇷 Leia em português](./pt-BR/zima.md)**

[< VMs](../README.md)

ZimaOS — the CasaOS-derived NAS interface — without buying the hardware.

ZimaOS itself on **8011**, the VM's viewer on **8012**. Unit `vm-zima`.

Two ports, and the difference matters: **8011** is ZimaOS's own web interface, the one you actually use, and **8012** is the QEMU viewer that shows the boot screen. Go to 8011 unless something failed to start.

Whatever you store in it lands in the virtual disk, inside the volume under your home. `DISK_SIZE` is the ceiling; it grows on demand rather than being taken up front.

It is a NAS operating system running as a guest on a machine that already has your disks. Useful for trying it, awkward as the place your files actually live.

There is no version to pick: the tag in `Image=` is the ZimaOS that gets
installed, and it moves when the unit is bumped.

All of these need `/dev/kvm` on the host — without hardware virtualisation
the VM either refuses to start or crawls. `RAM_SIZE` is reserved for the whole
life of the VM, so leave the host enough to breathe; `DISK_SIZE` is a ceiling
and grows on demand.

## Install

```bash
qh vm-zima
qh vm-zima --apply
```

Installing the folder — `qh vm --apply` — brings this one along with the rest.

## Files

```
vm-zima.container     unit
vm-zima.env.example   environment
```

Data in `~/.config/containers/volumes/vm/zima/storage`.

## Update

```bash
qh vm-zima --update --apply
```

Pinned to `1.7.0`. Nothing updates on its own — a new version is applied when
you run the command above.

## Backup

```bash
qh vm-zima --backup --apply --out ~/backups
```

The archive holds this unit's directories, its secrets and its own `.env` — nothing a sibling also reads.

It stops this unit, packs it and starts it again. Cold on purpose: copying a
live database gives an archive that only fails when you restore it.

```bash
qh vm-zima --restore ~/backups/vm-zima-20260809-1200.tar.gz --apply
```

Restoring asks you to type `vm-zima` to confirm, because the current data is
deleted before the archive is unpacked.

## Remove

```bash
qh vm-zima --remove --apply           # stops it, keeps the data
qh vm-zima --remove --purge --apply   # and deletes its volume
```

Only the volumes of this VM. `vm-zima.env` is kept even though nothing else
reads it — a per-unit purge does not touch the environment file.

## Commands

```bash
systemctl --user status vm-zima
podman logs -f vm-zima
qh vm-zima --update --apply
```

## Credits

[ZimaOS](https://github.com/dockur/zima) — MIT

[Official documentation](https://github.com/dockur/zima#readme)
