# Donetick — Podman Quadlet (rootless)

**[🇬🇧 Read in English](./README.md)**

Deploy do [Donetick](https://github.com/donetick/donetick) (tarefas
domésticas recorrentes) via Podman Quadlet, usando a imagem oficial
`docker.io/donetick/donetick`.

Feito pra tarefa que **volta**: trocar filtro, limpar caixa d'água, pagar
o IPVA. Cada tarefa tem responsável, recorrência e histórico de quem fez.
Não substitui um gerenciador de projeto — é o quadro da geladeira.

## Arquitetura

Container único, Go, **SQLite embutido**. Aceita o nível mais forte de
hardening do repositório (`ReadOnly=true`, `DropCapability=ALL`,
`User=1000`), testado exercitando o app.

Dois volumes: `/config` (o `selfhosted.yaml`) e `/donetick-data` (o
banco).

### A config não é versionada

O `selfhosted.yaml` guarda o **segredo do JWT** — quem tem esse valor
forja sessão de qualquer usuário. Por isso ele mora no volume, como um
`podman secret`, e o repositório só traz o `.example` com o campo
marcado pra trocar.

## Arquivos

```
donetick.container         # unit principal
selfhosted.yaml.example    # config — banco, JWT, CORS
```

## Instalação

```bash
python3 install.py donetick            # dry-run: mostra o que vai fazer
python3 install.py donetick --apply
```

Só na rede local, `--access local`; na tailnet e na LAN, `--access
both`. Acrescentar `--href-local` faz o link do dashboard apontar pra LAN. O script cria os diretórios, grava o
`.env`, gera os secrets, ajusta o dono dos volumes, sobe o serviço e
imprime o endereço no fim — ver
[Instalando e operando](../../docs/pt-BR/instalacao.md) no README
raiz.

Acessar `http://<ip-do-host>:2021` (ou via [tsdproxy](../tsdproxy/README.pt-BR.md) em
`https://donetick.<your-tailnet>.ts.net`) e criar a conta.

<details>
<summary><b>Instalação manual</b> (avançado) — os mesmos passos, um a um</summary>


```bash
# 1. Baixar a unit (sem precisar clonar o repositório)
mkdir -p ~/.config/containers/systemd
wget -P ~/.config/containers/systemd/ \
  https://raw.githubusercontent.com/wallacepnts/quadlet-homelab/main/apps/donetick/donetick.container

# 2. Diretórios
mkdir -p ~/.config/containers/volumes/donetick/{config,data}

# 3. Config — trocar o segredo do JWT e o domínio
wget -O ~/.config/containers/volumes/donetick/config/selfhosted.yaml \
  https://raw.githubusercontent.com/wallacepnts/quadlet-homelab/main/apps/donetick/selfhosted.yaml.example
sed -i "s|CHANGEME_openssl_rand_hex_24|$(openssl rand -hex 24)|" \
  ~/.config/containers/volumes/donetick/config/selfhosted.yaml
sed -i "s|<your-tailnet>|SEU-TAILNET-AQUI|g" \
  ~/.config/containers/volumes/donetick/config/selfhosted.yaml

# 4. Dono correspondente ao User=1000 da unit
podman unshare chown -R 1000:1000 ~/.config/containers/volumes/donetick

# 5. Subir
systemctl --user daemon-reload
systemctl --user start donetick
```

Acessar `http://<ip-do-host>:2021` (ou via [tsdproxy](../tsdproxy/README.pt-BR.md) em
`https://donetick.<your-tailnet>.ts.net`) e criar a conta.

**Depois de criar a sua conta**, fechar o cadastro:

```bash
sed -i 's/^is_user_creation_disabled: false/is_user_creation_disabled: true/' \
  ~/.config/containers/volumes/donetick/config/selfhosted.yaml
systemctl --user restart donetick
```

</details>

## App no celular

O Donetick tem app Android. Ele exige que a URL do servidor esteja em
`server.cors_allow_origins` **e** em `server.public_host` — as duas coisas
já vêm apontando pro domínio da tailnet no `.example`, junto com as
origens `capacitor://localhost` que o app usa internamente.

## Notificações

O `selfhosted.yaml` tem campos pra Telegram e Pushover. Este repositório
usa [ntfy](../ntfy/README.pt-BR.md) pro resto dos alertas; o Donetick ainda não fala
ntfy nativamente, então ou vai por Telegram/Pushover, ou por um webhook
via [n8n](../n8n/README.pt-BR.md).

## Auto-update

Sem `AutoUpdate=` — tag explícita (`v0.1.76`), bump manual (regra 9 do
convenções). O upstream publica **beta junto das estáveis** (havia
`v0.1.77-beta.3` ao lado da `v0.1.76` quando isto foi escrito), daí o
`wud.tag.include=^v[0-9]+.[0-9]+.[0-9]+$` na unit. Projeto em `0.x`:
ler o changelog antes de subir.

## Backup & Recuperação

```bash
systemctl --user stop donetick
tar -czf donetick-backup-$(date +%Y%m%d-%H%M%S).tar.gz \
  -C ~/.config/containers/volumes donetick
systemctl --user start donetick
```

O `config/` entra no backup junto — sem o mesmo segredo de JWT, todas as
sessões caem.

## Comandos úteis

```bash
systemctl --user status donetick
podman logs -f donetick
```

## Créditos

Deploy Quadlet baseado no [Donetick](https://github.com/donetick/donetick)
(AGPL-3.0).
