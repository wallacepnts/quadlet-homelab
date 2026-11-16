# Zigbee2MQTT

<img src="https://cdn.jsdelivr.net/gh/homarr-labs/dashboard-icons/svg/zigbee2mqtt.svg" width="64" height="64" alt="">

**[🇧🇷 Leia em português](./README.pt-BR.md)**

A bridge between Zigbee devices and MQTT, with no proprietary hub — no coordinator plugged in yet.

## First run

Open `http://<host-ip>:1884` or `https://zigbee2mqtt.<your-tailnet>.ts.net`.

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

## Remove

The tailnet node is not deregistered when an app is removed: do that in the Tailscale admin.

## Credits

[Koenkk/zigbee2mqtt](https://github.com/Koenkk/zigbee2mqtt) — GPL-3.0

[Official documentation](https://www.zigbee2mqtt.io)
