# Ferdium Server

<img src="https://cdn.jsdelivr.net/gh/homarr-labs/dashboard-icons/svg/ferdium.svg" width="64" height="64" alt="">

**[🇺🇸 Read in English](./README.md)**

A metade servidor do [Ferdium](https://github.com/ferdium/ferdium-app), o app
desktop que junta WhatsApp, Telegram, Slack e o resto numa janela só. É ele que
mantém a sua lista de serviços e os seus workspaces sincronizados entre
máquinas — o trabalho que uma conta do Franz faria, no seu próprio hardware.

O app desktop não está aqui: é um programa Electron que você instala em cada
máquina, e é ele quem conversa com isto.

## Instalação

```bash
qh ferdium-server            # mostra o plano
qh ferdium-server --apply
```

Depois, no Ferdium desktop: **Settings → Ferdium account → Use custom server**,
apontando para `https://ferdium.<your-tailnet>.ts.net`. Crie a sua conta,
depois ponha `IS_REGISTRATION_ENABLED=false` no `.env` e rode
`qh ferdium-server --update --apply` para que mais ninguém crie.

<details>
<summary><b>Instalação manual (avançado)</b></summary>

```bash
mkdir -p ~/.config/containers/systemd ~/.config/containers/env
mkdir -p ~/.config/containers/volumes/ferdium-server/data
mkdir -p ~/.config/containers/volumes/ferdium-server/recipes

wget -P ~/.config/containers/systemd/ \
  https://raw.githubusercontent.com/wallacepnts/quadlet-homelab/main/apps/ferdium-server/ferdium-server.container
wget -O ~/.config/containers/env/ferdium-server.env \
  https://raw.githubusercontent.com/wallacepnts/quadlet-homelab/main/apps/ferdium-server/.env.example
# editar ~/.config/containers/env/ferdium-server.env: APP_URL

systemctl --user daemon-reload
systemctl --user start ferdium-server
```

</details>

## Arquivos

```
ferdium-server.container   unit
.env.example               ambiente
```

Dois volumes. O `data/` guarda o banco SQLite e as chaves JWT que o servidor
gera no primeiro start — o `FERDIUM_APP_KEY.txt` e o par PEM. Perdê-los é fazer
todo cliente logar de novo, e é por isso que ficam em volume e não na imagem.

O `recipes/` é um clone git do
[ferdium-recipes](https://github.com/ferdium/ferdium-recipes), as definições de
cada serviço que o app sabe embutir. O entrypoint clona no primeiro start e dá
pull nos seguintes, e é por isso que a primeira subida leva perto de um minuto
e meio.

## O primeiro start é lento

O `TimeoutStartSec=300` não é folga: antes de servir qualquer coisa o
entrypoint instala o pnpm, clona as receitas e roda as migrações do banco. São
uns 90 segundos com o volume vazio, e o `HealthStartPeriod=180s` cobre isso.

## Endurecimento

`DropCapability=ALL` como root. Dois degraus acima foram tentados e recusados:

- `ReadOnly=true` — o entrypoint clona as receitas com git e escreve o
  `/home/node/.gitconfig`: `could not create work tree dir 'recipes':
  Read-only file system`.
- `User=1000` — ele instala o pnpm global a cada start:
  `EACCES: permission denied, mkdir '/usr/local/lib/node_modules/pnpm'`.

## Atualizar

```bash
qh ferdium-server --update --apply
```

Fixado em `2.0.13`.

## Backup

```bash
qh ferdium-server --backup --apply --out ~/backups
```

Para o serviço, empacota os dois volumes e o `.env`, e sobe de novo. As
receitas são um clone git e voltariam sozinhas, mas o banco e as chaves são a
conta em si.

Pra restaurar, por cima dos dados atuais:

```bash
qh ferdium-server --restore ~/backups/ferdium-server-20260811-1200.tar.gz --apply
```

## Remover

```bash
qh ferdium-server --remove --apply           # para e mantém as contas
qh ferdium-server --remove --purge --apply   # e apaga os dois volumes
```

## Comandos

```bash
systemctl --user status ferdium-server
podman logs -f ferdium-server

# quantas contas existem
podman exec ferdium-server sh -c \
  "sqlite3 /data/ferdium.sqlite 'select count(*) from users'" 2>/dev/null
```

## Créditos

[ferdium/ferdium-server](https://github.com/ferdium/ferdium-server) — MIT.

[Documentação oficial](https://github.com/ferdium/ferdium-server#readme)
