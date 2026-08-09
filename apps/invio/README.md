# Invio

<img src="https://cdn.simpleicons.org/invoiceninja" width="64" height="64" alt="">

**[🇧🇷 Leia em português](./README.pt-BR.md)**

Self-hosted invoicing and invoice tracking, on SQLite and with no external service.

## Install

```bash
qh invio            # shows the plan
qh invio --apply
```

Open `http://<host-ip>:8106` or `https://invio.<your-tailnet>.ts.net`.

<details>
<summary><b>Manual install</b></summary>

```bash
# 1. Download the unit (no need to clone the repository)
mkdir -p ~/.config/containers/systemd
wget -P ~/.config/containers/systemd/ \
  https://raw.githubusercontent.com/wallacepnts/quadlet-homelab/main/apps/invio/invio.container

# 2. Data directory
mkdir -p ~/.config/containers/volumes/invio/data

# 3. Variables — replace <your-tailnet> in ORIGIN
mkdir -p ~/.config/containers/env
wget -O ~/.config/containers/env/invio.env \
  https://raw.githubusercontent.com/wallacepnts/quadlet-homelab/main/apps/invio/.env.example
${EDITOR:-vi} ~/.config/containers/env/invio.env

# 4. Secrets — the admin password and the key that signs the session. They
#    deliberately do not go in the .env.
mkdir -p ~/.config/containers/secrets/invio
python3 -c "import secrets;print(secrets.token_urlsafe(18),end='')" \
  > ~/.config/containers/secrets/invio/admin-pass.txt
python3 -c "import secrets;print(secrets.token_hex(32),end='')" \
  > ~/.config/containers/secrets/invio/jwt-secret.txt
chmod 600 ~/.config/containers/secrets/invio/*.txt
podman secret create invio-admin-pass ~/.config/containers/secrets/invio/admin-pass.txt
podman secret create invio-jwt-secret ~/.config/containers/secrets/invio/jwt-secret.txt

# 5. Start it
systemctl --user daemon-reload
systemctl --user start invio
```

```bash
qh invio --apply
```

</details>

## Files

```
invio.container
.env.example
install.ini
```

## Update

```bash
qh invio --update --apply
```

Pinned to `v2.1.1`. Nothing updates on its own — a new version is applied
when you run the command above.

## Backup

```bash
qh invio --backup --apply --out ~/backups
```

It stops the service, packs the data, the `.env` and the secrets, and starts
it again. Cold on purpose: copying a live database gives an archive that only
fails when you restore it.

To restore, over the current data:

```bash
qh invio --restore ~/backups/invio-20260809-1200.tar.gz --apply
```

It asks you to type `invio` to confirm, because the current data is deleted
before the archive is unpacked.

## Remove

```bash
qh invio --remove --apply           # stops it, keeps the data
qh invio --remove --purge --apply   # and deletes volumes, secrets and .env
```

`--purge` asks for the typed name too. The tailnet node is not deregistered by
this — that is done in the Tailscale admin.

## Commands

```bash
systemctl --user status invio
podman logs -f invio
```

## Credits

[kittendevv/Invio](https://github.com/kittendevv/Invio)

[Official documentation](https://github.com/kittendevv/Invio#readme)
