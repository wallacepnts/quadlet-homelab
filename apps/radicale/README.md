# Radicale

<img src="https://cdn.jsdelivr.net/gh/homarr-labs/dashboard-icons/svg/radicale.svg" width="64" height="64" alt="">

**[🇧🇷 Leia em português](./README.pt-BR.md)**

A light, minimal CalDAV/CardDAV server.

## Install

```bash
qh radicale            # shows the plan
qh radicale --apply
```

Open `http://<host-ip>:5232` or `https://radicale.<your-tailnet>.ts.net`.

<details>
<summary><b>Manual install</b></summary>

```bash
# 1. Download the unit (no need to clone the repository)
mkdir -p ~/.config/containers/systemd
wget -P ~/.config/containers/systemd/ \
  https://raw.githubusercontent.com/wallacepnts/quadlet-homelab/main/apps/radicale/radicale.container

# 2. Data directories — a bind mount requires them to exist before the start
mkdir -p ~/.config/containers/volumes/radicale/{data,config}
wget -O ~/.config/containers/volumes/radicale/config/config \
  https://raw.githubusercontent.com/wallacepnts/quadlet-homelab/main/apps/radicale/config/config

# 3. Username and password — a bcrypt hash generated locally, in htpasswd
#    format (user:hash, one per line). The /config/users file has to be
#    readable by any uid (world-readable) because the container runs with a
#    fixed internal uid (2999) that is not yours — with no UserNS=keep-id on
#    this image (see Architecture), that is the only way it can see the file.
read -p "Radicale username: " RADICALE_USER
read -s -p "Radicale password: " RADICALE_PW; echo
RADICALE_USER="$RADICALE_USER" RADICALE_PW="$RADICALE_PW" python3 -c "
import bcrypt, os
user = os.environ['RADICALE_USER']
pw = os.environ['RADICALE_PW'].encode()
h = bcrypt.hashpw(pw, bcrypt.gensalt()).decode()
print(f'{user}:{h}')
" > ~/.config/containers/volumes/radicale/config/users
unset RADICALE_PW
chmod 644 ~/.config/containers/volumes/radicale/config/users

# 4. Non-secret env — download the example
mkdir -p ~/.config/containers/env
wget -O ~/.config/containers/env/radicale.env \
  https://raw.githubusercontent.com/wallacepnts/quadlet-homelab/main/apps/radicale/.env.example

# 5. Start it
systemctl --user daemon-reload
systemctl --user start radicale
```

</details>

## Files

```
radicale.container
.env.example
```

## Update

```bash
qh radicale --update --apply
```

Pinned to `3.7.6.0`. Nothing updates on its own — a new version is applied
when you run the command above.

## Backup

```bash
qh radicale --backup --apply --out ~/backups
```

It stops the service, packs the data, the `.env` and the secrets, and starts
it again. Cold on purpose: copying a live database gives an archive that only
fails when you restore it.

To restore, over the current data:

```bash
qh radicale --restore ~/backups/radicale-20260809-1200.tar.gz --apply
```

It asks you to type `radicale` to confirm, because the current data is deleted
before the archive is unpacked.

## Remove

```bash
qh radicale --remove --apply           # stops it, keeps the data
qh radicale --remove --purge --apply   # and deletes volumes, secrets and .env
```

`--purge` asks for the typed name too. The tailnet node is not deregistered by
this — that is done in the Tailscale admin.

## Commands

```bash
systemctl --user status radicale
podman logs -f radicale
```

## Credits

[tomsquest/docker-radicale](https://github.com/tomsquest/docker-radicale) — MIT

[Official documentation](https://radicale.org/v3.html)
