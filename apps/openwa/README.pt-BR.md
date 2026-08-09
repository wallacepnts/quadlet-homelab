# OpenWA

<img src="https://cdn.jsdelivr.net/gh/rmyndharis/OpenWA@main/docs/logo/openwa.svg" width="64" height="64" alt="">

**[🇺🇸 Read in English](./README.md)**

Gateway de API do WhatsApp — transforma a conta em REST + webhooks, pro n8n e o Home Assistant usarem.

## Instalar

```bash
qh openwa            # mostra o plano
qh openwa --apply
```

Abrir `http://<ip-do-host>:2785` ou `https://openwa.<your-tailnet>.ts.net`.

<details>
<summary><b>Instalação manual</b></summary>

```bash
# 1. Baixar a unit (sem precisar clonar o repositório)
mkdir -p ~/.config/containers/systemd
wget -P ~/.config/containers/systemd/ \
  https://raw.githubusercontent.com/wallacepnts/quadlet-homelab/main/apps/openwa/openwa.container

# 2. Diretórios
mkdir -p ~/.config/containers/volumes/openwa/data
mkdir -p ~/.config/containers/env

# 3. Ambiente
wget -O ~/.config/containers/env/openwa.env \
  https://raw.githubusercontent.com/wallacepnts/quadlet-homelab/main/apps/openwa/.env.example

# 4. Secrets
podman secret create openwa-master-key - <<< "$(python3 -c 'import secrets;print(secrets.token_urlsafe(48))')"
podman secret create openwa-key-pepper - <<< "$(openssl rand -hex 32)"

# 5. Subir
systemctl --user daemon-reload
systemctl --user start openwa
```

</details>

## Arquivos

```
openwa.container
.env.example
install.ini
```

## Mudança de comportamento na 0.15.0

Enquanto o WhatsApp Web recarrega a própria página — medido em torno de cinco
minutos depois de um pareamento novo — todas as rotas do engine respondem `409`
em vez do `500` cru de antes. Cliente que tenta de novo em 5xx e desiste em 4xx
vai falhar onde antes se recuperava, então vale conferir os fluxos que chamam
essa API.

## Atualizar

```bash
qh openwa --update --apply
```

Fixado em `0.14.6`. Nada atualiza sozinho — versão nova entra quando você
roda o comando acima.

## Backup

```bash
qh openwa --backup --apply --out ~/backups
```

Ele para o serviço, empacota os dados, o `.env` e os secrets, e sobe de novo.
A frio de propósito: copiar banco vivo dá um arquivo que só falha na hora de
restaurar.

Pra restaurar, por cima dos dados atuais:

```bash
qh openwa --restore ~/backups/openwa-20260809-1200.tar.gz --apply
```

Ele pede que você digite `openwa` pra confirmar, porque os dados atuais são
apagados antes de o arquivo ser extraído.

## Remover

```bash
qh openwa --remove --apply           # para e tira, mantendo os dados
qh openwa --remove --purge --apply   # e apaga volumes, secrets e .env
```

O `--purge` também pede o nome digitado. O nó da tailnet não é desregistrado
por isso — isso é no admin do Tailscale.

## Comandos

```bash
systemctl --user status openwa
podman logs -f openwa
```

## Créditos

[rmyndharis/OpenWA](https://github.com/rmyndharis/OpenWA) — MIT

[Documentação oficial](https://www.open-wa.org)
