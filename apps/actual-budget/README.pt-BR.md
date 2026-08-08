# Actual Budget — Podman Quadlet (rootless)

**[🇬🇧 Read in English](./README.md)**

Deploy do [Actual Budget](https://actualbudget.org) (servidor de sync)
via Podman Quadlet — orçamento pessoal self-hosted, local-first.

## Arquivos

```
actual.container   # unit principal
```

## Pré-requisitos

- Podman rootless com systemd `--user` funcionando

## Instalação

```bash
python3 install.py actual-budget            # dry-run: mostra o que vai fazer
python3 install.py actual-budget --apply
```

Só na rede local, `--access local`; na tailnet e na LAN, `--access
both`. Acrescentar `--href-local` faz o link do dashboard apontar pra LAN. O script cria os diretórios, grava o
`.env`, gera os secrets, ajusta o dono dos volumes, sobe o serviço e
imprime o endereço no fim — ver
[Instalando e operando](../../docs/pt-BR/instalacao.md) no README
raiz.

Acessar em `http://localhost:5006` ou, via
[tsdproxy](../tsdproxy/README.pt-BR.md) (tailnet), `https://actual.<your-tailnet>.ts.net`
— trocar isso em `homepage.href` no `.container` e, se for usar o
`HOMEPAGE_ALLOWED_HOSTS`/domínio próprio, ajustar também lá.

<details>
<summary><b>Instalação manual</b> (avançado) — os mesmos passos, um a um</summary>


```bash
# 1. Baixar a unit (sem precisar clonar o repositório)
mkdir -p ~/.config/containers/systemd
wget -P ~/.config/containers/systemd/ \
  https://raw.githubusercontent.com/wallacepnts/quadlet-homelab/main/apps/actual-budget/actual.container

# 2. Diretório de dados — bind mount exige que já exista antes do start.
#    O próprio Actual cria server-files/ e user-files/ dentro dele.
mkdir -p ~/.config/containers/volumes/actual/data

# 3. Env — baixar o exemplo (TZ obrigatório, resto é opcional — ver
#    https://actualbudget.org/docs/config/)
mkdir -p ~/.config/containers/env
wget -O ~/.config/containers/env/actual.env \
  https://raw.githubusercontent.com/wallacepnts/quadlet-homelab/main/apps/actual-budget/.env.example

# 4. Subir
systemctl --user daemon-reload
systemctl --user start actual
```

Acessar em `http://localhost:5006` ou, via
[tsdproxy](../tsdproxy/README.pt-BR.md) (tailnet), `https://actual.<your-tailnet>.ts.net`
— trocar isso em `homepage.href` no `.container` e, se for usar o
`HOMEPAGE_ALLOWED_HOSTS`/domínio próprio, ajustar também lá.

</details>

## Onde mora o projeto (o repo antigo está arquivado)

O `actualbudget/actual-server` foi **arquivado em fev/2025** e o código
migrou pro monorepo `actualbudget/actual`, em `packages/sync-server` —
por isso os links deste README apontam pra lá. **A imagem Docker seguiu
com o nome antigo**: `docker.io/actualbudget/actual-server` continua
sendo a publicada e ativa (conferido: `latest` e `26.8.0` batem com a
release `v26.8.0` do repo novo). Não existe imagem `actualbudget/actual`
— repo arquivado aqui não significa imagem abandonada.

## Health check

`HealthCmd` usa o script oficial de health check do próprio projeto
(`node /app/src/scripts/health-check.js`, mesmo comando do
[`docker-compose.yml` oficial](https://github.com/actualbudget/actual/blob/master/packages/sync-server/docker-compose.yml)).
A imagem é Debian, não minimal — tem shell/Node.js disponíveis, então o
health check funciona de verdade (diferente do any-sync-bundle).

## Auto-update

**Ligado**, ao contrário da política padrão do resto do repo (regra 9 do
convenções) — exceção deliberada, porque aqui as duas condições da regra
9 realmente se cumprem: `HealthCmd` real (o script oficial) dá rollback
automático de verdade, e não há dado de terceiros em jogo.

```ini
Image=docker.io/actualbudget/actual-server:latest
AutoUpdate=registry
```

Não existe tag "só patch" pro `actual-server` (só tags exatas tipo
`26.7.0`, que nunca mudam de digest, ou `latest`/`edge`/`nightly`, que
flutuam por qualquer versão) — usar `:latest` é a própria recomendação
oficial do projeto pra maioria dos usuários, então foi essa a escolhida.

```bash
podman auto-update --dry-run              # prévia, sem aplicar nada
podman auto-update --rollback actual      # reverter manualmente se precisar
```

`podman-auto-update.timer` precisa estar ativo pra isso rodar sozinho
1x/dia — `systemctl --user enable --now podman-auto-update.timer` (é
compartilhado entre todos os serviços deste repo, só precisa ligar uma
vez).

**Fazer backup antes de qualquer atualização importante** (ver seção
abaixo) — o rollback automático cobre "não ficou `healthy`", não cobre
"ficou healthy mas com um bug silencioso nos dados".

## Backup & Recuperação

Todo o estado (orçamento, `server-files`, `user-files`) fica em
`volumes/actual/data/`. Parar o serviço antes de copiar:

```bash
systemctl --user stop actual
tar -czf actual-backup-$(date +%Y%m%d-%H%M%S).tar.gz \
  -C ~/.config/containers/volumes actual
systemctl --user start actual
```

## Comandos úteis

```bash
systemctl --user status actual
podman logs -f actual
podman exec actual node /app/src/scripts/health-check.js
```

## Créditos

Deploy Quadlet baseado no [Actual Budget](https://github.com/actualbudget/actual).
Licença original: MIT.
