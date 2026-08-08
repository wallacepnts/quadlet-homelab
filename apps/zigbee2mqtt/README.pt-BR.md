# Zigbee2MQTT — Podman Quadlet (rootless)

**[🇬🇧 Read in English](./README.md)**

Deploy do [Zigbee2MQTT](https://github.com/Koenkk/zigbee2mqtt) (ponte
entre dispositivos Zigbee e MQTT, sem hub proprietário) via Podman
Quadlet, usando a imagem oficial `ghcr.io/koenkk/zigbee2mqtt`.

> **Não está no ar.** Falta o hardware: o Zigbee2MQTT só sobe com um
> coordenador Zigbee (adaptador USB ou de rede) conectado — sem ele o
> processo sai na hora, antes mesmo de conectar no MQTT. As units estão
> prontas e o broker foi validado; falta plugar o adaptador e fazer os
> dois ajustes da seção "Ligando o coordenador". Mesmo estado do
> [Frigate](../frigate/README.pt-BR.md), que espera uma câmera.

## Arquitetura

Dois containers na rede `zigbee2mqtt-net`:

| Unit | Papel |
| --- | --- |
| `zigbee2mqtt.container` | a ponte + frontend web |
| `zigbee2mqtt-mosquitto.container` | broker MQTT |

### Por que um broker próprio, se o owntracks já tem um

O [owntracks](../owntracks/README.pt-BR.md) roda um Mosquitto — e um broker MQTT
compartilhado seria a arquitetura "certa" no papel. Aqui foram dois
brokers de propósito:

- O container do owntracks se chama literalmente `mosquitto` e vive na
  rede dele. Reaproveitar significaria pôr o Zigbee2MQTT na
  `owntracks-net`, e aí **reiniciar o owntracks derrubaria a rede
  Zigbee** ([regra 8](../../docs/pt-BR/convencoes.md)).
- A convenção deste repositório é serviço autocontido por pasta, cada um
  instalável sozinho pelos `wget` do seu README.

Custo: ~10 MB de RAM a mais. Se um dia valer unificar, o caminho é
promover o Mosquitto a serviço de primeiro nível (pasta própria) e
apontar os dois clientes pra ele — não pendurar um serviço na rede do
outro.

O broker sai na porta **1884** do host, porque a 1883 já é do owntracks.

## Arquivos

```
zigbee2mqtt-net.network            # rede bridge isolada
zigbee2mqtt.container              # ponte + frontend
zigbee2mqtt-mosquitto.container    # broker MQTT
configuration.yaml                 # config inicial do z2m
mosquitto.conf                     # config do broker
```

Os dois arquivos de config vão pros volumes na instalação (passos 2 e 3)
— o Zigbee2MQTT reescreve o `configuration.yaml` sozinho conforme você
mexe no frontend, então a cópia aqui é só o ponto de partida.

## Pré-requisitos

- Podman rootless com systemd `--user` funcionando
- **Um coordenador Zigbee** — adaptador USB (Sonoff ZBDongle-E/P,
  ConBee II, CC2652) ou de rede (SLZB-06). Sem isso o serviço não sobe.

## Instalação

```bash
python3 install.py zigbee2mqtt            # dry-run: mostra o que vai fazer
python3 install.py zigbee2mqtt --apply
```

Só na rede local, `--access local`; na tailnet e na LAN, `--access
both`. Acrescentar `--href-local` faz o link do dashboard apontar pra LAN. O script cria os diretórios, grava o
`.env`, gera os secrets, ajusta o dono dos volumes, sobe o serviço e
imprime o endereço no fim — ver
[Instalando e operando](../../docs/pt-BR/instalacao.md) no README
raiz.

Acessar `http://<ip-do-host>:8097` (ou via [tsdproxy](../tsdproxy/README.pt-BR.md) em
`https://zigbee2mqtt.<your-tailnet>.ts.net`).

<details>
<summary><b>Instalação manual</b> (avançado) — os mesmos passos, um a um</summary>


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

Acessar `http://<ip-do-host>:8097` (ou via [tsdproxy](../tsdproxy/README.pt-BR.md) em
`https://zigbee2mqtt.<your-tailnet>.ts.net`).

</details>

## Ligando o coordenador

São dois ajustes que precisam **combinar**, senão o serviço não sobe.

### Adaptador USB

Descobrir o caminho estável (nunca usar `/dev/ttyUSB0` direto — o número
muda entre reboots):

```bash
ls -l /dev/serial/by-id/
```

Descomentar e ajustar a linha na unit:

```ini
AddDevice=/dev/serial/by-id/usb-ITEAD_SONOFF_Zigbee_3.0_USB_Dongle_Plus_xxxx-if00-port0:/dev/ttyACM0
```

E apontar a mesma coisa no `configuration.yaml`:

```yaml
serial:
  port: /dev/ttyACM0
  adapter: ezsp   # zstack pro ZBDongle-P/CC2652, ezsp pro ZBDongle-E, deconz pro ConBee
```

Rootless não dá acesso a `/dev` automaticamente: o seu usuário precisa
estar no grupo dono do dispositivo (`dialout` na maioria das distros).
Confere com `ls -l /dev/ttyACM0` e, se preciso:

```bash
sudo usermod -aG dialout $USER   # exige relogar
```

### Coordenador de rede (SLZB-06 e afins)

Mais simples — **não** precisa de `AddDevice=`, só do endereço no
`configuration.yaml`:

```yaml
serial:
  port: tcp://192.168.1.50:6638
  adapter: ezsp
```

## Integrando com o Home Assistant

O [Home Assistant](../home-assistant/README.pt-BR.md) deste repositório está numa rede
diferente, então a conexão é pela porta publicada do host:

1. No `configuration.yaml` do z2m, ligar `homeassistant: enabled: true`
   e reiniciar.
2. No HA: Configurações → Dispositivos e Serviços → Adicionar → MQTT,
   apontando pra `<ip-do-host>:1884`.

Os dispositivos aparecem sozinhos via MQTT discovery.

## Anotar a chave de rede

No primeiro start o z2m gera `network_key`, `pan_id` e `ext_pan_id` e
grava no `configuration.yaml`. **É o que permite os dispositivos voltarem
sem re-parear** — perdeu, tem que parear tudo de novo, um por um. Entra
no backup (abaixo) e vale uma cópia no
[vaultwarden](../vaultwarden/README.pt-BR.md).

## Auto-update

Sem `AutoUpdate=` — tag explícita (`2.13.0`), bump manual (regra 9 do
convenções). Aqui pesa a migração de `database.db`: releases do z2m
mudam formato de estado com alguma frequência, e o rollback nem sempre lê
o banco novo. Ler as release notes e fazer backup antes.

## Backup & Recuperação

O que importa é `data/` — `configuration.yaml` (com as chaves de rede) e
`database.db` (os dispositivos pareados):

```bash
systemctl --user stop zigbee2mqtt zigbee2mqtt-mosquitto
tar -czf zigbee2mqtt-backup-$(date +%Y%m%d-%H%M%S).tar.gz \
  -C ~/.config/containers/volumes zigbee2mqtt
systemctl --user start zigbee2mqtt
```

Parar os dois juntos, não só o principal — senão o broker segue gravando
([regra 8](../../docs/pt-BR/convencoes.md)).

## Comandos úteis

```bash
systemctl --user status zigbee2mqtt zigbee2mqtt-mosquitto
podman logs -f zigbee2mqtt
# ver o que está passando no broker
podman exec zigbee2mqtt-mosquitto mosquitto_sub -h 127.0.0.1 -t 'zigbee2mqtt/#' -v
```

## Créditos

Deploy Quadlet baseado no
[Zigbee2MQTT](https://github.com/Koenkk/zigbee2mqtt) de
[Koen Kanters](https://github.com/Koenkk) (GPL-3.0).
