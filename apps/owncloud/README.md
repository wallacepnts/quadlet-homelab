# ownCloud

<img src="https://cdn.jsdelivr.net/gh/homarr-labs/dashboard-icons/svg/owncloud.svg" width="64" height="64" alt="">

**[🇧🇷 Leia em português](./README.pt-BR.md)**

File sync and sharing on a cloud of your own.

## Install

```bash
qh owncloud            # shows the plan
qh owncloud --apply
```

Open `http://<host-ip>:8094` or `https://owncloud.<your-tailnet>.ts.net`.

<details>
<summary><b>Manual install</b></summary>

```bash
# 1. Download the unit (no need to clone the repository)
mkdir -p ~/.config/containers/systemd
wget -P ~/.config/containers/systemd/ \
  https://raw.githubusercontent.com/wallacepnts/quadlet-homelab/main/apps/owncloud/owncloud.container

# 2. Data directory — a bind mount requires it to exist before the start
mkdir -p ~/.config/containers/volumes/owncloud/data

# 3. Secret — the admin password (created on the first start)
mkdir -p ~/.config/containers/secrets/owncloud
openssl rand -base64 18 | tr -d '\n' > ~/.config/containers/secrets/owncloud/admin-password.txt
chmod 600 ~/.config/containers/secrets/owncloud/admin-password.txt
podman secret create owncloud-admin-password ~/.config/containers/secrets/owncloud/admin-password.txt

# 4. Non-secret env — download the example
#    OWNCLOUD_TRUSTED_DOMAINS with your tailnet domain
mkdir -p ~/.config/containers/env
wget -O ~/.config/containers/env/owncloud.env \
  https://raw.githubusercontent.com/wallacepnts/quadlet-homelab/main/apps/owncloud/.env.example
# edit ~/.config/containers/env/owncloud.env

# 5. Start it
systemctl --user daemon-reload
systemctl --user start owncloud
```

</details>

## Files

```
owncloud.container
.env.example
install.ini
```

## Update

```bash
qh owncloud --update --apply
```

Pinned to `11.0.0-20260802`. Nothing updates on its own — a new version is applied
when you run the command above.

## Backup

```bash
qh owncloud --backup --apply --out ~/backups
```

It stops the service, packs the data, the `.env` and the secrets, and starts
it again. Cold on purpose: copying a live database gives an archive that only
fails when you restore it.

To restore, over the current data:

```bash
qh owncloud --restore ~/backups/owncloud-20260809-1200.tar.gz --apply
```

It asks you to type `owncloud` to confirm, because the current data is deleted
before the archive is unpacked.

## Remove

```bash
qh owncloud --remove --apply           # stops it, keeps the data
qh owncloud --remove --purge --apply   # and deletes volumes, secrets and .env
```

`--purge` asks for the typed name too. The tailnet node is not deregistered by
this — that is done in the Tailscale admin.

## Commands

```bash
systemctl --user status owncloud
podman logs -f owncloud
```

## Credits

[owncloud/core](https://github.com/owncloud/core) — AGPL-3.0.

[Official documentation](https://owncloud.com)
