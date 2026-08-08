# Invio — Podman Quadlet (rootless)

**[🇬🇧 Read in English](./README.md)**

Deploy do [Invio](https://github.com/kittendevv/Invio) (emissão e controle
de faturas) via Podman Quadlet, usando a imagem oficial
`ghcr.io/kittendevv/invio`.

*"Self-hosted invoicing without the bloat"* — cliente, item, fatura, PDF.
Sem contabilidade, sem CRM, sem assinatura mensal.

## Arquitetura

Container único (SvelteKit + supervisord), **SQLite** em `/app/data`
([regra 22](../../docs/pt-BR/convencoes.md)).

Hardening medido: `DropCapability=ALL` passa. **`ReadOnly` foi recusado** —
o supervisord da imagem grava `/app/supervisord.log`. Tentei contornar de
duas formas e nenhuma serve: `Tmpfs=/app` mascara a aplicação inteira, e
bind de um arquivo que não existe faz o Podman criar um diretório no
lugar. Fica sem `ReadOnly` mesmo.

## O `ORIGIN` não é decoração

O SvelteKit valida a origem em todo `POST` como proteção de CSRF. Se o
`ORIGIN` não for **exatamente** a URL pela qual você acessa, o app abre
normalmente e depois recusa qualquer formulário — inclusive o login, sem
mensagem que ajude. Trocar `<your-tailnet>` no `.env` antes de subir.

## Arquivos

```
invio.container   # unit principal
.env.example      # usuário admin, ORIGIN e caminho do banco
install.ini       # receitas dos secrets
```

## Instalação

```bash
python3 install.py invio            # dry-run: mostra o que vai fazer
python3 install.py invio --apply
```

Só na rede local, `--access local`; na tailnet e na LAN, `--access
both`. Acrescentar `--href-local` faz o link do dashboard apontar pra LAN. O script cria os diretórios, grava o
`.env`, gera os secrets, ajusta o dono dos volumes, sobe o serviço e
imprime o endereço no fim — ver
[Instalando e operando](../../docs/pt-BR/instalacao.md) no README
raiz.

Acessar `http://<ip-do-host>:8106` (ou via [tsdproxy](../tsdproxy/README.pt-BR.md) em
`https://invio.<your-tailnet>.ts.net`). O usuário é o `ADMIN_USER` do
`.env`; a senha está em
`~/.config/containers/secrets/invio/admin-pass.txt`.

<details>
<summary><b>Instalação manual</b> (avançado) — os mesmos passos, um a um</summary>


```bash
# 1. Baixar a unit (sem precisar clonar o repositório)
mkdir -p ~/.config/containers/systemd
wget -P ~/.config/containers/systemd/ \
  https://raw.githubusercontent.com/wallacepnts/quadlet-homelab/main/apps/invio/invio.container

# 2. Diretório de dados
mkdir -p ~/.config/containers/volumes/invio/data

# 3. Variáveis — trocar <your-tailnet> no ORIGIN
mkdir -p ~/.config/containers/env
wget -O ~/.config/containers/env/invio.env \
  https://raw.githubusercontent.com/wallacepnts/quadlet-homelab/main/apps/invio/.env.example
${EDITOR:-vi} ~/.config/containers/env/invio.env

# 4. Secrets — a senha do admin e a chave que assina a sessão. Não vão no
#    .env de propósito ([regra 2](../../docs/pt-BR/convencoes.md)).
mkdir -p ~/.config/containers/secrets/invio
python3 -c "import secrets;print(secrets.token_urlsafe(18),end='')" \
  > ~/.config/containers/secrets/invio/admin-pass.txt
python3 -c "import secrets;print(secrets.token_hex(32),end='')" \
  > ~/.config/containers/secrets/invio/jwt-secret.txt
chmod 600 ~/.config/containers/secrets/invio/*.txt
podman secret create invio-admin-pass ~/.config/containers/secrets/invio/admin-pass.txt
podman secret create invio-jwt-secret ~/.config/containers/secrets/invio/jwt-secret.txt

# 5. Subir
systemctl --user daemon-reload
systemctl --user start invio
```

Acessar `http://<ip-do-host>:8106` (ou via [tsdproxy](../tsdproxy/README.pt-BR.md) em
`https://invio.<your-tailnet>.ts.net`). O usuário é o `ADMIN_USER` do
`.env`; a senha está em
`~/.config/containers/secrets/invio/admin-pass.txt`.

Com o [`install.py`](../../install.py) os passos 2 a 5 saem de uma vez:

```bash
python3 install.py invio --apply
```

</details>

## Auto-update

Sem `AutoUpdate=` — tag explícita (`v2.1.1`), bump manual (regra 9 do
convenções). Fatura emitida é registro fiscal: backup antes de subir de
versão. O repositório publica também `main`, `latest` e tags de PR
(`pr-123`), daí o `wud.tag.include` restringindo a `vX.Y.Z`.

## Backup & Recuperação

```bash
python3 install.py invio --backup --apply --out ~/backups
```

Leva o SQLite, os secrets e o `.env` — o suficiente pra restaurar. Trocar
o `invio-jwt-secret` desloga todo mundo, então ele precisa vir junto.

## Comandos úteis

```bash
systemctl --user status invio
podman logs -f invio
cat ~/.config/containers/secrets/invio/admin-pass.txt
```

## Créditos

Deploy Quadlet baseado no [Invio](https://github.com/kittendevv/Invio) de
[kittendevv](https://github.com/kittendevv) (Unlicense).
