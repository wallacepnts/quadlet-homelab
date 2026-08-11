# AdGuard Home

<img src="https://cdn.jsdelivr.net/gh/homarr-labs/dashboard-icons/svg/adguard-home.svg" width="64" height="64" alt="">

**[🇧🇷 Leia em português](./README.pt-BR.md)**

A recursive DNS server that blocks ads and trackers for the whole network.

## Install

```bash
qh adguardhome            # shows the plan
qh adguardhome --apply
```

Open `http://<host-ip>:3006` or `https://adguardhome.<your-tailnet>.ts.net`.

<details>
<summary><b>Manual install</b></summary>

```bash
# 1. Download the units (no need to clone the repository)
mkdir -p ~/.config/containers/systemd
wget -P ~/.config/containers/systemd/ \
  https://raw.githubusercontent.com/wallacepnts/quadlet-homelab/main/apps/adguardhome/adguardhome.container

# 2. Data directories — a bind mount requires them to exist before the start
mkdir -p ~/.config/containers/volumes/adguardhome/{conf,work}

# 3. Start it
systemctl --user daemon-reload
systemctl --user start adguardhome
```

</details>

## Files

```
adguardhome.container
install.ini
```

## Update

```bash
qh adguardhome --update --apply
```

Pinned to `v0.107.78`. Nothing updates on its own — a new version is applied
when you run the command above.

## Backup

```bash
qh adguardhome --backup --apply --out ~/backups
```

It stops the service, packs the data, the `.env` and the secrets, and starts
it again. Cold on purpose: copying a live database gives an archive that only
fails when you restore it.

To restore, over the current data:

```bash
qh adguardhome --restore ~/backups/adguardhome-20260809-1200.tar.gz --apply
```

It asks you to type `adguardhome` to confirm, because the current data is deleted
before the archive is unpacked.

## Remove

```bash
qh adguardhome --remove --apply           # stops it, keeps the data
qh adguardhome --remove --purge --apply   # and deletes volumes, secrets and .env
```

`--purge` asks for the typed name too. The tailnet node is not deregistered by
this — that is done in the Tailscale admin.

## Commands

```bash
systemctl --user status adguardhome
podman logs -f adguardhome
```

## Credits

[AdguardTeam/AdGuardHome](https://github.com/AdguardTeam/AdGuardHome) — GPL-3.0

[Official documentation](https://adguard.com/adguard-home/overview.html)
