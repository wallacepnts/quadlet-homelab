# Beszel

<img src="https://cdn.jsdelivr.net/gh/homarr-labs/dashboard-icons/svg/beszel.svg" width="64" height="64" alt="">

**[🇺🇸 Read in English](./README.md)**

Dashboard leve de monitoramento de recursos (CPU/RAM/disco/rede/containers) deste host.

## Instalar

```bash
qh beszel            # mostra o plano
qh beszel --apply
```

Abrir `http://<ip-do-host>:8090` ou `https://beszel.<your-tailnet>.ts.net`.

<details>
<summary><b>Instalação manual</b></summary>

```bash
# 1. Baixar as units (sem precisar clonar o repositório)
mkdir -p ~/.config/containers/systemd/beszel
wget -P ~/.config/containers/systemd/beszel/ \
  https://raw.githubusercontent.com/wallacepnts/quadlet-homelab/main/apps/beszel/beszel-net.network \
  https://raw.githubusercontent.com/wallacepnts/quadlet-homelab/main/apps/beszel/beszel.container \
  https://raw.githubusercontent.com/wallacepnts/quadlet-homelab/main/apps/beszel/beszel-agent.container

# 2. Diretórios de dados — bind mount exige que já existam antes do start
mkdir -p ~/.config/containers/volumes/beszel/{hub-data,socket,agent-data}

# 3. Env — baixar o exemplo, ajustar APP_URL pra URL real de acesso
mkdir -p ~/.config/containers/env
wget -O ~/.config/containers/env/beszel.env \
  https://raw.githubusercontent.com/wallacepnts/quadlet-homelab/main/apps/beszel/.env.example
# editar APP_URL no arquivo baixado — valor de exemplo com "<your-tailnet>"
# literal não sobe (hub recusa com "appURL: must be a valid URL"),
# testado na prática; usar a URL real (tsdproxy) ou http://localhost:8090

# 4. Subir só o hub primeiro
systemctl --user start beszel
```

```bash
# 5. KEY — chave pública do hub, a mesma pra qualquer agent deste hub;
#    lida direto do arquivo (sem precisar copiar pela UI)
mkdir -p ~/.config/containers/secrets/beszel
ssh-keygen -y -f ~/.config/containers/volumes/beszel/hub-data/id_ed25519 \
  > ~/.config/containers/secrets/beszel/key.txt
chmod 600 ~/.config/containers/secrets/beszel/key.txt
podman secret create beszel-agent-key ~/.config/containers/secrets/beszel/key.txt

# 6. TOKEN — esse já precisa vir da UI: painel do hub → "Add System"
#    (ou Configurações → Tokens) → copiar o token mostrado
read -s -p "Token do Beszel: " BESZEL_TOKEN; echo
echo -n "$BESZEL_TOKEN" > ~/.config/containers/secrets/beszel/token.txt
unset BESZEL_TOKEN
chmod 600 ~/.config/containers/secrets/beszel/token.txt
podman secret create beszel-agent-token ~/.config/containers/secrets/beszel/token.txt

# 7. Subir o agent
systemctl --user daemon-reload
systemctl --user start beszel-agent
```

</details>

## Arquivos

```
beszel-agent.container
beszel.container
beszel-net.network
.env.example
install.ini
```

Units da stack:

- `beszel-agent`
- `beszel`
- `beszel-n`

## Atualizar

```bash
qh beszel --update --apply
```

Fixado em `0.18.7`. Nada atualiza sozinho — versão nova entra quando você
roda o comando acima.

## Backup

```bash
qh beszel --backup --apply --out ~/backups
```

Ele para o serviço, empacota os dados, o `.env` e os secrets, e sobe de novo.
A frio de propósito: copiar banco vivo dá um arquivo que só falha na hora de
restaurar.

Pra restaurar, por cima dos dados atuais:

```bash
qh beszel --restore ~/backups/beszel-20260809-1200.tar.gz --apply
```

Ele pede que você digite `beszel` pra confirmar, porque os dados atuais são
apagados antes de o arquivo ser extraído.

## Remover

```bash
qh beszel --remove --apply           # para e tira, mantendo os dados
qh beszel --remove --purge --apply   # e apaga volumes, secrets e .env
```

O `--purge` também pede o nome digitado. O nó da tailnet não é desregistrado
por isso — isso é no admin do Tailscale.

## Comandos

```bash
systemctl --user status beszel
podman logs -f beszel
```

## Créditos

[henrygd/beszel](https://github.com/henrygd/beszel) — MIT

[Documentação oficial](https://beszel.dev)
