# WUD (What's Up Docker)

<img src="https://cdn.jsdelivr.net/gh/getwud/wud@main/ui/public/img/icons/android-chrome-512x512.png" width="64" height="64" alt="">

**[🇧🇷 Leia em português](./README.pt-BR.md)**

Watches for available image updates for the containers, applying nothing itself — it only reports.

## Install

```bash
qh wud            # shows the plan
qh wud --apply
```

Open `http://<host-ip>:8085` or `https://wud.<your-tailnet>.ts.net`.

<details>
<summary><b>Manual install</b></summary>

```bash
# 1. Download the unit (no need to clone the repository)
mkdir -p ~/.config/containers/systemd
wget -P ~/.config/containers/systemd/ \
  https://raw.githubusercontent.com/wallacepnts/quadlet-homelab/main/apps/wud/wud.container

# 2. Data directory — a bind mount requires it to exist before the start
mkdir -p ~/.config/containers/volumes/wud/store

# 3. Env — download the example. The check schedule (cron): WUD's own
#    default is hourly; daily is enough for most homelabs and generates far
#    less traffic against the registries.
mkdir -p ~/.config/containers/env
wget -O ~/.config/containers/env/wud.env \
  https://raw.githubusercontent.com/wallacepnts/quadlet-homelab/main/apps/wud/.env.example

# 4. The Podman socket
systemctl --user enable --now podman.socket

# 5. Start it
systemctl --user daemon-reload
systemctl --user start wud
```

</details>

## Files

```
wud.container
.env.example
```

## Update

```bash
qh wud --update --apply
```

Pinned to `8.3.1`. Nothing updates on its own — a new version is applied
when you run the command above.

## Backup

```bash
qh wud --backup --apply --out ~/backups
```

It stops the service, packs the data, the `.env` and the secrets, and starts
it again. Cold on purpose: copying a live database gives an archive that only
fails when you restore it.

To restore, over the current data:

```bash
qh wud --restore ~/backups/wud-20260809-1200.tar.gz --apply
```

It asks you to type `wud` to confirm, because the current data is deleted
before the archive is unpacked.

## Remove

```bash
qh wud --remove --apply           # stops it, keeps the data
qh wud --remove --purge --apply   # and deletes volumes, secrets and .env
```

`--purge` asks for the typed name too. The tailnet node is not deregistered by
this — that is done in the Tailscale admin.

## Commands

```bash
systemctl --user status wud
podman logs -f wud
```

## Credits

[getwud/wud](https://github.com/getwud/wud) — MIT

[Official documentation](https://getwud.github.io/wud/)
