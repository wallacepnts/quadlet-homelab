# Zigbee2MQTT

<img src="https://cdn.jsdelivr.net/gh/homarr-labs/dashboard-icons/svg/zigbee2mqtt.svg" width="64" height="64" alt="">

**[🇧🇷 Leia em português](./README.pt-BR.md)**

A bridge between Zigbee devices and MQTT, with no proprietary hub — no coordinator plugged in yet.

## Install

```bash
qh zigbee2mqtt            # shows the plan
qh zigbee2mqtt --apply
```

Open `http://<host-ip>:1884` or `https://zigbee2mqtt.<your-tailnet>.ts.net`.

<details>
<summary><b>Manual install</b></summary>

```bash
# 1. Download the units (no need to clone the repository)
mkdir -p ~/.config/containers/systemd/zigbee2mqtt
wget -P ~/.config/containers/systemd/zigbee2mqtt/ \
  https://raw.githubusercontent.com/wallacepnts/quadlet-homelab/main/apps/zigbee2mqtt/zigbee2mqtt.container \
  https://raw.githubusercontent.com/wallacepnts/quadlet-homelab/main/apps/zigbee2mqtt/zigbee2mqtt-mosquitto.container \
  https://raw.githubusercontent.com/wallacepnts/quadlet-homelab/main/apps/zigbee2mqtt/zigbee2mqtt-net.network

# 2. Data directories — a bind mount requires them to exist before the start
mkdir -p ~/.config/containers/volumes/zigbee2mqtt/{data,mosquitto/config,mosquitto/data}
podman unshare chown -R 1883:1883 ~/.config/containers/volumes/zigbee2mqtt/mosquitto   # o broker roda com User=1883

# 3. Initial configs
wget -O ~/.config/containers/volumes/zigbee2mqtt/data/configuration.yaml \
  https://raw.githubusercontent.com/wallacepnts/quadlet-homelab/main/apps/zigbee2mqtt/configuration.yaml
wget -O ~/.config/containers/volumes/zigbee2mqtt/mosquitto/config/mosquitto.conf \
  https://raw.githubusercontent.com/wallacepnts/quadlet-homelab/main/apps/zigbee2mqtt/mosquitto.conf

# 4. Plug in the coordinator (see the section below) and start — the main
#    unit only, Requires= pulls the broker
systemctl --user daemon-reload
systemctl --user start zigbee2mqtt
```

</details>

## Files

```
zigbee2mqtt-mosquitto.container
zigbee2mqtt.container
zigbee2mqtt-net.network
install.ini
```

Units in this stack:

- `zigbee2mqtt-mosquitto`
- `zigbee2mqtt`
- `zigbee2mqtt-n`

## Update

```bash
qh zigbee2mqtt --update --apply
```

Pinned to `2.1.2-alpine`, `2.13.0`. Nothing updates on its own — a new version is applied
when you run the command above.

## Backup

```bash
qh zigbee2mqtt --backup --apply --out ~/backups
```

It stops the service, packs the data, the `.env` and the secrets, and starts
it again. Cold on purpose: copying a live database gives an archive that only
fails when you restore it.

To restore, over the current data:

```bash
qh zigbee2mqtt --restore ~/backups/zigbee2mqtt-20260809-1200.tar.gz --apply
```

It asks you to type `zigbee2mqtt` to confirm, because the current data is deleted
before the archive is unpacked.

## Remove

```bash
qh zigbee2mqtt --remove --apply           # stops it, keeps the data
qh zigbee2mqtt --remove --purge --apply   # and deletes volumes, secrets and .env
```

`--purge` asks for the typed name too. The tailnet node is not deregistered by
this — that is done in the Tailscale admin.

## Commands

```bash
systemctl --user status zigbee2mqtt
podman logs -f zigbee2mqtt
```

## Credits

[Koenkk/zigbee2mqtt](https://github.com/Koenkk/zigbee2mqtt) — GPL-3.0

[Official documentation](https://www.zigbee2mqtt.io)
