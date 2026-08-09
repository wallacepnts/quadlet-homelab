# OpenWA

<img src="https://cdn.jsdelivr.net/gh/rmyndharis/OpenWA@main/docs/logo/openwa.svg" width="64" height="64" alt="">

**[🇧🇷 Leia em português](./README.pt-BR.md)**

A WhatsApp API gateway — turns the account into REST plus webhooks, for n8n and Home Assistant to use.

## Install

```bash
qh openwa            # shows the plan
qh openwa --apply
```

Open `http://<host-ip>:2785` or `https://openwa.<your-tailnet>.ts.net`.

<details>
<summary><b>Manual install</b></summary>

```bash
# 1. Download the unit (no need to clone the repository)
mkdir -p ~/.config/containers/systemd
wget -P ~/.config/containers/systemd/ \
  https://raw.githubusercontent.com/wallacepnts/quadlet-homelab/main/apps/openwa/openwa.container

# 2. Directories
mkdir -p ~/.config/containers/volumes/openwa/data
mkdir -p ~/.config/containers/env

# 3. Environment
wget -O ~/.config/containers/env/openwa.env \
  https://raw.githubusercontent.com/wallacepnts/quadlet-homelab/main/apps/openwa/.env.example

# 4. Secrets
podman secret create openwa-master-key - <<< "$(python3 -c 'import secrets;print(secrets.token_urlsafe(48))')"
podman secret create openwa-key-pepper - <<< "$(openssl rand -hex 32)"

# 5. Start it
systemctl --user daemon-reload
systemctl --user start openwa
```

</details>

## Files

```
openwa.container
.env.example
install.ini
```

## Update

```bash
qh openwa --update --apply
```

Pinned to `0.14.6`. Nothing updates on its own — a new version is applied
when you run the command above.

## Backup

```bash
qh openwa --backup --apply --out ~/backups
```

It stops the service, packs the data, the `.env` and the secrets, and starts
it again. Cold on purpose: copying a live database gives an archive that only
fails when you restore it.

To restore, over the current data:

```bash
qh openwa --restore ~/backups/openwa-20260809-1200.tar.gz --apply
```

It asks you to type `openwa` to confirm, because the current data is deleted
before the archive is unpacked.

## Remove

```bash
qh openwa --remove --apply           # stops it, keeps the data
qh openwa --remove --purge --apply   # and deletes volumes, secrets and .env
```

`--purge` asks for the typed name too. The tailnet node is not deregistered by
this — that is done in the Tailscale admin.

## Commands

```bash
systemctl --user status openwa
podman logs -f openwa
```

## Credits

[rmyndharis/OpenWA](https://github.com/rmyndharis/OpenWA) — MIT

[Official documentation](https://www.open-wa.org)
