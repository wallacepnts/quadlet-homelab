# wger

<img src="https://cdn.jsdelivr.net/gh/homarr-labs/dashboard-icons/svg/wger.svg" width="64" height="64" alt="">

**[🇧🇷 Leia em português](./README.pt-BR.md)**

Workout planning and tracking, with an exercise database and body measurements.

## Install

```bash
qh wger            # shows the plan
qh wger --apply
```

Open `http://<host-ip>:8102` or `https://wger.<your-tailnet>.ts.net`.

<details>
<summary><b>Manual install</b></summary>

```bash
# 1. Download the unit (no need to clone the repository)
mkdir -p ~/.config/containers/systemd
wget -P ~/.config/containers/systemd/ \
  https://raw.githubusercontent.com/wallacepnts/quadlet-homelab/main/apps/wger/wger.container

# 2. Directories, with the owner matching the image's uid 1000
mkdir -p ~/.config/containers/volumes/wger/{db,static,media}
podman unshare chown -R 1000:1000 ~/.config/containers/volumes/wger

# 3. Variables — replace <your-tailnet> in ALLOWED_HOSTS and CSRF_TRUSTED_ORIGINS
mkdir -p ~/.config/containers/env
wget -O ~/.config/containers/env/wger.env \
  https://raw.githubusercontent.com/wallacepnts/quadlet-homelab/main/apps/wger/.env.example
${EDITOR:-vi} ~/.config/containers/env/wger.env

# 4. SECRET_KEY — it signs sessions and cookies
mkdir -p ~/.config/containers/secrets/wger
openssl rand -hex 32 > ~/.config/containers/secrets/wger/secret-key.txt
chmod 600 ~/.config/containers/secrets/wger/secret-key.txt
podman secret create wger-secret-key ~/.config/containers/secrets/wger/secret-key.txt

# 5. Start it. The first start runs ALL of Django's migrations and collects
#    the static files — it takes minutes, hence TimeoutStartSec=300.
systemctl --user daemon-reload
systemctl --user start wger
podman logs -f wger    # follow it until it stops applying migrations
```

</details>

## Files

```
wger.container
.env.example
install.ini
```

## Update

```bash
qh wger --update --apply
```

Pinned to `2.6.0`. Nothing updates on its own — a new version is applied
when you run the command above.

## Backup

```bash
qh wger --backup --apply --out ~/backups
```

It stops the service, packs the data, the `.env` and the secrets, and starts
it again. Cold on purpose: copying a live database gives an archive that only
fails when you restore it.

To restore, over the current data:

```bash
qh wger --restore ~/backups/wger-20260809-1200.tar.gz --apply
```

It asks you to type `wger` to confirm, because the current data is deleted
before the archive is unpacked.

## Remove

```bash
qh wger --remove --apply           # stops it, keeps the data
qh wger --remove --purge --apply   # and deletes volumes, secrets and .env
```

`--purge` asks for the typed name too. The tailnet node is not deregistered by
this — that is done in the Tailscale admin.

## Commands

```bash
systemctl --user status wger
podman logs -f wger
```

## Credits

[wger-project/wger](https://github.com/wger-project/wger) — AGPL-3.0

[Official documentation](https://wger.de)
