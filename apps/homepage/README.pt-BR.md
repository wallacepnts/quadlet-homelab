# homepage

<img src="https://cdn.jsdelivr.net/gh/homarr-labs/dashboard-icons/png/homepage.png" width="64" height="64" alt="">

**[🇺🇸 Read in English](./README.md)**

Dashboard que descobre e organiza os outros containers sozinho via labels, sem editar config a cada serviço novo.

## Instalar

```bash
qh homepage            # mostra o plano
qh homepage --apply
```

Abrir `http://<ip-do-host>:3000` ou `https://homepage.<your-tailnet>.ts.net`.

<details>
<summary><b>Instalação manual</b></summary>

```bash
# 1. Baixar a unit (sem precisar clonar o repositório)
mkdir -p ~/.config/containers/systemd
wget -P ~/.config/containers/systemd/ \
  https://raw.githubusercontent.com/wallacepnts/quadlet-homelab/main/apps/homepage/homepage.container

# 2. Config — precisa existir antes do start. O services.yaml e o
#    bookmarks.yaml vão vazios: a Homepage escreve um arquivo de exemplo no
#    lugar de cada um que não encontra, e o exemplo aparece no dashboard.
mkdir -p ~/.config/containers/volumes/homepage/config
wget -P ~/.config/containers/volumes/homepage/config/ \
  https://raw.githubusercontent.com/wallacepnts/quadlet-homelab/main/apps/homepage/config/docker.yaml \
  https://raw.githubusercontent.com/wallacepnts/quadlet-homelab/main/apps/homepage/config/settings.yaml \
  https://raw.githubusercontent.com/wallacepnts/quadlet-homelab/main/apps/homepage/config/services.yaml \
  https://raw.githubusercontent.com/wallacepnts/quadlet-homelab/main/apps/homepage/config/bookmarks.yaml

# 2b. Ícones customizados (opcional) — só precisa existir se for usar,
#     ver seção "Marcando um serviço" abaixo
mkdir -p ~/.config/containers/volumes/homepage/icons

# 3. Env — baixar o exemplo. HOMEPAGE_ALLOWED_HOSTS é obrigatório
#    (allowlist de Host header, formato host:porta; aceita vários
#    separados por vírgula). O .container já vem com labels tsdproxy (nó
#    "homepage" na tailnet), então incluir o hostname MagicDNS aqui
#    também, senão a Homepage rejeita as requisições vindas do tsdproxy
#    com "Host not allowed".
mkdir -p ~/.config/containers/env
wget -O ~/.config/containers/env/homepage.env \
  https://raw.githubusercontent.com/wallacepnts/quadlet-homelab/main/apps/homepage/.env.example
# editar ~/.config/containers/env/homepage.env: HOMEPAGE_ALLOWED_HOSTS

# 4. Socket do Podman
systemctl --user enable --now podman.socket

# 5. Subir
systemctl --user daemon-reload
systemctl --user start homepage

# 6. Auto-update (ver seção própria abaixo) — timer diário, compartilhado
#    com qualquer outro serviço deste host que também use AutoUpdate=
systemctl --user enable --now podman-auto-update.timer
```

</details>

## Arquivos

```
homepage.container
.env.example
```

## Atualizar

```bash
qh homepage --update --apply
```

`AutoUpdate=registry` ligado: a imagem é atualizada sozinha.

## Backup

```bash
qh homepage --backup --apply --out ~/backups
```

Ele para o serviço, empacota os dados, o `.env` e os secrets, e sobe de novo.
A frio de propósito: copiar banco vivo dá um arquivo que só falha na hora de
restaurar.

Pra restaurar, por cima dos dados atuais:

```bash
qh homepage --restore ~/backups/homepage-20260809-1200.tar.gz --apply
```

Ele pede que você digite `homepage` pra confirmar, porque os dados atuais são
apagados antes de o arquivo ser extraído.

## Remover

```bash
qh homepage --remove --apply           # para e tira, mantendo os dados
qh homepage --remove --purge --apply   # e apaga volumes, secrets e .env
```

O `--purge` também pede o nome digitado. O nó da tailnet não é desregistrado
por isso — isso é no admin do Tailscale.

## Comandos

```bash
systemctl --user status homepage
podman logs -f homepage
```

## Créditos

[gethomepage/homepage](https://github.com/gethomepage/homepage) — GPL-3.0.

[Documentação oficial](https://gethomepage.dev)
