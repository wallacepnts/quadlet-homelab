# Uptime Kuma

<img src="https://cdn.jsdelivr.net/gh/homarr-labs/dashboard-icons/svg/uptime-kuma.svg" width="64" height="64" alt="">

**[🇧🇷 Leia em português](./README.pt-BR.md)**

An uptime monitor for the other services and the tailnet, with history and notifications.

## Install

```bash
qh uptime-kuma            # shows the plan
qh uptime-kuma --apply
```

Open `http://<host-ip>:3001` or `https://uptime-kuma.<your-tailnet>.ts.net`.

<details>
<summary><b>Manual install</b></summary>

```bash
# 1. Download the units (no need to clone the repository)
mkdir -p ~/.config/containers/systemd
wget -P ~/.config/containers/systemd/ \
  https://raw.githubusercontent.com/wallacepnts/quadlet-homelab/main/apps/uptime-kuma/uptime-kuma.container

# 2. Data directory, with the owner matching the unit's User=1000.
#    `podman unshare` runs the chown INSIDE the user namespace, which is
#    where the container's 1000 exists (on the host that becomes 100999).
mkdir -p ~/.config/containers/volumes/uptime-kuma/data
podman unshare chown -R 1000:1000 ~/.config/containers/volumes/uptime-kuma/data

# 3. Start it
systemctl --user daemon-reload
systemctl --user start uptime-kuma
```

</details>

## Files

```
uptime-kuma.container
```

## Update

```bash
qh uptime-kuma --update --apply
```

Pinned to `2.5.0`. Nothing updates on its own — a new version is applied
when you run the command above.

## Backup

```bash
qh uptime-kuma --backup --apply --out ~/backups
```

It stops the service, packs the data, the `.env` and the secrets, and starts
it again. Cold on purpose: copying a live database gives an archive that only
fails when you restore it.

To restore, over the current data:

```bash
qh uptime-kuma --restore ~/backups/uptime-kuma-20260809-1200.tar.gz --apply
```

It asks you to type `uptime-kuma` to confirm, because the current data is deleted
before the archive is unpacked.

## Remove

```bash
qh uptime-kuma --remove --apply           # stops it, keeps the data
qh uptime-kuma --remove --purge --apply   # and deletes volumes, secrets and .env
```

`--purge` asks for the typed name too. The tailnet node is not deregistered by
this — that is done in the Tailscale admin.

## Commands

```bash
systemctl --user status uptime-kuma
podman logs -f uptime-kuma
```

## Credits

[louislam/uptime-kuma](https://github.com/louislam/uptime-kuma) — MIT

[Official documentation](https://uptime.kuma.pet)
