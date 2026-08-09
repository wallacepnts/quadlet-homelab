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
vm-chromeos.container
vm-macos.container
vm-qemu.container
vm-windows-arm.container
vm-windows.container
vm-zima.container
vm-chromeos.env.example
vm-macos.env.example
vm-qemu.env.example
vm-windows-arm.env.example
vm-windows.env.example
vm-zima.env.example
install.ini
```

Units in this stack:

- `vm-chromeos`
- `vm-macos`
- `vm-qemu`
- `vm-windows-arm`
- `vm-windows`
- `vm-zima`

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
