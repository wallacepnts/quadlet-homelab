# Node-RED

<img src="https://cdn.jsdelivr.net/gh/homarr-labs/dashboard-icons/svg/node-red.svg" width="64" height="64" alt="">

**[🇺🇸 Read in English](./README.md)**

Automação de fluxos via editor visual de nós.

## Instalar

```bash
qh node-red            # mostra o plano
qh node-red --apply
```

Abrir `http://<ip-do-host>:1880` ou `https://node-red.<your-tailnet>.ts.net`.

<details>
<summary><b>Instalação manual</b></summary>

```bash
# 1. Baixar as units (sem precisar clonar o repositório)
mkdir -p ~/.config/containers/systemd
wget -P ~/.config/containers/systemd/ \
  https://raw.githubusercontent.com/wallacepnts/quadlet-homelab/main/apps/node-red/node-red.container

# 2. Diretório de dados — bind mount exige que já exista antes do start
mkdir -p ~/.config/containers/volumes/node-red/data

# 3. Env não-secreto
mkdir -p ~/.config/containers/env
wget -O ~/.config/containers/env/node-red.env \
  https://raw.githubusercontent.com/wallacepnts/quadlet-homelab/main/apps/node-red/.env.example

# 4. Subir
systemctl --user daemon-reload
systemctl --user start node-red
```

</details>

## Arquivos

```
node-red.container
.env.example
install.ini
```

## Atualizar

```bash
qh node-red --update --apply
```

Fixado em `5.0.4-minimal`. Nada atualiza sozinho — versão nova entra quando você
roda o comando acima.

## Backup

```bash
qh node-red --backup --apply --out ~/backups
```

Ele para o serviço, empacota os dados, o `.env` e os secrets, e sobe de novo.
A frio de propósito: copiar banco vivo dá um arquivo que só falha na hora de
restaurar.

Pra restaurar, por cima dos dados atuais:

```bash
qh node-red --restore ~/backups/node-red-20260809-1200.tar.gz --apply
```

Ele pede que você digite `node-red` pra confirmar, porque os dados atuais são
apagados antes de o arquivo ser extraído.

## Remover

```bash
qh node-red --remove --apply           # para e tira, mantendo os dados
qh node-red --remove --purge --apply   # e apaga volumes, secrets e .env
```

O `--purge` também pede o nome digitado. O nó da tailnet não é desregistrado
por isso — isso é no admin do Tailscale.

## Comandos

```bash
systemctl --user status node-red
podman logs -f node-red
```

## Créditos

[node-red/node-red](https://github.com/node-red/node-red) — Apache-2.0

[Documentação oficial](http://nodered.org)
