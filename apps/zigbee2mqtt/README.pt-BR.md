# Zigbee2MQTT

<img src="https://cdn.jsdelivr.net/gh/homarr-labs/dashboard-icons/svg/zigbee2mqtt.svg" width="64" height="64" alt="">

**[🇺🇸 Read in English](./README.md)**

Ponte entre dispositivos Zigbee e MQTT, sem hub proprietário — sem coordenador ligado ainda.

## Primeiro acesso

Abrir `http://<ip-do-host>:1884` ou `https://zigbee2mqtt.<your-tailnet>.ts.net`.

## Arquivos

```
zigbee2mqtt-mosquitto.container
zigbee2mqtt.container
zigbee2mqtt-net.network
install.ini
```

Units da stack:

- `zigbee2mqtt-mosquitto`
- `zigbee2mqtt`
- `zigbee2mqtt-n`

## Remover

O nó da tailnet não é desregistrado ao remover um app: isso é no admin do Tailscale.

## Créditos

[Koenkk/zigbee2mqtt](https://github.com/Koenkk/zigbee2mqtt) — GPL-3.0

[Documentação oficial](https://www.zigbee2mqtt.io)
