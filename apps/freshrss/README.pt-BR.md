# FreshRSS — Podman Quadlet (rootless)

**[🇬🇧 Read in English](./README.md)**

Deploy do [FreshRSS](https://freshrss.org) (agregador de feeds RSS/Atom
self-hosted, leve e com API compatível com Google Reader/Fever pra apps
móveis) via Podman Quadlet, usando a imagem oficial
[`freshrss/freshrss`](https://github.com/FreshRSS/FreshRSS/blob/edge/Docker/README.md)
(variante Alpine).

**Imagem baixada do GHCR, não do Docker Hub** — `docker.io/freshrss/freshrss`
devolveu erro de autenticação testado na prática (`unauthorized:
incorrect username or password`, mesmo anônimo/sem login configurado —
parece problema do lado do registry, não deste host); `ghcr.io/freshrss/freshrss`
funcionou normal, mesma imagem/tag, publicada pelo mesmo projeto.

## Arquitetura

Container único, roda como root internamente (sem `PUID`/`PGID`, sem
`UserNS=keep-id` — a própria imagem gerencia permissão do jeito dela).
Banco **SQLite embutido** no volume de dados, sem container de banco
separado — suficiente pro uso pessoal (o próprio projeto documenta
Postgres/MySQL como alternativa só pra instalações maiores, fora do
escopo deste deploy).

**Sem instalação automática por env var** — a imagem suporta
`FRESHRSS_INSTALL`/`FRESHRSS_USER` pra criar o admin sem tocar no
navegador, mas isso significa embutir a senha em texto puro num
`EnvironmentFile=` (contra a [regra 2](../../docs/pt-BR/convencoes.md), secrets são
imperativos). Em vez disso, a conta admin é criada pelo assistente web
no primeiro acesso — mesmo padrão já usado pro
[ownCloud](../owncloud/README.pt-BR.md)/[Immich](../immich/README.pt-BR.md)/[Audiobookshelf](../audiobookshelf/README.pt-BR.md).

Healthcheck usa o próprio `cli/health.php` da imagem (sem saída, só
exit code) — não precisa de `wget`/`curl` contra um endpoint HTTP.

## Arquivos

```
freshrss.container      # unit principal
```

## Pré-requisitos

- Podman rootless com systemd `--user` funcionando

## Instalação

```bash
python3 install.py freshrss            # dry-run: mostra o que vai fazer
python3 install.py freshrss --apply
```

Só na rede local, `--access local`; na tailnet e na LAN, `--access
both`. Acrescentar `--href-local` faz o link do dashboard apontar pra LAN. O script cria os diretórios, grava o
`.env`, gera os secrets, ajusta o dono dos volumes, sobe o serviço e
imprime o endereço no fim — ver
[Instalando e operando](../../docs/pt-BR/instalacao.md) no README
raiz.

Acessar `http://<ip-do-host>:8104` (ou via [tsdproxy](../tsdproxy/README.pt-BR.md) em
`https://freshrss.<your-tailnet>.ts.net`) e completar o assistente de
instalação no primeiro acesso — escolher **SQLite** como banco (já vem
selecionado por padrão) e criar a conta admin ali.

<details>
<summary><b>Instalação manual</b> (avançado) — os mesmos passos, um a um</summary>


```bash
# 1. Baixar as units (sem precisar clonar o repositório)
mkdir -p ~/.config/containers/systemd
wget -P ~/.config/containers/systemd/ \
  https://raw.githubusercontent.com/wallacepnts/quadlet-homelab/main/apps/freshrss/freshrss.container

# 2. Diretório de dados — bind mount exige que já exista antes do start
mkdir -p ~/.config/containers/volumes/freshrss/data

# 3. Env não-secreto — baixar o exemplo, ajustar TZ/CRON_MIN se quiser
mkdir -p ~/.config/containers/env
wget -O ~/.config/containers/env/freshrss.env \
  https://raw.githubusercontent.com/wallacepnts/quadlet-homelab/main/apps/freshrss/.env.example

# 4. Subir
systemctl --user daemon-reload
systemctl --user start freshrss
```

Acessar `http://<ip-do-host>:8104` (ou via [tsdproxy](../tsdproxy/README.pt-BR.md) em
`https://freshrss.<your-tailnet>.ts.net`) e completar o assistente de
instalação no primeiro acesso — escolher **SQLite** como banco (já vem
selecionado por padrão) e criar a conta admin ali.

</details>

## Auto-update

Sem `AutoUpdate=` — tag explícita (`1.29.1-alpine`), bump manual (regra
9 das convenções). A imagem tem healthcheck real (`cli/health.php`) —
daria pra habilitar `AutoUpdate=registry` com rollback funcional, mas
feeds/artigos salvos são dado real do usuário, mesmo raciocínio do
[Radicale](../radicale/README.pt-BR.md)/[vaultwarden](../vaultwarden/README.pt-BR.md) — revisão manual antes de
atualizar.

## Backup & Recuperação

```bash
systemctl --user stop freshrss
tar -czf freshrss-backup-$(date +%Y%m%d-%H%M%S).tar.gz \
  -C ~/.config/containers/volumes freshrss
systemctl --user start freshrss
```

## Comandos úteis

```bash
systemctl --user status freshrss
podman logs -f freshrss
podman exec freshrss php cli/health.php
podman exec --user www-data freshrss php cli/actualize-feeds.php   # forçar atualização manual
```

## Créditos

Deploy Quadlet baseado no [FreshRSS](https://github.com/FreshRSS/FreshRSS)
(AGPL-3.0).
