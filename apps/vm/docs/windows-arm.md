# Windows on ARM

<img src="https://cdn.jsdelivr.net/gh/homarr-labs/dashboard-icons/png/windows-11.png" width="64" height="64" alt="">

**[🇧🇷 Leia em português](./pt-BR/windows-arm.md)**

[< VMs](../README.md)

The same as `vm-windows`, built for an ARM64 host.

Web viewer on **8006**, RDP on **3389**. Unit `vm-windows-arm`.

Use this one when the machine running Podman is ARM — a Raspberry Pi 5, an Ampere server, an Apple Silicon Linux. On an x86 host it is `vm-windows` that you want.

It shares 8006 and 3389 with `vm-windows`, which `check.py` is told to allow. Starting both at once fails on the port, and that is the intended outcome: only one of the two makes sense on a given machine.

Fewer editions than the x86 image, because not every Windows was built for ARM.

All of these need `/dev/kvm` on the host — without hardware virtualisation
the VM either refuses to start or crawls. `RAM_SIZE` is reserved for the whole
life of the VM, so leave the host enough to breathe; `DISK_SIZE` is a ceiling
and grows on demand.

## Commands

```bash
systemctl --user status vm-windows-arm
podman logs -f vm-windows-arm
qh vm-windows-arm --update --apply
```

## Credits

[Windows on ARM](https://github.com/dockur/windows-arm) — MIT

[Official documentation](https://github.com/dockur/windows-arm#readme)
