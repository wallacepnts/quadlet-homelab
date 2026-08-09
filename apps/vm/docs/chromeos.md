# ChromeOS

<img src="https://cdn.jsdelivr.net/gh/homarr-labs/dashboard-icons/svg/chrome.svg" width="64" height="64" alt="">

**[🇧🇷 Leia em português](./pt-BR/chromeos.md)**

[< VMs](../README.md)

ChromeOS Flex in a VM, with the host's GPU.

Web viewer on **8013**, VNC on **5901**. Unit `vm-chromeos`.

The install asks which channel to track — stable, beta, or one of the two long-term ones. Then you sign in with a Google account inside the VM, as on a Chromebook.

This is the only VM here with a password on the viewer itself: the account is `admin` and the password is a generated secret, printed by the install.

It reaches the host's graphics through `--device-cgroup-rule=c 226:* rwm`, which is the DRI device class. Without that rule it still boots, only without acceleration.

All of these need `/dev/kvm` on the host — without hardware virtualisation
the VM either refuses to start or crawls. `RAM_SIZE` is reserved for the whole
life of the VM, so leave the host enough to breathe; `DISK_SIZE` is a ceiling
and grows on demand.

## Commands

```bash
systemctl --user status vm-chromeos
podman logs -f vm-chromeos
qh vm-chromeos --update --apply
```

## Credits

[ChromeOS](https://github.com/dockur/chromeos) — MIT

[Official documentation](https://github.com/dockur/chromeos#readme)
