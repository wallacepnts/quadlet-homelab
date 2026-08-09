# Calibre-Web-Automated

<img src="https://cdn.jsdelivr.net/gh/homarr-labs/dashboard-icons/svg/calibre-web.svg" width="64" height="64" alt="">

**[🇧🇷 Leia em português](./README.pt-BR.md)**

An ebook library with automatic conversion, metadata and covers via Calibre, readable straight in the browser.

## Install

```bash
qh calibre-web-automated            # shows the plan
qh calibre-web-automated --apply
```

Open `http://<host-ip>:8105` or `https://calibre-web.<your-tailnet>.ts.net`.

<details>
<summary><b>Manual install</b></summary>

```bash
# 1. Download the unit (no need to clone the repository)
mkdir -p ~/.config/containers/systemd
wget -P ~/.config/containers/systemd/ \
  https://raw.githubusercontent.com/wallacepnts/quadlet-homelab/main/apps/calibre-web-automated/calibre-web-automated.container

# 2. Data directories — a bind mount requires them to exist before the start
mkdir -p ~/.config/containers/volumes/calibre-web-automated/{config,ingest,library}

# 3. Non-secret env — download the example
#    que roda o Podman (mesmo dono dos volumes acima)
mkdir -p ~/.config/containers/env
wget -O ~/.config/containers/env/calibre-web-automated.env \
  https://raw.githubusercontent.com/wallacepnts/quadlet-homelab/main/apps/calibre-web-automated/.env.example
sed -i "s/^PUID=.*/PUID=$(id -u)/;s/^PGID=.*/PGID=$(id -g)/" \
  ~/.config/containers/env/calibre-web-automated.env

# 4. Start it
systemctl --user daemon-reload
systemctl --user start calibre-web-automated
```

</details>

## Files

```
calibre-web-automated.container
.env.example
```

## Update

```bash
qh calibre-web-automated --update --apply
```

Pinned to `v4.0.6`. Nothing updates on its own — a new version is applied
when you run the command above.

## Backup

```bash
qh calibre-web-automated --backup --apply --out ~/backups
```

It stops the service, packs the data, the `.env` and the secrets, and starts
it again. Cold on purpose: copying a live database gives an archive that only
fails when you restore it.

To restore, over the current data:

```bash
qh calibre-web-automated --restore ~/backups/calibre-web-automated-20260809-1200.tar.gz --apply
```

It asks you to type `calibre-web-automated` to confirm, because the current data is deleted
before the archive is unpacked.

## Remove

```bash
qh calibre-web-automated --remove --apply           # stops it, keeps the data
qh calibre-web-automated --remove --purge --apply   # and deletes volumes, secrets and .env
```

`--purge` asks for the typed name too. The tailnet node is not deregistered by
this — that is done in the Tailscale admin.

## Commands

```bash
systemctl --user status calibre-web-automated
podman logs -f calibre-web-automated
```

## Credits

[crocodilestick/Calibre-Web-Automated](https://github.com/crocodilestick/Calibre-Web-Automated) — GPL-3.0

[Official documentation](https://github.com/crocodilestick/Calibre-Web-Automated)
