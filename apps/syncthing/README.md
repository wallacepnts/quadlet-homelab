# Syncthing

<img src="https://cdn.jsdelivr.net/gh/homarr-labs/dashboard-icons/svg/syncthing.svg" width="64" height="64" alt="">

**[🇧🇷 Leia em português](./README.pt-BR.md)**

P2P file sync between devices, with no central server.

## Install

```bash
qh syncthing            # shows the plan
qh syncthing --apply
```

Open `http://<host-ip>:8384` or `https://syncthing.<your-tailnet>.ts.net`.

<details>
<summary><b>Manual install</b></summary>

```bash
# 1. Download the unit (no need to clone the repository)
mkdir -p ~/.config/containers/systemd
wget -P ~/.config/containers/systemd/ \
  https://raw.githubusercontent.com/wallacepnts/quadlet-homelab/main/apps/syncthing/syncthing.container

# 2. Data directory — a bind mount requires it to exist before the start
mkdir -p ~/.config/containers/volumes/syncthing/data
podman unshare chown -R 1000:1000 ~/.config/containers/volumes/syncthing   # a unit usa User=1000

# 3. Non-secret env — download the example
#    que roda o Podman (mesmo dono do volume acima)
mkdir -p ~/.config/containers/env
wget -O ~/.config/containers/env/syncthing.env \
  https://raw.githubusercontent.com/wallacepnts/quadlet-homelab/main/apps/syncthing/.env.example
sed -i "s/^PUID=.*/PUID=$(id -u)/;s/^PGID=.*/PGID=$(id -g)/" \
  ~/.config/containers/env/syncthing.env

# 4. Start it
systemctl --user daemon-reload
systemctl --user start syncthing
```

</details>

## Files

```
syncthing.container
.env.example
```

## Update

```bash
qh syncthing --update --apply
```

Pinned to `2.1.3`. Nothing updates on its own — a new version is applied
when you run the command above.

## Backup

```bash
qh syncthing --backup --apply --out ~/backups
```

It stops the service, packs the data, the `.env` and the secrets, and starts
it again. Cold on purpose: copying a live database gives an archive that only
fails when you restore it.

To restore, over the current data:

```bash
qh syncthing --restore ~/backups/syncthing-20260809-1200.tar.gz --apply
```

It asks you to type `syncthing` to confirm, because the current data is deleted
before the archive is unpacked.

## Remove

```bash
qh syncthing --remove --apply           # stops it, keeps the data
qh syncthing --remove --purge --apply   # and deletes volumes, secrets and .env
```

`--purge` asks for the typed name too. The tailnet node is not deregistered by
this — that is done in the Tailscale admin.

## Commands

```bash
systemctl --user status syncthing
podman logs -f syncthing
```

## Credits

[syncthing/syncthing](https://github.com/syncthing/syncthing) — MPL-2.0.

[Official documentation](https://syncthing.net/)
