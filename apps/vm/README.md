# VM

<img src="https://cdn.jsdelivr.net/gh/homarr-labs/dashboard-icons/svg/qemu.svg" width="64" height="64" alt="">

**[🇧🇷 Leia em português](./README.pt-BR.md)**

Windows, macOS, ChromeOS Flex, ZimaOS and 23 Linux distros as VMs in containers, viewed in the browser — needs KVM on the host.

## Install

```bash
qh vm            # shows the plan
qh vm --apply
```

Open `http://<host-ip>:3389` or `https://chromeos.<your-tailnet>.ts.net`.

<details>
<summary><b>Manual install</b></summary>

```bash
# 1. Download the unit you want (no need to clone the repository)
mkdir -p ~/.config/containers/systemd/vm
wget -P ~/.config/containers/systemd/vm/ \
  https://raw.githubusercontent.com/wallacepnts/quadlet-homelab/main/apps/vm/vm-qemu.container

# 2. Directories
mkdir -p ~/.config/containers/volumes/vm/qemu/storage
mkdir -p ~/.config/containers/env

# 3. Environment
wget -O ~/.config/containers/env/vm-qemu.env \
  https://raw.githubusercontent.com/wallacepnts/quadlet-homelab/main/apps/vm/vm-qemu.env.example

# 4. Windows only — the RDP password for the `Docker` account
podman secret create vm-windows-password - <<< "$(python3 -c 'import secrets,string;a=string.ascii_letters+string.digits;print("".join(secrets.choice(a) for _ in range(20)))')"

# 5. Start it
systemctl --user daemon-reload
systemctl --user start vm-qemu
```

</details>

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
| <img src="https://cdn.jsdelivr.net/gh/homarr-labs/dashboard-icons/png/windows-11.png" width="28" height="28" alt=""> | [Windows](./docs/windows.md) | A Windows VM in the browser, with RDP for a real desktop | `6.04` |
| <img src="https://cdn.jsdelivr.net/gh/homarr-labs/dashboard-icons/png/windows-11.png" width="28" height="28" alt=""> | [Windows on ARM](./docs/windows-arm.md) | The same, for an ARM64 host. Shares the ports — only one of the two runs | `6.04` |
| <img src="https://cdn.simpleicons.org/macos/888888" width="28" height="28" alt=""> | [macOS](./docs/macos.md) | A macOS VM, from Big Sur to Sequoia | `3.09` |
| <img src="https://cdn.jsdelivr.net/gh/homarr-labs/dashboard-icons/svg/qemu.svg" width="28" height="28" alt=""> | [QEMU](./docs/qemu.md) | Any of twenty-three systems, chosen at install time | `7.44` |
| <img src="https://cdn.jsdelivr.net/gh/homarr-labs/dashboard-icons/svg/chrome.svg" width="28" height="28" alt=""> | [ChromeOS](./docs/chromeos.md) | ChromeOS Flex with the host's GPU | `1.02` |
| <img src="https://cdn.jsdelivr.net/gh/dockur/zima@master/assets/20241126-153324.png" width="28" height="28" alt=""> | [ZimaOS](./docs/zima.md) | The CasaOS-derived NAS interface, without the hardware | `1.7.0` |

Every page above says what its VM asks for on the first boot. They are
independent: installing the folder brings all six, and you start the one you
want.

## Update

```bash
qh vm --update --apply
```

Pinned to `1.02`, `1.7.0`, `3.09`. Nothing updates on its own — a new version is applied
when you run the command above.

## Backup

```bash
qh vm --backup --apply --out ~/backups
```

It stops the service, packs the data, the `.env` and the secrets, and starts
it again. Cold on purpose: copying a live database gives an archive that only
fails when you restore it.

To restore, over the current data:

```bash
qh vm --restore ~/backups/vm-20260809-1200.tar.gz --apply
```

It asks you to type `vm` to confirm, because the current data is deleted
before the archive is unpacked.

## Remove

```bash
qh vm --remove --apply           # stops it, keeps the data
qh vm --remove --purge --apply   # and deletes volumes, secrets and .env
```

`--purge` asks for the typed name too. The tailnet node is not deregistered by
this — that is done in the Tailscale admin.

## Commands

```bash
systemctl --user status vm
podman logs -f vm
```

## Credits

[qemus/qemu](https://github.com/qemus/qemu) — MIT

[Official documentation](https://github.com/dockur/windows#readme)
