# Monica

<img src="https://cdn.jsdelivr.net/gh/homarr-labs/dashboard-icons/svg/monica.svg" width="64" height="64" alt="">

**[🇧🇷 Leia em português](./README.pt-BR.md)**

A personal CRM — relationship history, contacts, reminders.

## Install

```bash
qh monica            # shows the plan
qh monica --apply
```

Open `http://<host-ip>:9092` or `https://monica.<your-tailnet>.ts.net`.

<details>
<summary><b>Manual install</b></summary>

```bash
# 1. Download the units (no need to clone the repository)
mkdir -p ~/.config/containers/systemd
wget -P ~/.config/containers/systemd/ \
  https://raw.githubusercontent.com/wallacepnts/quadlet-homelab/main/apps/monica/monica.container

# 2. Data directory — a bind mount requires it to exist before the start
mkdir -p ~/.config/containers/volumes/monica/storage

# 3. Non-secret env — download the example
#    replace "<your-tailnet>" with the real domain, see below) before starting
mkdir -p ~/.config/containers/env
wget -O ~/.config/containers/env/monica.env \
  https://raw.githubusercontent.com/wallacepnts/quadlet-homelab/main/apps/monica/.env.example

# 4. Secret — APP_KEY (the "base64:" prefix plus 32 random bytes in base64,
#    the same as what `artisan key:generate` itself would produce)
mkdir -p ~/.config/containers/secrets/monica
python3 -c "
import base64, os
print(f'base64:{base64.b64encode(os.urandom(32)).decode()}', end='')
" > ~/.config/containers/secrets/monica/app-key.txt
chmod 600 ~/.config/containers/secrets/monica/app-key.txt
podman secret create monica-app-key ~/.config/containers/secrets/monica/app-key.txt

# 5. Start it
systemctl --user daemon-reload
systemctl --user start monica
```

```bash
podman logs monica 2>&1 | grep -A5 "verify\|reset-password"
```

</details>

## Files

```
monica.container
.env.example
install.ini
```

## Update

```bash
qh monica --update --apply
```

Pinned to `main`. Nothing updates on its own — a new version is applied
when you run the command above.

## Backup

```bash
qh monica --backup --apply --out ~/backups
```

It stops the service, packs the data, the `.env` and the secrets, and starts
it again. Cold on purpose: copying a live database gives an archive that only
fails when you restore it.

To restore, over the current data:

```bash
qh monica --restore ~/backups/monica-20260809-1200.tar.gz --apply
```

It asks you to type `monica` to confirm, because the current data is deleted
before the archive is unpacked.

## Remove

```bash
qh monica --remove --apply           # stops it, keeps the data
qh monica --remove --purge --apply   # and deletes volumes, secrets and .env
```

`--purge` asks for the typed name too. The tailnet node is not deregistered by
this — that is done in the Tailscale admin.

## Commands

```bash
systemctl --user status monica
podman logs -f monica
```

## Credits

[monicahq/monica](https://github.com/monicahq/monica) — AGPL-3.0

[Official documentation](https://beta.monicahq.com)
