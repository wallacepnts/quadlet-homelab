# OpenWA — Podman Quadlet (rootless)

**[🇺🇸 Read in English](./README.md)**

Deploy do [OpenWA](https://github.com/rmyndharis/OpenWA) (gateway de API do
WhatsApp, self-hosted) via Podman Quadlet, usando a imagem oficial
`ghcr.io/rmyndharis/openwa`.

Ele transforma uma conta de WhatsApp numa API HTTP: liga o celular por QR
code e daí manda e recebe mensagem por REST, com webhooks pros eventos que
chegam. É a peça que deixa o [n8n](../n8n/) ou o
[Home Assistant](../home-assistant/) falarem com o WhatsApp sem provedor pago.

**Ele dirige a sua conta pessoal pelo mesmo canal que o WhatsApp Web usa.**
Isso não é API oficial — a conta pode ser bloqueada por volume ou por
comportamento que pareça automatizado. Tratar como automação pessoal, não como
ferramenta de disparo em massa.

## Arquitetura

Um container só: NestJS, **SQLite embutido**, mídia em disco local. Um volume,
`/app/data`, com o banco, as sessões do WhatsApp, as mídias e os plugins.

O `docker-compose.yml` oficial também traz Postgres, Redis e MinIO — os três
atrás de **profiles** do Compose, então nenhum sobe por padrão. SQLite é a
alternativa suportada pro banco (inclusive pra busca full-text, que usa FTS5),
disco local pro armazenamento, e o Redis só é necessário em deploy com várias
réplicas. Aqui um container é o deploy inteiro.

### O que ficou de fora de propósito: o proxy do socket do Docker

O compose oficial tem um quarto serviço, `tecnativa/docker-socket-proxy`, que
existe pro dashboard conseguir subir sozinho aqueles containers de
Postgres/Redis/MinIO ("Infrastructure > built-in toggles"). Os comentários do
próprio compose mandam desabilitar se você não usa esse recurso — e o
`SECURITY.md` deles diz que o proxy não consegue limitar o payload de criação
de container, então uma API comprometida poderia criar containers com bind
mount do host.

Entregar o socket do Podman pra um container voltado ao WhatsApp e exposto à
internet, pra fechar um recurso que não usamos, não é uma troca que valha.
`DOCKER_HOST` fica vazio, o `DockerService` reporta Docker indisponível e a
orquestração degrada graciosamente — exatamente o comportamento documentado.

## Arquivos

```
openwa.container    # unit principal
.env.example        # engine, nível de log, timeouts de webhook
install.ini         # receitas dos secrets
```

## Instalação

```bash
python3 install.py openwa            # dry-run: mostra o que vai fazer
python3 install.py openwa --apply
```

Só na rede local, `--access local`; na tailnet e na LAN, `--access both`.
Somando `--href-local`, o link do dashboard aponta pra LAN. O script cria os
diretórios, escreve o `.env`, gera os secrets, ajusta o dono dos volumes, sobe
o serviço e imprime o endereço no fim — ver
[Instalando e operando](../../docs/pt-BR/instalacao.md).

Abrir `http://<ip-do-host>:2785` (ou via [tsdproxy](../tsdproxy/) em
`https://openwa.<your-tailnet>.ts.net`), autenticar com a master key e ligar o
celular escaneando o QR code.

```bash
podman secret inspect --showsecret openwa-master-key
```

<details>
<summary><b>Instalação manual</b> (avançado) — os mesmos passos, um a um</summary>


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

## A engine

O OpenWA suporta duas, e a escolha pesa mais que qualquer outra configuração
daqui:

| | `whatsapp-web.js` (padrão) | `baileys` |
| --- | --- | --- |
| Como | um Chromium de verdade dirigindo o WhatsApp Web | cliente WebSocket, sem navegador |
| Custo | ~1–2 GB de RAM, centenas de processos | dezenas de MB |
| Na imagem | sim, o Chromium vem junto | sim, carregada sob demanda |

Sem definir nada, quem manda é o dashboard (Infrastructure > Engine), com
padrão `whatsapp-web.js`. Definir `ENGINE_TYPE` no `.env` sempre ganha do
dashboard.

**O hardening da unit está dimensionado pra engine com Chromium.** Se fixar
`baileys`, `PidsLimit=2048` e `Tmpfs=/tmp:size=512M` ficam muito acima do
necessário — mas sobrar não custa nada, e apertar quebra no dia em que voltar
atrás.

## Hardening

O compose oficial já roda o container `read_only`, com `cap_drop: ALL` e
`no-new-privileges`, então isso veio validado. O que cada linha custa, na
ordem da [regra 20](../../docs/pt-BR/convencoes.md):

- **`DropCapability=ALL` e cinco de volta.** O entrypoint roda como root, faz
  `chown -R openwa /app/data` no volume e só então cai pro usuário `openwa`
  via `gosu` — isso exige `CHOWN`, `DAC_OVERRIDE`, `FOWNER`, `SETGID` e
  `SETUID`. É a lista do upstream, não um chute.
- **Sem `User=`.** Mesmo motivo: a imagem larga o privilégio sozinha. Forçar
  um uid quebraria o `chown` antes de chegar no `gosu`.
- **`Tmpfs=/tmp:size=512M`, não 64M.** Com `ReadOnly=true`, `HOME`,
  `XDG_CONFIG_HOME` e `XDG_CACHE_HOME` são todos redirecionados pro `/tmp`, e
  o Chromium trata aquilo como rascunho. Medir sob uso real com
  `podman exec openwa df -h /tmp` antes de cortar.
- **`PidsLimit=2048`, não os 256 de praxe do repositório.** É o padrão do
  upstream, e o único número daqui que não é conservador: o Chromium abre um
  processo por aba, por renderer e por utilitário, vezes cada sessão ligada.

Memória não tem teto na unit — o upstream sugere 2 GB. Somar `Memory=2G` se uma
sessão desgovernada começar a machucar o host; fica de fora aqui porque um teto
duro num navegador no meio da sessão aparece como vínculo do WhatsApp morto, não
como erro.

## O banco é SQLite

`DATABASE_TYPE=sqlite` na unit, e `DATABASE_NAME` de propósito **sem valor**
no `.env` — com SQLite, um valor solto ali vira o *caminho* do arquivo de
banco, o que sob `ReadOnly=true` é um boot-loop de `SQLITE_CANTOPEN`
(upstream #677). O caminho padrão, `/app/data/openwa.sqlite`, fica dentro do
volume.

## Auto-update

Sem `AutoUpdate=` — tag explícita (`0.14.6`), bump na mão
([regra 9](../../docs/pt-BR/convencoes.md)). Projeto `0.x` andando rápido, que
guarda sessões do WhatsApp precisando ser religadas por QR code se o estado
quebrar: ler o
[CHANGELOG](https://github.com/rmyndharis/OpenWA/blob/main/CHANGELOG.md) e
fazer backup antes de subir versão.

O upstream também publica tags de commit sha junto das versões, daí o
`wud.tag.include=^[0-9]+.[0-9]+.[0-9]+$` na unit. Reparar que a tag da release
tem prefixo `v` (`v0.14.6`) e a da imagem não (`0.14.6`).

## Backup & recuperação

```bash
systemctl --user stop openwa
tar -czf openwa-backup-$(date +%Y%m%d-%H%M%S).tar.gz \
  -C ~/.config/containers/volumes openwa
systemctl --user start openwa
```

As sessões estão aí dentro. Restaurar um backup antigo por cima de um estado
mais novo **não** restaura o vínculo com o WhatsApp — o celular precisa
escanear o QR code de novo.

Os dois secrets **não** estão no volume. Perder o `openwa-key-pepper` faz toda
API key emitida parar de validar; perder o `openwa-master-key` tranca você
fora do dashboard. Os dois voltam com o `install.py`, mas as chaves que você
entregou pras integrações, não.

## Comandos úteis

```bash
systemctl --user status openwa
podman logs -f openwa
podman exec openwa df -h /tmp        # 512M dá conta?
curl -H "X-Api-Key: $KEY" http://127.0.0.1:2785/api/sessions
```

## Créditos

Deploy Quadlet baseado no [OpenWA](https://github.com/rmyndharis/OpenWA) de
[rmyndharis](https://github.com/rmyndharis) (MIT).
