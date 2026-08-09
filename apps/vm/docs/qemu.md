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

## Commands

```bash
systemctl --user status vm-qemu
podman logs -f vm-qemu
qh vm-qemu --update --apply
```

## Credits

[QEMU](https://github.com/qemus/qemu) — MIT

[Official documentation](https://github.com/qemus/qemu#readme)
