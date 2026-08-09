# Zigbee2MQTT

<img src="https://cdn.jsdelivr.net/gh/homarr-labs/dashboard-icons/svg/zigbee2mqtt.svg" width="64" height="64" alt="">

**[🇺🇸 Read in English](./README.md)**

Ponte entre dispositivos Zigbee e MQTT, sem hub proprietário — sem coordenador ligado ainda.

## Instalar

```bash
qh zigbee2mqtt            # mostra o plano
qh zigbee2mqtt --apply
```

Abrir `http://<ip-do-host>:1884` ou `https://zigbee2mqtt.<your-tailnet>.ts.net`.

<details>
<summary><b>Instalação manual</b></summary>

```bash
# 1. Baixar as units (sem precisar clonar o repositório)
mkdir -p ~/.config/containers/systemd/zigbee2mqtt
wget -P ~/.config/containers/systemd/zigbee2mqtt/ \
  https://raw.githubusercontent.com/wallacepnts/quadlet-homelab/main/apps/zigbee2mqtt/zigbee2mqtt.container \
  https://raw.githubusercontent.com/wallacepnts/quadlet-homelab/main/apps/zigbee2mqtt/zigbee2mqtt-mosquitto.container \
  https://raw.githubusercontent.com/wallacepnts/quadlet-homelab/main/apps/zigbee2mqtt/zigbee2mqtt-net.network

# 2. Diretórios de dados — bind mount exige que já existam antes do start
mkdir -p ~/.config/containers/volumes/zigbee2mqtt/{data,mosquitto/config,mosquitto/data}
podman unshare chown -R 1883:1883 ~/.config/containers/volumes/zigbee2mqtt/mosquitto   # o broker roda com User=1883

# 3. Configs iniciais
wget -O ~/.config/containers/volumes/zigbee2mqtt/data/configuration.yaml \
  https://raw.githubusercontent.com/wallacepnts/quadlet-homelab/main/apps/zigbee2mqtt/configuration.yaml
wget -O ~/.config/containers/volumes/zigbee2mqtt/mosquitto/config/mosquitto.conf \
  https://raw.githubusercontent.com/wallacepnts/quadlet-homelab/main/apps/zigbee2mqtt/mosquitto.conf

# 4. Ligar o coordenador (ver seção abaixo) e subir — só o principal,
#    Requires= puxa o broker
systemctl --user daemon-reload
systemctl --user start zigbee2mqtt
```

</details>

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

## Atualizar

```bash
qh zigbee2mqtt --update --apply
```

Fixado em `2.1.2-alpine`, `2.13.0`. Nada atualiza sozinho — versão nova entra quando você
roda o comando acima.

## Backup

```bash
qh zigbee2mqtt --backup --apply --out ~/backups
```

Ele para o serviço, empacota os dados, o `.env` e os secrets, e sobe de novo.
A frio de propósito: copiar banco vivo dá um arquivo que só falha na hora de
restaurar.

Pra restaurar, por cima dos dados atuais:

```bash
qh zigbee2mqtt --restore ~/backups/zigbee2mqtt-20260809-1200.tar.gz --apply
```

Ele pede que você digite `zigbee2mqtt` pra confirmar, porque os dados atuais são
apagados antes de o arquivo ser extraído.

## Remover

```bash
qh zigbee2mqtt --remove --apply           # para e tira, mantendo os dados
qh zigbee2mqtt --remove --purge --apply   # e apaga volumes, secrets e .env
```

O `--purge` também pede o nome digitado. O nó da tailnet não é desregistrado
por isso — isso é no admin do Tailscale.

## Comandos

```bash
systemctl --user status zigbee2mqtt
podman logs -f zigbee2mqtt
```

## Créditos

[Koenkk/zigbee2mqtt](https://github.com/Koenkk/zigbee2mqtt) — GPL-3.0

[Documentação oficial](https://www.zigbee2mqtt.io)
