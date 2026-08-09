# OwnTracks

<img src="https://cdn.jsdelivr.net/gh/homarr-labs/dashboard-icons/svg/owntracks.svg" width="64" height="64" alt="">

**[🇺🇸 Read in English](./README.md)**

Rastreamento de localização pessoal via app de celular, com broker MQTT próprio e histórico de posições.

## Instalar

```bash
qh owntracks            # mostra o plano
qh owntracks --apply
```

Abrir `http://<ip-do-host>:1883` ou `https://owntracks-ui.<your-tailnet>.ts.net`.

<details>
<summary><b>Instalação manual</b></summary>

```bash
# 1. Baixar as units (sem precisar clonar o repositório)
mkdir -p ~/.config/containers/systemd/owntracks
for f in owntracks-net.network owntracks-mosquitto.container \
         owntracks-recorder.container owntracks-frontend.container; do
  wget -P ~/.config/containers/systemd/owntracks/ \
    "https://raw.githubusercontent.com/wallacepnts/quadlet-homelab/main/apps/owntracks/$f"
done

# 2. Diretórios — bind mount exige que já existam antes do start
mkdir -p ~/.config/containers/volumes/owntracks/{mosquitto/config,mosquitto/data,store,config}
wget -O ~/.config/containers/volumes/owntracks/mosquitto/config/mosquitto.conf \
  https://raw.githubusercontent.com/wallacepnts/quadlet-homelab/main/apps/owntracks/mosquitto.conf
wget -O ~/.config/containers/volumes/owntracks/frontend-config.js \
  https://raw.githubusercontent.com/wallacepnts/quadlet-homelab/main/apps/owntracks/frontend-config.js

# 3. Senha MQTT — gerada uma vez, usada pelo app do celular pra
#    autenticar no broker. Os dois segredos abaixo (arquivo passwd do
#    Mosquitto e OTR_PASS do recorder) embutem a MESMA senha.
mkdir -p ~/.config/containers/secrets/owntracks
MQTT_PW=$(openssl rand -base64 24 | tr -d '\n')

# 3a. passwd do Mosquitto — mosquitto_passwd gera o hash, viramos secret
#     em vez de deixar como arquivo solto no volume (regra 2 do README
#     raiz). Secret montado como arquivo já vem 0444 (mundo-legível) por
#     padrão do Podman — funciona mesmo o mosquitto rodando
#     internamente como usuário não-root "mosquitto".
podman run --rm --entrypoint mosquitto_passwd \
  -v ~/.config/containers/secrets/owntracks:/secrets:Z \
  docker.io/library/eclipse-mosquitto:2.1.2-alpine \
  -b -c /secrets/mosquitto-passwd owntracks "$MQTT_PW"
podman secret create owntracks-mosquitto-passwd ~/.config/containers/secrets/owntracks/mosquitto-passwd

# 3b. OTR_PASS do recorder — mesma senha, crua (não hash), pro cliente
#     MQTT do próprio recorder autenticar no broker
echo -n "$MQTT_PW" > ~/.config/containers/secrets/owntracks/mqtt-password.txt
chmod 600 ~/.config/containers/secrets/owntracks/mqtt-password.txt
podman secret create owntracks-mqtt-password ~/.config/containers/secrets/owntracks/mqtt-password.txt
echo "Senha MQTT (configurar no app do celular): $MQTT_PW"

# 4. Env não-secreto — baixar o exemplo (padrão já bate com o usuário
#    criado acima; só editar se quiser um nome de usuário diferente de
#    "owntracks", refazendo o passo 3 com esse nome)
mkdir -p ~/.config/containers/env
wget -O ~/.config/containers/env/owntracks-recorder.env \
  https://raw.githubusercontent.com/wallacepnts/quadlet-homelab/main/apps/owntracks/.env.example

# 5. Subir (mosquitto sobe primeiro via Requires=; o frontend sobe
#    depois do recorder, mesma lógica)
systemctl --user daemon-reload
systemctl --user start owntracks-frontend
```

</details>

## Arquivos

```
owntracks-frontend.container
owntracks-mosquitto.container
owntracks-recorder.container
owntracks-net.network
.env.example
install.ini
```

Units da stack:

- `owntracks-frontend`
- `owntracks-mosquitto`
- `owntracks-recorder`
- `owntracks-n`

## Atualizar

```bash
qh owntracks --update --apply
```

Fixado em `1.0.1`, `2.1.2-alpine`, `2.15.3`. Nada atualiza sozinho — versão nova entra quando você
roda o comando acima.

## Backup

```bash
qh owntracks --backup --apply --out ~/backups
```

Ele para o serviço, empacota os dados, o `.env` e os secrets, e sobe de novo.
A frio de propósito: copiar banco vivo dá um arquivo que só falha na hora de
restaurar.

Pra restaurar, por cima dos dados atuais:

```bash
qh owntracks --restore ~/backups/owntracks-20260809-1200.tar.gz --apply
```

Ele pede que você digite `owntracks` pra confirmar, porque os dados atuais são
apagados antes de o arquivo ser extraído.

## Remover

```bash
qh owntracks --remove --apply           # para e tira, mantendo os dados
qh owntracks --remove --purge --apply   # e apaga volumes, secrets e .env
```

O `--purge` também pede o nome digitado. O nó da tailnet não é desregistrado
por isso — isso é no admin do Tailscale.

## Comandos

```bash
systemctl --user status owntracks
podman logs -f owntracks
```

## Créditos

[owntracks/recorder](https://github.com/owntracks/recorder) — GPL-2.0

[Documentação oficial](https://owntracks.org/booklet/)
