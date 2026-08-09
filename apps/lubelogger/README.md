# LubeLogger

<img src="https://cdn.jsdelivr.net/gh/homarr-labs/dashboard-icons/png/lubelogger.png" width="64" height="64" alt="">

**[🇧🇷 Leia em português](./README.pt-BR.md)**

Vehicle maintenance records — oil changes, services, costs and reminders, per vehicle.

## Install

```bash
qh lubelogger            # shows the plan
qh lubelogger --apply
```

Open `http://<host-ip>:8083` or `https://lubelogger.<your-tailnet>.ts.net`.

<details>
<summary><b>Manual install</b></summary>

```bash
# 1. Download the unit (no need to clone the repository)
mkdir -p ~/.config/containers/systemd
wget -P ~/.config/containers/systemd/ \
  https://raw.githubusercontent.com/wallacepnts/quadlet-homelab/main/apps/lubelogger/lubelogger.container

# 2. Data directories — a bind mount requires them to exist before the start
mkdir -p ~/.config/containers/volumes/lubelogger/{data,keys}

# 3. Env — download the example and edit the domain
mkdir -p ~/.config/containers/env
wget -O ~/.config/containers/env/lubelogger.env \
  https://raw.githubusercontent.com/wallacepnts/quadlet-homelab/main/apps/lubelogger/.env.example
# edit ~/.config/containers/env/lubelogger.env: LUBELOGGER_DOMAIN

# 4. Start it
systemctl --user daemon-reload
systemctl --user start lubelogger
```

</details>

## Files

```
lubelogger.container
.env.example
install.ini
```

## Update

```bash
qh lubelogger --update --apply
```

Pinned to `v1.7.0`. Nothing updates on its own — a new version is applied
when you run the command above.

## Backup

```bash
qh lubelogger --backup --apply --out ~/backups
```

It stops the service, packs the data, the `.env` and the secrets, and starts
it again. Cold on purpose: copying a live database gives an archive that only
fails when you restore it.

To restore, over the current data:

```bash
qh lubelogger --restore ~/backups/lubelogger-20260809-1200.tar.gz --apply
```

It asks you to type `lubelogger` to confirm, because the current data is deleted
before the archive is unpacked.

## Remove

```bash
qh lubelogger --remove --apply           # stops it, keeps the data
qh lubelogger --remove --purge --apply   # and deletes volumes, secrets and .env
```

`--purge` asks for the typed name too. The tailnet node is not deregistered by
this — that is done in the Tailscale admin.

## Commands

```bash
systemctl --user status lubelogger
podman logs -f lubelogger
```

## Credits

[hargata/lubelog](https://github.com/hargata/lubelog) — MIT

[Official documentation](https://lubelogger.com)
