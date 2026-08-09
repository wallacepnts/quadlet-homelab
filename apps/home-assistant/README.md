# Home Assistant

<img src="https://cdn.jsdelivr.net/gh/homarr-labs/dashboard-icons/svg/home-assistant.svg" width="64" height="64" alt="">

**[🇧🇷 Leia em português](./README.pt-BR.md)**

The central home automation hub; it brings devices from any manufacturer into a single panel.

## Install

```bash
qh home-assistant            # shows the plan
qh home-assistant --apply
```

Open `http://<host-ip>:8123` or `https://home-assistant.<your-tailnet>.ts.net`.

<details>
<summary><b>Manual install</b></summary>

```bash
# 1. Download the unit (no need to clone the repository)
mkdir -p ~/.config/containers/systemd
wget -P ~/.config/containers/systemd/ \
  https://raw.githubusercontent.com/wallacepnts/quadlet-homelab/main/apps/home-assistant/home-assistant.container

# 2. Data directory — a bind mount requires it to exist before the start
mkdir -p ~/.config/containers/volumes/home-assistant/config

# 3. Env — baixar o exemplo
mkdir -p ~/.config/containers/env
wget -O ~/.config/containers/env/home-assistant.env \
  https://raw.githubusercontent.com/wallacepnts/quadlet-homelab/main/apps/home-assistant/.env.example

# 4. Start it
systemctl --user daemon-reload
systemctl --user start home-assistant
```

</details>

## Files

```
home-assistant.container
.env.example
install.ini
```

## Update

```bash
qh home-assistant --update --apply
```

Pinned to `2026.8.1`. Nothing updates on its own — a new version is applied
when you run the command above.

## Backup

```bash
qh home-assistant --backup --apply --out ~/backups
```

It stops the service, packs the data, the `.env` and the secrets, and starts
it again. Cold on purpose: copying a live database gives an archive that only
fails when you restore it.

To restore, over the current data:

```bash
qh home-assistant --restore ~/backups/home-assistant-20260809-1200.tar.gz --apply
```

It asks you to type `home-assistant` to confirm, because the current data is deleted
before the archive is unpacked.

## Remove

```bash
qh home-assistant --remove --apply           # stops it, keeps the data
qh home-assistant --remove --purge --apply   # and deletes volumes, secrets and .env
```

`--purge` asks for the typed name too. The tailnet node is not deregistered by
this — that is done in the Tailscale admin.

## Commands

```bash
systemctl --user status home-assistant
podman logs -f home-assistant
```

## Credits

[home-assistant/core](https://github.com/home-assistant/core) — Apache-2.0

[Official documentation](https://www.home-assistant.io)
