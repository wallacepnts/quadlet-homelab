# homepage

<img src="https://cdn.jsdelivr.net/gh/homarr-labs/dashboard-icons/png/homepage.png" width="64" height="64" alt="">

**[🇧🇷 Leia em português](./README.pt-BR.md)**

A dashboard that discovers and organises the other containers by itself through labels, with no config to edit per new service.

## Install

```bash
qh homepage            # shows the plan
qh homepage --apply
```

Open `http://<host-ip>:3000` or `https://homepage.<your-tailnet>.ts.net`.

<details>
<summary><b>Manual install</b></summary>

```bash
# 1. Download the unit (no need to clone the repository)
mkdir -p ~/.config/containers/systemd
wget -P ~/.config/containers/systemd/ \
  https://raw.githubusercontent.com/wallacepnts/quadlet-homelab/main/apps/homepage/homepage.container

# 2. Config — it has to exist before the start. services.yaml and
#    bookmarks.yaml go in empty: Homepage writes a sample file over each
#    one it does not find, and the sample shows up on the dashboard.
mkdir -p ~/.config/containers/volumes/homepage/config
wget -P ~/.config/containers/volumes/homepage/config/ \
  https://raw.githubusercontent.com/wallacepnts/quadlet-homelab/main/apps/homepage/config/docker.yaml \
  https://raw.githubusercontent.com/wallacepnts/quadlet-homelab/main/apps/homepage/config/settings.yaml \
  https://raw.githubusercontent.com/wallacepnts/quadlet-homelab/main/apps/homepage/config/services.yaml \
  https://raw.githubusercontent.com/wallacepnts/quadlet-homelab/main/apps/homepage/config/bookmarks.yaml

# 2b. Custom icons (optional) — this only needs to exist if you use them,
#     see "Marking a service" below
mkdir -p ~/.config/containers/volumes/homepage/icons

# 3. Env — download the example. HOMEPAGE_ALLOWED_HOSTS is mandatory (a
#    Host-header allowlist, in host:port form; it accepts several,
#    comma-separated). The .container already ships tsdproxy labels (a
#    "homepage" node on the tailnet), so include the MagicDNS hostname here
#    too, otherwise Homepage rejects the requests coming from tsdproxy with
#    "Host not allowed".
mkdir -p ~/.config/containers/env
wget -O ~/.config/containers/env/homepage.env \
  https://raw.githubusercontent.com/wallacepnts/quadlet-homelab/main/apps/homepage/.env.example
# edit ~/.config/containers/env/homepage.env: HOMEPAGE_ALLOWED_HOSTS

# 4. The Podman socket
systemctl --user enable --now podman.socket

# 5. Start it
systemctl --user daemon-reload
systemctl --user start homepage

# 6. Auto-update (see the dedicated section below) — a daily timer, shared
#    with any other service on this host that also uses AutoUpdate=
systemctl --user enable --now podman-auto-update.timer
```

</details>

## Files

```
homepage.container
.env.example
```

## Update

```bash
qh homepage --update --apply
```

`AutoUpdate=registry` is on: the image updates on its own.

## Backup

```bash
qh homepage --backup --apply --out ~/backups
```

It stops the service, packs the data, the `.env` and the secrets, and starts
it again. Cold on purpose: copying a live database gives an archive that only
fails when you restore it.

To restore, over the current data:

```bash
qh homepage --restore ~/backups/homepage-20260809-1200.tar.gz --apply
```

It asks you to type `homepage` to confirm, because the current data is deleted
before the archive is unpacked.

## Remove

```bash
qh homepage --remove --apply           # stops it, keeps the data
qh homepage --remove --purge --apply   # and deletes volumes, secrets and .env
```

`--purge` asks for the typed name too. The tailnet node is not deregistered by
this — that is done in the Tailscale admin.

## Commands

```bash
systemctl --user status homepage
podman logs -f homepage
```

## Credits

[gethomepage/homepage](https://github.com/gethomepage/homepage) — GPL-3.0.

[Official documentation](https://gethomepage.dev)
