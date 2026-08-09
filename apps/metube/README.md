# MeTube

<img src="https://cdn.jsdelivr.net/gh/homarr-labs/dashboard-icons/svg/metube.svg" width="64" height="64" alt="">

**[🇧🇷 Leia em português](./README.pt-BR.md)**

A web interface for yt-dlp — paste the URL and the video lands on disk.

## Install

```bash
qh metube            # shows the plan
qh metube --apply
```

Open `http://<host-ip>:8100` or `https://metube.<your-tailnet>.ts.net`.

<details>
<summary><b>Manual install</b></summary>

```bash
# 1. Download the unit (no need to clone the repository)
mkdir -p ~/.config/containers/systemd
wget -P ~/.config/containers/systemd/ \
  https://raw.githubusercontent.com/wallacepnts/quadlet-homelab/main/apps/metube/metube.container

# 2. Directory, with the owner matching the unit's User=1000
mkdir -p ~/.config/containers/volumes/metube/downloads
podman unshare chown -R 1000:1000 ~/.config/containers/volumes/metube

# 3. Start it
systemctl --user daemon-reload
systemctl --user start metube
```

</details>

## Files

```
metube.container
```

## Update

```bash
qh metube --update --apply
```

Pinned to `2026.08.04`. Nothing updates on its own — a new version is applied
when you run the command above.

## Backup

```bash
qh metube --backup --apply --out ~/backups
```

It stops the service, packs the data, the `.env` and the secrets, and starts
it again. Cold on purpose: copying a live database gives an archive that only
fails when you restore it.

To restore, over the current data:

```bash
qh metube --restore ~/backups/metube-20260809-1200.tar.gz --apply
```

It asks you to type `metube` to confirm, because the current data is deleted
before the archive is unpacked.

## Remove

```bash
qh metube --remove --apply           # stops it, keeps the data
qh metube --remove --purge --apply   # and deletes volumes, secrets and .env
```

`--purge` asks for the typed name too. The tailnet node is not deregistered by
this — that is done in the Tailscale admin.

## Commands

```bash
systemctl --user status metube
podman logs -f metube
```

## Credits

[alexta69/metube](https://github.com/alexta69/metube) — AGPL-3.0

[Official documentation](https://github.com/alexta69/metube#readme)
