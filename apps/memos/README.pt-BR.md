# Memos — Podman Quadlet (rootless)

**[🇬🇧 Read in English](./README.md)**

Deploy do [Memos](https://usememos.com) (notas rápidas self-hosted,
markdown-nativo, leve) via Podman Quadlet, usando a imagem oficial
[`neosmemo/memos`](https://github.com/usememos/memos).

## Arquitetura

Container único, roda como root internamente (sem `PUID`/`PGID`, sem
`UserNS=keep-id` — a própria imagem ajusta o dono do volume sozinha no
primeiro start, mesmo padrão de vários outros apps deste repositório).
**SQLite embutido** — um volume só, guarda o banco inteiro
(`/var/opt/memos`).

Healthcheck usa o endpoint próprio da imagem (`/healthz`, testado na
prática) — não precisa de checagem HTTP genérica.

## Arquivos

```
memos.container       # unit principal
```

## Pré-requisitos

- Podman rootless com systemd `--user` funcionando

## Instalação

```bash
python3 install.py memos            # dry-run: mostra o que vai fazer
python3 install.py memos --apply
```

Só na rede local, `--access local`; na tailnet e na LAN, `--access
both`. Acrescentar `--href-local` faz o link do dashboard apontar pra LAN. O script cria os diretórios, grava o
`.env`, gera os secrets, ajusta o dono dos volumes, sobe o serviço e
imprime o endereço no fim — ver
[Instalando e operando](../../docs/pt-BR/instalacao.md) no README
raiz.

Acessar `http://<ip-do-host>:5230` (ou via [tsdproxy](../tsdproxy/README.pt-BR.md) em
`https://memos.<your-tailnet>.ts.net`) e criar a conta no primeiro
acesso — **o primeiro usuário a se cadastrar vira admin
automaticamente**, sem confirmação de e-mail (diferente do
[Monica](../monica/README.pt-BR.md)). Depois de criar essa conta, desligar cadastro
aberto em Configurações → (seção de admin) → "Allow user signup", senão
qualquer um que alcance a URL consegue criar conta própria.

<details>
<summary><b>Instalação manual</b> (avançado) — os mesmos passos, um a um</summary>


```bash
# 1. Baixar as units (sem precisar clonar o repositório)
mkdir -p ~/.config/containers/systemd
wget -P ~/.config/containers/systemd/ \
  https://raw.githubusercontent.com/wallacepnts/quadlet-homelab/main/apps/memos/memos.container

# 2. Diretório de dados — bind mount exige que já exista antes do start
mkdir -p ~/.config/containers/volumes/memos/data
podman unshare chown -R 1000:1000 ~/.config/containers/volumes/memos   # a unit usa User=1000

# 3. Env não-secreto
mkdir -p ~/.config/containers/env
wget -O ~/.config/containers/env/memos.env \
  https://raw.githubusercontent.com/wallacepnts/quadlet-homelab/main/apps/memos/.env.example

# 4. Subir
systemctl --user daemon-reload
systemctl --user start memos
```

Acessar `http://<ip-do-host>:5230` (ou via [tsdproxy](../tsdproxy/README.pt-BR.md) em
`https://memos.<your-tailnet>.ts.net`) e criar a conta no primeiro
acesso — **o primeiro usuário a se cadastrar vira admin
automaticamente**, sem confirmação de e-mail (diferente do
[Monica](../monica/README.pt-BR.md)). Depois de criar essa conta, desligar cadastro
aberto em Configurações → (seção de admin) → "Allow user signup", senão
qualquer um que alcance a URL consegue criar conta própria.

</details>

## Auto-update

Sem `AutoUpdate=` — tag explícita (`0.30.0`), bump manual (regra 9 do
convenções). A imagem tem `wget`/healthcheck real (`/healthz`) — daria
pra habilitar `AutoUpdate=registry` com rollback funcional, mas notas
são dado real do usuário, mesmo raciocínio do
[vaultwarden](../vaultwarden/README.pt-BR.md)/[radicale](../radicale/README.pt-BR.md) — revisão manual antes de
atualizar.

## Backup & Recuperação

```bash
systemctl --user stop memos
tar -czf memos-backup-$(date +%Y%m%d-%H%M%S).tar.gz \
  -C ~/.config/containers/volumes memos
systemctl --user start memos
```

## Comandos úteis

```bash
systemctl --user status memos
podman logs -f memos
podman exec memos wget -qO- http://127.0.0.1:5230/healthz
```

## Créditos

Deploy Quadlet baseado no [Memos](https://github.com/usememos/memos)
(MIT).
