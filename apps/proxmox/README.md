# Proxmox VE

<img src="https://cdn.jsdelivr.net/gh/homarr-labs/dashboard-icons/svg/proxmox.svg" width="64" height="64" alt="">

**[🇧🇷 Leia em português](./README.pt-BR.md)**

The Proxmox hypervisor in a container, for trying it without dedicating a machine — runs privileged.

## Install

```bash
qh proxmox            # shows the plan
qh proxmox --apply
```

Open `http://<host-ip>:8010` or `https://proxmox.<your-tailnet>.ts.net`.

<details>
<summary><b>Manual install</b></summary>

```bash
# 1. Download the unit (no need to clone the repository)
mkdir -p ~/.config/containers/systemd
wget -P ~/.config/containers/systemd/ \
  https://raw.githubusercontent.com/wallacepnts/quadlet-homelab/main/apps/proxmox/proxmox.container

# 2. Directories
mkdir -p ~/.config/containers/volumes/proxmox/{data,config}

# 3. Secret — the root password for the web interface
podman secret create proxmox-root-password - <<< "$(python3 -c 'import secrets,string;a=string.ascii_letters+string.digits;print("".join(secrets.choice(a) for _ in range(20)))')"

# 4. Start it
systemctl --user daemon-reload
systemctl --user start proxmox
```

</details>

## Files

```
proxmox.container
install.ini
```

## Update

```bash
qh proxmox --update --apply
```

Pinned to `9.2.9`. Nothing updates on its own — a new version is applied
when you run the command above.

## Backup

```bash
qh proxmox --backup --apply --out ~/backups
```

It stops the service, packs the data, the `.env` and the secrets, and starts
it again. Cold on purpose: copying a live database gives an archive that only
fails when you restore it.

To restore, over the current data:

```bash
qh proxmox --restore ~/backups/proxmox-20260809-1200.tar.gz --apply
```

It asks you to type `proxmox` to confirm, because the current data is deleted
before the archive is unpacked.

## Remove

```bash
qh proxmox --remove --apply           # stops it, keeps the data
qh proxmox --remove --purge --apply   # and deletes volumes, secrets and .env
```

`--purge` asks for the typed name too. The tailnet node is not deregistered by
this — that is done in the Tailscale admin.

## Commands

```bash
systemctl --user status proxmox
podman logs -f proxmox
```

## Credits

[dockur/proxmox](https://github.com/dockur/proxmox) — MIT

[Official documentation](https://pve.proxmox.com/pve-docs/)
