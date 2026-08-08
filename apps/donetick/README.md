# Donetick — Podman Quadlet (rootless)

**[🇧🇷 Leia em português](./README.pt-BR.md)**

A [Donetick](https://github.com/donetick/donetick) (recurring household
chores) deploy via Podman Quadlet, using the official
`docker.io/donetick/donetick` image.

Built for the kind of task that **comes back**: change the filter, clean the
water tank, pay the road tax. Every task has an assignee, a recurrence and a
history of who did it. It does not replace a project manager — it is the
fridge-door list.

## Architecture

A single container, Go, with **embedded SQLite**. It takes this
repository's strongest hardening level (`ReadOnly=true`,
`DropCapability=ALL`, `User=1000`), tested by exercising the app.

Two volumes: `/config` (the `selfhosted.yaml`) and `/donetick-data` (the
database).

### The config is not versioned

`selfhosted.yaml` holds the **JWT secret** — whoever has that value can forge
any user's session. That is why it lives in the volume, like a `podman
secret`, and the repository only ships the `.example` with the field marked
for replacement.

## Files

```
donetick.container         # main unit
selfhosted.yaml.example    # config — banco, JWT, CORS
```

## Installation

```bash
python3 install.py donetick            # dry-run: shows what it will do
python3 install.py donetick --apply
```

For the local network only, `--access local`; on the tailnet and the LAN,
`--access both`. Adding `--href-local` points the dashboard link at the LAN.
The script creates the directories, writes the `.env`, generates the secrets,
fixes the volumes' ownership, starts the service and prints the address at the
end — see [Installing and operating](../../docs/installing.md).

Open `http://<host-ip>:2021` (ou via [tsdproxy](../tsdproxy/) em
`https://donetick.<your-tailnet>.ts.net`) e criar a conta.

<details>
<summary><b>Manual installation</b> (advanced) — the same steps, one at a time</summary>


```bash
# 1. Download the unit (no need to clone the repository)
mkdir -p ~/.config/containers/systemd
wget -P ~/.config/containers/systemd/ \
  https://raw.githubusercontent.com/wallacepnts/quadlet-homelab/main/apps/donetick/donetick.container

# 2. Directories
mkdir -p ~/.config/containers/volumes/donetick/{config,data}

# 3. Config — replace the JWT secret and the domain
wget -O ~/.config/containers/volumes/donetick/config/selfhosted.yaml \
  https://raw.githubusercontent.com/wallacepnts/quadlet-homelab/main/apps/donetick/selfhosted.yaml.example
sed -i "s|CHANGEME_openssl_rand_hex_24|$(openssl rand -hex 24)|" \
  ~/.config/containers/volumes/donetick/config/selfhosted.yaml
sed -i "s|<your-tailnet>|YOUR-TAILNET-HERE|g" \
  ~/.config/containers/volumes/donetick/config/selfhosted.yaml

# 4. Dono correspondente ao User=1000 da unit
podman unshare chown -R 1000:1000 ~/.config/containers/volumes/donetick

# 5. Start it
systemctl --user daemon-reload
systemctl --user start donetick
```

Open `http://<host-ip>:2021` (ou via [tsdproxy](../tsdproxy/) em
`https://donetick.<your-tailnet>.ts.net`) e criar a conta.

**Depois de criar a sua conta**, fechar o cadastro:

```bash
sed -i 's/^is_user_creation_disabled: false/is_user_creation_disabled: true/' \
  ~/.config/containers/volumes/donetick/config/selfhosted.yaml
systemctl --user restart donetick
```

</details>

## The phone app

Donetick has an Android app. It requires the server's URL to be in
`server.cors_allow_origins` **and** in `server.public_host` — both already
point at the tailnet domain in the `.example`, alongside the
`capacitor://localhost` origins the app uses internally.

## Notifications

`selfhosted.yaml` has fields for Telegram and Pushover. This repository uses
[ntfy](../ntfy/) for the rest of its alerts; Donetick does not speak ntfy
natively yet, so it is either Telegram/Pushover or a webhook via
[n8n](../n8n/).

## Auto-update

No `AutoUpdate=` — an explicit tag (`v0.1.76`), bumped by hand
(rule 9 of the [conventions](../../docs/conventions.md)). Upstream publishes **betas alongside the stable releases** (there was a
`v0.1.77-beta.3` next to `v0.1.76` when this was written), hence the
`wud.tag.include=^v[0-9]+.[0-9]+.[0-9]+$` in the unit. A `0.x` project: read
the changelog before bumping.

## Backup & recovery

```bash
systemctl --user stop donetick
tar -czf donetick-backup-$(date +%Y%m%d-%H%M%S).tar.gz \
  -C ~/.config/containers/volumes donetick
systemctl --user start donetick
```

`config/` goes into the backup too — without the same JWT secret, every
session drops.

## Useful commands

```bash
systemctl --user status donetick
podman logs -f donetick
```

## Credits

Quadlet deploy based on [Donetick](https://github.com/donetick/donetick)
(AGPL-3.0).
