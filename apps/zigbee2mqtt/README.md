# Zigbee2MQTT — Podman Quadlet (rootless)

**[🇧🇷 Leia em português](./README.pt-BR.md)**

Deploy do [Zigbee2MQTT](https://github.com/Koenkk/zigbee2mqtt) (ponte
between Zigbee devices and MQTT, with no proprietary hub) via Podman
Quadlet, usando a imagem oficial `ghcr.io/koenkk/zigbee2mqtt`.

> **Not running.** The hardware is missing: Zigbee2MQTT only starts with a
> coordenador Zigbee (adaptador USB ou de rede) conectado — sem ele o
> the process exits immediately, before it even connects to MQTT. The units
> are
> prontas e o broker foi validado; falta plugar o adaptador e fazer os
> the two adjustments in "Plugging in the coordinator". The same state as
> [Frigate](../frigate/), which is waiting for a camera.

## Architecture

Dois containers na rede `zigbee2mqtt-net`:

| Unit | Papel |
| --- | --- |
| `zigbee2mqtt.container` | a ponte + frontend web |
| `zigbee2mqtt-mosquitto.container` | broker MQTT |

### Why its own broker, when owntracks already has one

O [owntracks](../owntracks/) roda um Mosquitto — e um broker MQTT
compartilhado seria a arquitetura "certa" no papel. Aqui foram dois
brokers on purpose:

- O container do owntracks se chama literalmente `mosquitto` e vive na
  rede dele. Reaproveitar significaria pôr o Zigbee2MQTT na
  `owntracks-net`, and then **restarting owntracks would take down the
  network
  Zigbee** ([regra 8](../../docs/conventions.md)).
- This repository's convention is a self-contained service per folder, each
  installable on its own through its README's `wget` commands.

The cost: about 10 MB more RAM. If unifying them ever becomes worthwhile,
the route is to promote Mosquitto to a first-class service (its own folder)
and point both clients at it — not to hang one service off the network of
outro.

The broker goes out on the host's port **1884**, because 1883 already
belongs to owntracks.

## Files

```
zigbee2mqtt-net.network            # rede bridge isolada
zigbee2mqtt.container              # ponte + frontend
zigbee2mqtt-mosquitto.container    # broker MQTT
configuration.yaml                 # config inicial do z2m
mosquitto.conf                     # config do broker
```

Both config files go into the volumes during installation (steps 2 and 3) —
Zigbee2MQTT rewrites `configuration.yaml` on its own as you change things in
the frontend, so the copy here is only the starting point.

## Prerequisites

- Rootless Podman with systemd `--user` working
- **Um coordenador Zigbee** — adaptador USB (Sonoff ZBDongle-E/P,
  ConBee II, CC2652) or a network one (SLZB-06). Without it the service does
  not start.

## Installation

```bash
python3 install.py zigbee2mqtt            # dry-run: shows what it will do
python3 install.py zigbee2mqtt --apply
```

For the local network only, `--access local`; on the tailnet and the LAN,
`--access both`. Adding `--href-local` points the dashboard link at the LAN.
The script creates the directories, writes the `.env`, generates the secrets,
fixes the volumes' ownership, starts the service and prints the address at the
end — see [Installing and operating](../../docs/installing.md).

Open `http://<host-ip>:8097` (or through [tsdproxy](../tsdproxy/) at
`https://zigbee2mqtt.<your-tailnet>.ts.net`).

<details>
<summary><b>Manual installation</b> (advanced) — the same steps, one at a time</summary>


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

Open `http://<host-ip>:8097` (ou via [tsdproxy](../tsdproxy/) em
`https://zigbee2mqtt.<your-tailnet>.ts.net`).

</details>

## Plugging in the coordinator

Two adjustments that have to **match**, or the service will not start.

### A USB adapter

Find the stable path (never use `/dev/ttyUSB0` directly — the number changes
between reboots):

```bash
ls -l /dev/serial/by-id/
```

Uncomment and adjust the line in the unit:

```ini
AddDevice=/dev/serial/by-id/usb-ITEAD_SONOFF_Zigbee_3.0_USB_Dongle_Plus_xxxx-if00-port0:/dev/ttyACM0
```

And point at the same thing in `configuration.yaml`:

```yaml
serial:
  port: /dev/ttyACM0
  adapter: ezsp   # zstack for the ZBDongle-P/CC2652, ezsp for the ZBDongle-E, deconz for the ConBee
```

Rootless does not grant access to `/dev` automatically: your user has to be
in the group that owns the device (`dialout` on most distros). Check with
`ls -l /dev/ttyACM0` and, if needed:

```bash
sudo usermod -aG dialout $USER   # requires logging out and back in
```

### A network coordinator (SLZB-06 and the like)

Simpler — it needs **no** `AddDevice=`, only the address in
`configuration.yaml`:

```yaml
serial:
  port: tcp://192.168.1.50:6638
  adapter: ezsp
```

## Integrating with Home Assistant

This repository's [Home Assistant](../home-assistant/) is on a different
network, so the connection goes through the host's published port:

1. In z2m's `configuration.yaml`, turn on `homeassistant: enabled: true` and
   restart.
2. In HA: Settings → Devices and Services → Add → MQTT, pointing at
   `<host-ip>:1884`.

The devices show up by themselves through MQTT discovery.

## Write down the network key

On the first start z2m generates `network_key`, `pan_id` and `ext_pan_id` and
writes them into `configuration.yaml`. **That is what lets the devices come
back without re-pairing** — lose it and everything has to be paired again, one
by one. It goes into the backup (below), and a copy in
[vaultwarden](../vaultwarden/) is worth having.

## Auto-update

No `AutoUpdate=` — an explicit tag (`2.13.0`), bumped by hand
(rule 9 of the [conventions](../../docs/conventions.md)). What weighs here is the `database.db` migration: z2m releases change the
state format fairly often, and a rollback does not always read
o banco novo. Ler as release notes e fazer backup antes.

## Backup & recovery

What matters is `data/` — `configuration.yaml` (with the network keys) and
`database.db` (os dispositivos pareados):

```bash
systemctl --user stop zigbee2mqtt zigbee2mqtt-mosquitto
tar -czf zigbee2mqtt-backup-$(date +%Y%m%d-%H%M%S).tar.gz \
  -C ~/.config/containers/volumes zigbee2mqtt
systemctl --user start zigbee2mqtt
```

Stop both together, not just the main unit — otherwise the broker keeps
writing
([regra 8](../../docs/conventions.md)).

## Useful commands

```bash
systemctl --user status zigbee2mqtt zigbee2mqtt-mosquitto
podman logs -f zigbee2mqtt
# see what is passing through the broker
podman exec zigbee2mqtt-mosquitto mosquitto_sub -h 127.0.0.1 -t 'zigbee2mqtt/#' -v
```

## Credits

Quadlet deploy based on
[Zigbee2MQTT](https://github.com/Koenkk/zigbee2mqtt) de
[Koen Kanters](https://github.com/Koenkk) (GPL-3.0).
