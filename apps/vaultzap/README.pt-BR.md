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
.env.example         # o ambiente, do deploy/vaultzap.env.example do upstream
install.ini          # o override de upstream pro updates.py
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
`.env`, ajusta o dono dos volumes, sobe o serviço e imprime o endereço no fim — ver
[Instalando e operando](../../docs/pt-BR/instalacao.md) no README
raiz.

Acessar `http://<ip-do-host>:8927` (ou via [tsdproxy](../tsdproxy/README.pt-BR.md) em
`https://vaultzap.<your-tailnet>.ts.net`) e **definir usuário e senha na hora**
— o primeiro acesso mostra uma tela de cadastro, e enquanto ninguém preencher,
quem alcançar a porta primeiro pode. Depois é soltar os exports do WhatsApp
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

## Como o acesso é protegido

**Tela de login, e é o padrão do upstream.** Nada é configurado aqui: no
primeiro acesso a um banco novo, o app mostra uma tela de cadastro onde você
escolhe usuário e senha. Só o hash é guardado (PBKDF2-HMAC-SHA256, com salt
próprio). Depois disso a tela de cadastro some, e a troca de senha passa a ser
em **Seu perfil → Alterar senha**.

> **Cadastre logo depois do primeiro start.** Enquanto ninguém cadastrou, quem
> alcançar a porta primeiro pode fazê-lo. É uma janela real, mesmo estreitada
> à tailnet. Se não precisa ser alcançável pela rede, publique só no localhost
> — `PublishPort=127.0.0.1:8927:8927`.

**Não existe limite de tentativas**, e o upstream diz o porquê: um limitador
por IP atrás de proxy reverso ou bloqueia todo mundo junto (todos chegam com o
IP do proxy) ou é contornável trocando um cabeçalho. O que protege é uma senha
boa.

### Perdeu a senha

O binário resolve, sem abrir nada pela rede:

```bash
podman exec vaultzap /vaultzap reset-password
```

Ele imprime uma senha nova, mantém o usuário e encerra todas as sessões
abertas.

### Desligar a autenticação

Só quando algo na frente já protege a porta. Descomentar no `vaultzap.env`:

```
VAULTZAP_AUTH=off
```

### Basic Auth no lugar

A tela de login substituiu o Basic Auth como padrão, mas o Basic Auth continua
funcionando e **tem precedência** quando a variável dele está definida. Este
deploy foi assim até o upstream criar a tela de login; a unit mantém a linha
comentada pra quem prefere o cabeçalho HTTP ao cookie de sessão.

```bash
mkdir -p ~/.config/containers/secrets/vaultzap
printf 'usuario:senha-forte' > ~/.config/containers/secrets/vaultzap/basic-auth.txt
chmod 600 ~/.config/containers/secrets/vaultzap/basic-auth.txt
podman secret create vaultzap-basic-auth ~/.config/containers/secrets/vaultzap/basic-auth.txt
```

Depois descomentar a linha `Secret=` na unit e reiniciar.

Três coisas desse caminho foram medidas e seguem valendo:

**`printf`, não `echo`.** O upstream aceita `VAULTZAP_BASIC_AUTH` (o valor) e
`VAULTZAP_BASIC_AUTH_FILE` (um caminho), e recusa as duas juntas em vez de
deixar uma vencer em silêncio. A forma `_FILE` apara espaços, a direta não — e
esta unit usa a direta, então um `echo` no lugar do `printf` deixa um `\n` no
fim da senha. Aí o login falha pra sempre com a senha certa digitada, e nenhuma
mensagem diz por quê.

Definir `VAULTZAP_BASIC_AUTH` **vazia** agora é erro no boot, em vez de
desligar a autenticação em silêncio. Pra rodar sem senha, deixe a variável de
fora e use `VAULTZAP_AUTH=off`.

**`type=env`, não `type=mount`.** O caminho natural seria montar o secret como
arquivo e usar a forma `_FILE`. Ele **não funciona com `ReadOnly=true`**, e nem
um `Tmpfs=/run` resolve — o Podman cria o mountpoint contra o rootfs antes do
tmpfs valer:

```
error mounting ... to rootfs at "/run/secrets/vaultzap_basic_auth":
make mountpoint: read-only file system
```

Testado dos dois jeitos. O `type=env` entrega o valor sem tocar no sistema de
arquivos, e o `podman inspect` mostra só o nome do secret, não o valor. O
quadlet do próprio upstream sugere a forma `_FILE` no bloco comentado dele; é
justamente a forma a evitar aqui.

**O healthcheck continua funcionando em qualquer modo.** O `/healthz` fica
**fora** do middleware de autenticação de propósito — no `main.go` do upstream
ele é registrado no mux externo, e o handler autenticado é montado em `/`. O
`HealthCmd=["/vaultzap", "healthcheck"]` bate exatamente nessa URL, sem
credencial, então nenhum modo de autenticação quebra o `Notify=healthy`.

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
