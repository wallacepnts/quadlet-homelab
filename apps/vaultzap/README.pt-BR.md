# VaultZap — Podman Quadlet (rootless)

**[🇬🇧 Read in English](./README.md)**

Deploy do [VaultZap](https://github.com/wallacepnts/vaultzap) (arquivo
local e navegável de conversas exportadas do WhatsApp — busca full-text,
galeria de mídia, calendário) via Podman Quadlet.

**A unit vem do próprio projeto** ([`deploy/vaultzap.container`](https://github.com/wallacepnts/vaultzap/blob/main/deploy/vaultzap.container)),
que já publica um Quadlet oficial e a documenta em
[`docs/quadlet.md`](https://github.com/wallacepnts/vaultzap/blob/main/docs/quadlet.md).
Aqui ela só ganha o que é convenção deste repositório: `ContainerName=`,
labels de [tsdproxy](../tsdproxy/README.pt-BR.md) e [homepage](../homepage/README.pt-BR.md), e
`Notify=healthy`. O resto é upstream — em conflito, o upstream manda.

## Arquitetura

Container único (binário Go + SQLite), **um dos mais travados deste
repositório** — tudo isso vem do upstream:

```ini
UserNS=keep-id:uid=65532,gid=65532   # nonroot, mapeado pro seu uid
ReadOnly=true                         # filesystem raiz somente leitura
Tmpfs=/tmp
NoNewPrivileges=true
DropCapability=ALL                    # nenhuma capability
```

Dois volumes: `data/` (banco `vaultzap.db` + mídia importada) e `inbox/`
(onde você solta os `.zip` exportados do WhatsApp; o serviço importa e
move pra `.imported/`).

**Com `AutoUpdate=registry` ligado** — terceiro caso neste repositório,
junto de [actual-budget](../actual-budget/README.pt-BR.md) e [homepage](../homepage/README.pt-BR.md).
Cumpre a [regra 9](../../docs/pt-BR/convencoes.md): tem `HealthCmd` real (subcomando
`healthcheck` do próprio binário), e aqui o critério "não confiar em
release de terceiro" não se aplica — as releases são suas. Por isso
também não leva `wud.watch`: o auto-update já cobre.

## Arquivos

```
vaultzap.container   # unit (cópia do upstream + convenções deste repo)
```

## Pré-requisitos

- Podman rootless com systemd `--user` funcionando
- `TAILNET` definida (ver [homepage](../homepage/README.pt-BR.md)), se for usar o
  dashboard

## Instalação

```bash
python3 install.py vaultzap            # dry-run: mostra o que vai fazer
python3 install.py vaultzap --apply
```

Só na rede local, `--access local`; na tailnet e na LAN, `--access
both`. Acrescentar `--href-local` faz o link do dashboard apontar pra LAN. O script cria os diretórios, grava o
`.env`, gera os secrets, ajusta o dono dos volumes, sobe o serviço e
imprime o endereço no fim — ver
[Instalando e operando](../../docs/pt-BR/instalacao.md) no README
raiz.

Acessar `http://<ip-do-host>:8927` (ou via [tsdproxy](../tsdproxy/README.pt-BR.md) em
`https://vaultzap.<your-tailnet>.ts.net`). Soltar os exports do WhatsApp
em `~/.config/containers/volumes/vaultzap/inbox/` — o serviço importa
sozinho.

<details>
<summary><b>Instalação manual</b> (avançado) — os mesmos passos, um a um</summary>


```bash
# 1. Baixar a unit (um arquivo só -> fica solto em systemd/)
mkdir -p ~/.config/containers/systemd
wget -P ~/.config/containers/systemd/ \
  https://raw.githubusercontent.com/wallacepnts/quadlet-homelab/main/apps/vaultzap/vaultzap.container

# 2. Diretórios — bind mount exige que já existam antes do start
mkdir -p ~/.config/containers/volumes/vaultzap/{data,inbox}

# 3. Env
mkdir -p ~/.config/containers/env
wget -O ~/.config/containers/env/vaultzap.env \
  https://raw.githubusercontent.com/wallacepnts/quadlet-homelab/main/apps/vaultzap/.env.example

# 4. Ícone do dashboard (o projeto tem o próprio, não há equivalente em
#    dashboard-icons)
mkdir -p ~/.config/containers/volumes/homepage/icons
wget -O ~/.config/containers/volumes/homepage/icons/vaultzap.svg \
  https://raw.githubusercontent.com/wallacepnts/vaultzap/main/internal/web/static/img/favicon.svg
systemctl --user restart homepage   # só detecta ícone novo depois de reiniciar

# 5. Subir
systemctl --user daemon-reload
systemctl --user start vaultzap
```

Acessar `http://<ip-do-host>:8927` (ou via [tsdproxy](../tsdproxy/README.pt-BR.md) em
`https://vaultzap.<your-tailnet>.ts.net`). Soltar os exports do WhatsApp
em `~/.config/containers/volumes/vaultzap/inbox/` — o serviço importa
sozinho.

</details>

## Proteger com senha (ligado)

**Está ligado neste deploy.** O acesso pede usuário e senha pelo diálogo
nativo do navegador (`WWW-Authenticate: Basic realm="vaultzap"`), tanto
em `http://<ip-do-host>:8927` quanto pela tailnet — o
[tsdproxy](../tsdproxy/README.pt-BR.md) repassa o cabeçalho `Authorization` sem
configuração extra.

```bash
mkdir -p ~/.config/containers/secrets/vaultzap
printf 'usuario:senha-forte' > ~/.config/containers/secrets/vaultzap/basic-auth.txt
chmod 600 ~/.config/containers/secrets/vaultzap/basic-auth.txt
podman secret create vaultzap-basic-auth ~/.config/containers/secrets/vaultzap/basic-auth.txt
```

### `printf`, não `echo`

O upstream aceita duas formas, `VAULTZAP_BASIC_AUTH` (valor direto) e
`VAULTZAP_BASIC_AUTH_FILE` (caminho), e **recusa as duas juntas** — sai
com `defina VAULTZAP_BASIC_AUTH ou VAULTZAP_BASIC_AUTH_FILE, não as
duas`, em vez de deixar uma vencer em silêncio.

A diferença que morde: **a forma `_FILE` apara espaço em branco, a direta
não.** Esta unit usa a direta (`type=env`, ver abaixo), então um `echo`
no lugar do `printf` coloca um `\n` no fim da senha — e aí o login falha
para sempre com a senha certa digitada, sem nenhuma mensagem que ajude.

Formato é `usuario:senha`, cortado no primeiro `:`; qualquer lado vazio
derruba o start com `VAULTZAP_BASIC_AUTH inválido`.

### Por que `type=env` e não `type=mount`

O jeito "natural" seria montar o secret como arquivo e usar a forma
`_FILE`. **Não funciona com `ReadOnly=true`**, e nem um `Tmpfs=/run`
resolve — o Podman cria o ponto de montagem contra o rootfs antes do
tmpfs valer:

```
error mounting ... to rootfs at "/run/secrets/vaultzap_basic_auth":
make mountpoint: read-only file system
```

Testado nas duas formas. `type=env` entrega o valor sem tocar no
filesystem, e o `podman inspect` mostra só o nome do secret, não o valor.

### O healthcheck continua funcionando

`/healthz` fica **fora** do middleware de autenticação de propósito — no
`main.go` do upstream ele é registrado no mux externo, e o handler
autenticado é montado em `/`. O `HealthCmd=["/vaultzap", "healthcheck"]`
bate exatamente nessa URL, sem credencial, então ligar o Basic Auth não
quebra o `Notify=healthy`. Confirmado depois de ligar: `healthy`.

### Trocando a senha

```bash
printf 'usuario:nova-senha' > ~/.config/containers/secrets/vaultzap/basic-auth.txt
podman secret rm vaultzap-basic-auth
podman secret create vaultzap-basic-auth ~/.config/containers/secrets/vaultzap/basic-auth.txt
systemctl --user restart vaultzap
```

## Auto-update

**Ligado** (`AutoUpdate=registry` + tag `latest`) — ver "Arquitetura"
acima pro porquê. Depende do timer do host, ligado uma vez só:

```bash
systemctl --user enable --now podman-auto-update.timer
podman auto-update --dry-run   # prévia, sem aplicar
```

Pra fixar numa versão específica, trocar `Image=` pra uma tag exata e
remover a linha `AutoUpdate=`.

## Backup & Recuperação

```bash
systemctl --user stop vaultzap
tar -czf vaultzap-backup-$(date +%Y%m%d-%H%M%S).tar.gz \
  -C ~/.config/containers/volumes vaultzap
systemctl --user start vaultzap
```

`data/vaultzap.db` é SQLite comum — dá pra abrir com `sqlite3` direto,
sem o serviço no ar.

## Comandos úteis

```bash
systemctl --user status vaultzap
podman logs -f vaultzap
podman exec vaultzap /vaultzap healthcheck
```

## Créditos

[VaultZap](https://github.com/wallacepnts/vaultzap) (AGPL-3.0), de
[wallacepnts](https://github.com/wallacepnts) — a unit deste diretório é
a oficial do projeto, com as convenções deste repositório por cima.
