# ZimaOS

<img src="https://cdn.jsdelivr.net/gh/dockur/zima@master/assets/20241126-153324.png" width="64" height="64" alt="">

**[🇧🇷 Leia em português](./pt-BR/zima.md)**

[< VMs](../README.md)

ZimaOS — the CasaOS-derived NAS interface — without buying the hardware.

ZimaOS itself on **8011**, the VM's viewer on **8012**. Unit `vm-zima`.

Two ports, and the difference matters: **8011** is ZimaOS's own web interface, the one you actually use, and **8012** is the QEMU viewer that shows the boot screen. Go to 8011 unless something failed to start.

Whatever you store in it lands in the virtual disk, inside the volume under your home. `DISK_SIZE` is the ceiling; it grows on demand rather than being taken up front.

It is a NAS operating system running as a guest on a machine that already has your disks. Useful for trying it, awkward as the place your files actually live.

All of these need `/dev/kvm` on the host — without hardware virtualisation
the VM either refuses to start or crawls. `RAM_SIZE` is reserved for the whole
life of the VM, so leave the host enough to breathe; `DISK_SIZE` is a ceiling
and grows on demand.

## Commands

```bash
systemctl --user status vm-zima
podman logs -f vm-zima
qh vm-zima --update --apply
```

## Credits

[ZimaOS](https://github.com/dockur/zima) — MIT

[Official documentation](https://github.com/dockur/zima#readme)
