# Node-RED

<img src="https://cdn.jsdelivr.net/gh/homarr-labs/dashboard-icons/svg/node-red.svg" width="64" height="64" alt="">

**[🇧🇷 Leia em português](./README.pt-BR.md)**

Flow automation through a visual node editor.

## Install

```bash
qh node-red            # shows the plan
qh node-red --apply
```

Open `http://<host-ip>:1880` or `https://node-red.<your-tailnet>.ts.net`.

<details>
<summary><b>Manual install</b></summary>

```bash
# 1. Download the units (no need to clone the repository)
mkdir -p ~/.config/containers/systemd
wget -P ~/.config/containers/systemd/ \
  https://raw.githubusercontent.com/wallacepnts/quadlet-homelab/main/apps/node-red/node-red.container

# 2. Data directory — a bind mount requires it to exist before the start
mkdir -p ~/.config/containers/volumes/node-red/data

# 3. Non-secret env
mkdir -p ~/.config/containers/env
wget -O ~/.config/containers/env/node-red.env \
  https://raw.githubusercontent.com/wallacepnts/quadlet-homelab/main/apps/node-red/.env.example

# 4. Start it
systemctl --user daemon-reload
systemctl --user start node-red
```

</details>

## Files

```
node-red.container
.env.example
install.ini
```

## Update

```bash
qh node-red --update --apply
```

Pinned to `5.0.4-minimal`. Nothing updates on its own — a new version is applied
when you run the command above.

## Backup

```bash
qh node-red --backup --apply --out ~/backups
```

It stops the service, packs the data, the `.env` and the secrets, and starts
it again. Cold on purpose: copying a live database gives an archive that only
fails when you restore it.

To restore, over the current data:

```bash
qh node-red --restore ~/backups/node-red-20260809-1200.tar.gz --apply
```

It asks you to type `node-red` to confirm, because the current data is deleted
before the archive is unpacked.

## Remove

```bash
qh node-red --remove --apply           # stops it, keeps the data
qh node-red --remove --purge --apply   # and deletes volumes, secrets and .env
```

`--purge` asks for the typed name too. The tailnet node is not deregistered by
this — that is done in the Tailscale admin.

## Commands

```bash
systemctl --user status node-red
podman logs -f node-red
```

## Credits

[node-red/node-red](https://github.com/node-red/node-red) — Apache-2.0

[Official documentation](http://nodered.org)
