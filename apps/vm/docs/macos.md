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

## Commands

```bash
systemctl --user status vm-macos
podman logs -f vm-macos
qh vm-macos --update --apply
```

## Credits

[macOS](https://github.com/dockur/macos) — MIT

[Official documentation](https://github.com/dockur/macos#readme)
