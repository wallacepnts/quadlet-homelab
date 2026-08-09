# VaultZap

<img src="https://raw.githubusercontent.com/wallacepnts/vaultzap/main/internal/web/static/img/favicon.svg" width="64" height="64" alt="">

**[🇧🇷 Leia em português](./README.pt-BR.md)**

A local, browsable archive of exported WhatsApp conversations — search, gallery and calendar, fully offline.

## Install

```bash
qh vaultzap            # shows the plan
qh vaultzap --apply
```

Open `http://<host-ip>:8927` or `https://vaultzap.<your-tailnet>.ts.net`.

<details>
<summary><b>Manual install</b></summary>

```bash
# 1. Download the unit (a single file -> it goes loose in systemd/)
mkdir -p ~/.config/containers/systemd
wget -P ~/.config/containers/systemd/ \
  https://raw.githubusercontent.com/wallacepnts/quadlet-homelab/main/apps/vaultzap/vaultzap.container

# 2. Directories — a bind mount requires them to exist before the start
mkdir -p ~/.config/containers/volumes/vaultzap/{data,inbox}

# 3. Env
mkdir -p ~/.config/containers/env
wget -O ~/.config/containers/env/vaultzap.env \
  https://raw.githubusercontent.com/wallacepnts/quadlet-homelab/main/apps/vaultzap/.env.example

# 4. The dashboard icon (the project has its own; there is no equivalent in
#    dashboard-icons)
mkdir -p ~/.config/containers/volumes/homepage/icons
wget -O ~/.config/containers/volumes/homepage/icons/vaultzap.svg \
  https://raw.githubusercontent.com/wallacepnts/vaultzap/main/internal/web/static/img/favicon.svg
systemctl --user restart homepage   # it only picks up a new icon after a restart

# 5. Start it
systemctl --user daemon-reload
systemctl --user start vaultzap
```

</details>

## Files

```
vaultzap.container
.env.example
install.ini
```

## Update

```bash
qh vaultzap --update --apply
```

`AutoUpdate=registry` is on: the image updates on its own.

## Backup

```bash
qh vaultzap --backup --apply --out ~/backups
```

It stops the service, packs the data, the `.env` and the secrets, and starts
it again. Cold on purpose: copying a live database gives an archive that only
fails when you restore it.

To restore, over the current data:

```bash
qh vaultzap --restore ~/backups/vaultzap-20260809-1200.tar.gz --apply
```

It asks you to type `vaultzap` to confirm, because the current data is deleted
before the archive is unpacked.

## Remove

```bash
qh vaultzap --remove --apply           # stops it, keeps the data
qh vaultzap --remove --purge --apply   # and deletes volumes, secrets and .env
```

`--purge` asks for the typed name too. The tailnet node is not deregistered by
this — that is done in the Tailscale admin.

## Commands

```bash
systemctl --user status vaultzap
podman logs -f vaultzap
```

## Credits

[wallacepnts/vaultzap](https://github.com/wallacepnts/vaultzap) — AGPL-3.0

[Official documentation](https://github.com/wallacepnts/vaultzap#readme)
