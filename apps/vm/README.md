# VM

<img src="https://cdn.jsdelivr.net/gh/homarr-labs/dashboard-icons/svg/qemu.svg" width="64" height="64" alt="">

**[🇧🇷 Leia em português](./README.pt-BR.md)**

Windows, macOS, ChromeOS Flex, ZimaOS and 23 Linux distros as VMs in containers, viewed in the browser — needs KVM on the host.

For a shell to install one tool in, without the cost of a VM, see [toolbx](../toolbx). For Proxmox's own interface, [proxmox](../proxmox).

## First run

Open `http://<host-ip>:3389` or `https://chromeos.<your-tailnet>.ts.net`.

## Files

```
vm-<name>.container       one unit per VM, six of them
vm-<name>.env.example     RAM, cores and disk, one per VM
install.ini               the passwords, and which OS the install offers
docs/                     a page per VM
```

Disks in `~/.config/containers/volumes/vm/<name>/`. Each VM's ports are on its
own page.

| | VM | What it does | Version |
| --- | --- | --- | --- |
| <img src="https://cdn.jsdelivr.net/gh/homarr-labs/dashboard-icons/png/windows-11.png" width="28" height="28" alt=""> | [Windows](./docs/windows.md) | A Windows VM in the browser, with RDP for a real desktop | `6.05` |
| <img src="https://cdn.jsdelivr.net/gh/homarr-labs/dashboard-icons/png/windows-11.png" width="28" height="28" alt=""> | [Windows on ARM](./docs/windows-arm.md) | The same, for an ARM64 host. Shares the ports — only one of the two runs | `6.05` |
| <img src="https://cdn.simpleicons.org/macos/888888" width="28" height="28" alt=""> | [macOS](./docs/macos.md) | A macOS VM, from Big Sur to Sequoia | `3.12` |
| <img src="https://cdn.jsdelivr.net/gh/homarr-labs/dashboard-icons/svg/qemu.svg" width="28" height="28" alt=""> | [QEMU](./docs/qemu.md) | Any of twenty-three systems, chosen at install time | `7.50` |
| <img src="https://cdn.jsdelivr.net/gh/homarr-labs/dashboard-icons/svg/chrome.svg" width="28" height="28" alt=""> | [ChromeOS](./docs/chromeos.md) | ChromeOS Flex with the host's GPU | `1.05` |
| <img src="https://cdn.jsdelivr.net/gh/dockur/zima@master/assets/20241126-153324.png" width="28" height="28" alt=""> | [ZimaOS](./docs/zima.md) | The CasaOS-derived NAS interface, without the hardware | `1.7.1` |

Every page above says what its VM asks for on the first boot. They are
independent: installing the folder brings all six, and you start the one you
want.

## Remove

The tailnet node is not deregistered when an app is removed: do that in the Tailscale admin.

## Credits

[qemus/qemu](https://github.com/qemus/qemu) — MIT

[Official documentation](https://github.com/dockur/windows#readme)
