# Paperless-ngx

<img src="https://cdn.jsdelivr.net/gh/homarr-labs/dashboard-icons/svg/paperless-ngx.svg" width="64" height="64" alt="">

**[🇧🇷 Leia em português](./README.pt-BR.md)**

Scans, OCRs and indexes documents automatically, with full-text search so you never hunt for paper again.

## Install

```bash
qh paperless-ngx            # shows the plan
qh paperless-ngx --apply
```

Open `http://<host-ip>:8091` or `https://paperless.<your-tailnet>.ts.net`.

<details>
<summary><b>Manual install</b></summary>

```bash
# 1. Download the units into a dedicated subfolder (no need to clone the
#    repository)
mkdir -p ~/.config/containers/systemd/paperless-ngx
for f in paperless-ngx-net.network paperless-ngx-broker.container \
         paperless-ngx-gotenberg.container paperless-ngx-tika.container \
         paperless-ngx.container; do
  wget -P ~/.config/containers/systemd/paperless-ngx/ \
    "https://raw.githubusercontent.com/wallacepnts/quadlet-homelab/main/apps/paperless-ngx/$f"
done

# 2. Data directories — a bind mount requires them to exist before the start
mkdir -p ~/.config/containers/volumes/paperless-ngx/{broker,data,media,export,consume}
podman unshare chown -R 999:999 ~/.config/containers/volumes/paperless-ngx/redis   # the broker runs with User=999

# 3. Secret — the key used to sign sessions and tokens
mkdir -p ~/.config/containers/secrets/paperless-ngx
openssl rand -base64 64 | tr -d '\n' > ~/.config/containers/secrets/paperless-ngx/secret-key.txt
chmod 600 ~/.config/containers/secrets/paperless-ngx/secret-key.txt
podman secret create paperless-ngx-secret-key ~/.config/containers/secrets/paperless-ngx/secret-key.txt

# 4. Non-secret env — download the example
#    the user running Podman (the same owner as the volumes above)
mkdir -p ~/.config/containers/env
wget -O ~/.config/containers/env/paperless-ngx.env \
  https://raw.githubusercontent.com/wallacepnts/quadlet-homelab/main/apps/paperless-ngx/.env.example
sed -i "s/^USERMAP_UID=.*/USERMAP_UID=$(id -u)/;s/^USERMAP_GID=.*/USERMAP_GID=$(id -g)/" \
  ~/.config/containers/env/paperless-ngx.env

# 5. Start it (broker/gotenberg/tika come up first, via Requires=)
systemctl --user daemon-reload
systemctl --user start paperless-ngx
```

```bash
podman exec -it paperless-ngx python3 manage.py createsuperuser
```

</details>

## Files

```
paperless-ngx-broker.container
paperless-ngx-gotenberg.container
paperless-ngx-tika.container
paperless-ngx.container
paperless-ngx-net.network
.env.example
install.ini
```

Units in this stack:

- `paperless-ngx-broker`
- `paperless-ngx-gotenberg`
- `paperless-ngx-tika`
- `paperless-ngx`
- `paperless-ngx-n`

## Update

```bash
qh paperless-ngx --update --apply
```

Pinned to `3.0.5`, `3.3.1.0`, `8.34`. Nothing updates on its own — a new version is applied
when you run the command above.

## Backup

```bash
qh paperless-ngx --backup --apply --out ~/backups
```

It stops the service, packs the data, the `.env` and the secrets, and starts
it again. Cold on purpose: copying a live database gives an archive that only
fails when you restore it.

To restore, over the current data:

```bash
qh paperless-ngx --restore ~/backups/paperless-ngx-20260809-1200.tar.gz --apply
```

It asks you to type `paperless-ngx` to confirm, because the current data is deleted
before the archive is unpacked.

## Remove

```bash
qh paperless-ngx --remove --apply           # stops it, keeps the data
qh paperless-ngx --remove --purge --apply   # and deletes volumes, secrets and .env
```

`--purge` asks for the typed name too. The tailnet node is not deregistered by
this — that is done in the Tailscale admin.

## Commands

```bash
systemctl --user status paperless-ngx
podman logs -f paperless-ngx
```

## Credits

[paperless-ngx/paperless-ngx](https://github.com/paperless-ngx/paperless-ngx) — GPL-3.0.

[Official documentation](https://docs.paperless-ngx.com/)
