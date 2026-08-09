# netboot.xyz

<img src="https://cdn.jsdelivr.net/gh/homarr-labs/dashboard-icons/svg/netbootxyz.svg" width="64" height="64" alt="">

**[🇧🇷 Leia em português](./README.pt-BR.md)**

A network boot (PXE) menu for installing or trying distros and tools without writing a USB stick.

## Install

```bash
qh netbootxyz            # shows the plan
qh netbootxyz --apply
```

Open `http://<host-ip>:69` or `https://netbootxyz.<your-tailnet>.ts.net`.

<details>
<summary><b>Manual install</b></summary>

```bash
# 1. Download the unit (no need to clone the repository)
mkdir -p ~/.config/containers/systemd
wget -P ~/.config/containers/systemd/ \
  https://raw.githubusercontent.com/wallacepnts/quadlet-homelab/main/apps/netbootxyz/netbootxyz.container

# 2. Data directories — a bind mount requires them to exist before the start
mkdir -p ~/.config/containers/volumes/netbootxyz/{config,assets}

# 3. Non-secret env
mkdir -p ~/.config/containers/env
wget -O ~/.config/containers/env/netbootxyz.env \
  https://raw.githubusercontent.com/wallacepnts/quadlet-homelab/main/apps/netbootxyz/.env.example

# 4. Start it
systemctl --user daemon-reload
systemctl --user start netbootxyz
```

</details>

## Files

```
netbootxyz.container
.env.example
install.ini
```

## Update

```bash
qh netbootxyz --update --apply
```

Pinned to `0.7.6-nbxyz23`. Nothing updates on its own — a new version is applied
when you run the command above.

## Backup

```bash
qh netbootxyz --backup --apply --out ~/backups
```

It stops the service, packs the data, the `.env` and the secrets, and starts
it again. Cold on purpose: copying a live database gives an archive that only
fails when you restore it.

To restore, over the current data:

```bash
qh netbootxyz --restore ~/backups/netbootxyz-20260809-1200.tar.gz --apply
```

It asks you to type `netbootxyz` to confirm, because the current data is deleted
before the archive is unpacked.

## Remove

```bash
qh netbootxyz --remove --apply           # stops it, keeps the data
qh netbootxyz --remove --purge --apply   # and deletes volumes, secrets and .env
```

`--purge` asks for the typed name too. The tailnet node is not deregistered by
this — that is done in the Tailscale admin.

## Commands

```bash
systemctl --user status netbootxyz
podman logs -f netbootxyz
```

## Credits

[netbootxyz/docker-netbootxyz](https://github.com/netbootxyz/docker-netbootxyz) — MIT

[Official documentation](https://netboot.xyz/docs/docker)
