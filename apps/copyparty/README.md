# Copyparty

<img src="https://cdn.jsdelivr.net/gh/homarr-labs/dashboard-icons/svg/copyparty.svg" width="64" height="64" alt="">

**[🇧🇷 Leia em português](./README.pt-BR.md)**

A file server with browser or phone uploads, resumable transfers and WebDAV.

## Install

```bash
qh copyparty            # shows the plan
qh copyparty --apply
```

Open `http://<host-ip>:3923` or `https://copyparty.<your-tailnet>.ts.net`.

<details>
<summary><b>Manual install</b></summary>

```bash
# 1. Download the unit (no need to clone the repository)
mkdir -p ~/.config/containers/systemd
wget -P ~/.config/containers/systemd/ \
  https://raw.githubusercontent.com/wallacepnts/quadlet-homelab/main/apps/copyparty/copyparty.container

# 2. Directories
mkdir -p ~/.config/containers/volumes/copyparty/{cfg,data}

# 3. Config — TROCAR a senha antes de subir
wget -O ~/.config/containers/volumes/copyparty/cfg/copyparty.conf \
  https://raw.githubusercontent.com/wallacepnts/quadlet-homelab/main/apps/copyparty/copyparty.conf.example
${EDITOR:-vi} ~/.config/containers/volumes/copyparty/cfg/copyparty.conf

# 4. Dono correspondente ao User=1000 da unit
podman unshare chown -R 1000:1000 ~/.config/containers/volumes/copyparty

# 5. Start it
systemctl --user daemon-reload
systemctl --user start copyparty
```

</details>

## Files

```
copyparty.container
copyparty.conf.example
install.ini
```

## Update

```bash
qh copyparty --update --apply
```

Pinned to `1.20.20`. Nothing updates on its own — a new version is applied
when you run the command above.

## Backup

```bash
qh copyparty --backup --apply --out ~/backups
```

It stops the service, packs the data, the `.env` and the secrets, and starts
it again. Cold on purpose: copying a live database gives an archive that only
fails when you restore it.

To restore, over the current data:

```bash
qh copyparty --restore ~/backups/copyparty-20260809-1200.tar.gz --apply
```

It asks you to type `copyparty` to confirm, because the current data is deleted
before the archive is unpacked.

## Remove

```bash
qh copyparty --remove --apply           # stops it, keeps the data
qh copyparty --remove --purge --apply   # and deletes volumes, secrets and .env
```

`--purge` asks for the typed name too. The tailnet node is not deregistered by
this — that is done in the Tailscale admin.

## Commands

```bash
systemctl --user status copyparty
podman logs -f copyparty
```

## Credits

[9001/copyparty](https://github.com/9001/copyparty) — MIT

[Official documentation](https://github.com/9001/copyparty#readme)
