# ownCloud — Podman Quadlet (rootless)

**[🇬🇧 Read in English](./README.md)**

Deploy do [ownCloud](https://owncloud.com) Server (sincronização e
compartilhamento de arquivos self-hosted) via Podman Quadlet, seguindo o
[guia oficial de instalação com Docker](https://doc.owncloud.com/server/latest/admin_manual/installation/docker/index.html).

## SQLite — avaliação, não produção

Rodando com **SQLite** de propósito (pedido explícito) — nenhuma
variável `OWNCLOUD_DB_TYPE`/`OWNCLOUD_DB_*` é definida no `.container`, e
SQLite é o que a imagem usa por padrão nesse caso. O próprio projeto
ownCloud **não suporta SQLite em produção**. Trocar pra MySQL/MariaDB ou
Postgres depois se o volume de uso justificar (mesmo padrão de container
extra usado no [immich](../immich/README.pt-BR.md)).

## Arquitetura

Container único, sem Redis (o compose oficial de produção inclui Redis
pra cache/lock — dispensado aqui porque SQLite já é o modo "avaliação",
não faz sentido trazer só uma peça da stack de produção). Expõe `8080`
(mapeado pra `8094` no host).

## Arquivos

```
owncloud.container   # unit principal
```

## Pré-requisitos

- Podman rootless com systemd `--user` funcionando
- `openssl` (pra gerar o secret)

## Instalação

```bash
python3 install.py owncloud            # dry-run: mostra o que vai fazer
python3 install.py owncloud --apply
```

Só na rede local, `--access local`; na tailnet e na LAN, `--access
both`. Acrescentar `--href-local` faz o link do dashboard apontar pra LAN. O script cria os diretórios, grava o
`.env`, gera os secrets, ajusta o dono dos volumes, sobe o serviço e
imprime o endereço no fim — ver
[Instalando e operando](../../docs/pt-BR/instalacao.md) no README
raiz.

Acessar via [tsdproxy](../tsdproxy/README.pt-BR.md) (tailnet) em
`https://owncloud.<your-tailnet>.ts.net`, ou local em
`http://localhost:8094`. Login com `OWNCLOUD_ADMIN_USERNAME` (default
`admin`) e a senha gerada no passo 3.

<details>
<summary><b>Instalação manual</b> (avançado) — os mesmos passos, um a um</summary>


```bash
# 1. Baixar a unit (sem precisar clonar o repositório)
mkdir -p ~/.config/containers/systemd
wget -P ~/.config/containers/systemd/ \
  https://raw.githubusercontent.com/wallacepnts/quadlet-homelab/main/apps/owncloud/owncloud.container

# 2. Diretório de dados — bind mount exige que já exista antes do start
mkdir -p ~/.config/containers/volumes/owncloud/data

# 3. Secret — senha do admin (criado no primeiro start)
mkdir -p ~/.config/containers/secrets/owncloud
openssl rand -base64 18 | tr -d '\n' > ~/.config/containers/secrets/owncloud/admin-password.txt
chmod 600 ~/.config/containers/secrets/owncloud/admin-password.txt
podman secret create owncloud-admin-password ~/.config/containers/secrets/owncloud/admin-password.txt

# 4. Env não-secreto — baixar o exemplo e editar OWNCLOUD_DOMAIN/
#    OWNCLOUD_TRUSTED_DOMAINS com seu domínio da tailnet
mkdir -p ~/.config/containers/env
wget -O ~/.config/containers/env/owncloud.env \
  https://raw.githubusercontent.com/wallacepnts/quadlet-homelab/main/apps/owncloud/.env.example
# editar ~/.config/containers/env/owncloud.env

# 5. Subir
systemctl --user daemon-reload
systemctl --user start owncloud
```

Acessar via [tsdproxy](../tsdproxy/README.pt-BR.md) (tailnet) em
`https://owncloud.<your-tailnet>.ts.net`, ou local em
`http://localhost:8094`. Login com `OWNCLOUD_ADMIN_USERNAME` (default
`admin`) e a senha gerada no passo 3.

</details>

## Solução de problemas

**Erro de CSRF/proxy confiável ao acessar via tailnet** — app pensa que
está em HTTP puro, mas o tsdproxy termina TLS na frente. `.env.example`
já vem com
`OWNCLOUD_OVERWRITE_PROTOCOL=https` pra evitar isso de saída — se ainda
assim acontecer, checar `OWNCLOUD_TRUSTED_DOMAINS` (precisa incluir o
hostname exato usado no navegador).

## Auto-update

Sem `AutoUpdate=` — tag explícita (`11.0.0-20260802`), bump manual
([regra 9](../../docs/pt-BR/convencoes.md)). Arquivos sincronizados são dado real do
usuário — revisão manual antes de atualizar, mesmo raciocínio do
immich. Ainda mais relevante aqui rodando em SQLite (modo não
suportado oficialmente em produção).

## Backup & Recuperação

```bash
systemctl --user stop owncloud
tar -czf owncloud-backup-$(date +%Y%m%d-%H%M%S).tar.gz \
  -C ~/.config/containers/volumes owncloud
systemctl --user start owncloud
```

## Comandos úteis

```bash
systemctl --user status owncloud
podman logs -f owncloud
podman exec owncloud /usr/bin/healthcheck
```

## Créditos

Deploy Quadlet baseado no [ownCloud](https://github.com/owncloud/core)
Server, usando a imagem oficial
[owncloud/server](https://github.com/owncloud-docker/server).
Licença original: AGPL-3.0.
