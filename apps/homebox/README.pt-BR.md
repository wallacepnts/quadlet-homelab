# HomeBox — Podman Quadlet (rootless)

**[🇬🇧 Read in English](./README.md)**

Deploy do [HomeBox](https://github.com/sysadminsmedia/homebox) (inventário
doméstico) via Podman Quadlet, usando a imagem oficial
`ghcr.io/sysadminsmedia/homebox`.

Catálogo do que você tem: onde está, quanto custou, quando comprou, nota
fiscal e manual anexados, garantia com data de vencimento. Complementa o
[LubeLogger](../lubelogger/README.pt-BR.md), que faz o mesmo pros veículos.

## Arquitetura

Container único, Go, **SQLite embutido** — a imagem já traz
`HBOX_DATABASE_SQLITE_PATH` apontando pro `/data` (regra 22 do README
raiz). Um volume só, guarda banco e anexos.

**É o serviço mais endurecido do repositório**, junto com
[uptime-kuma](../uptime-kuma/README.pt-BR.md) e [ntfy](../ntfy/README.pt-BR.md): `ReadOnly=true`,
`DropCapability=ALL` e `User=1000` — testado exercitando o app, com a UI
e o `/api/v1/status` respondendo 200 e o banco sendo criado no volume.

### O secret obrigatório

Desde a 0.26 o HomeBox **não sobe** sem `HBOX_AUTH_API_KEY_PEPPER` — o
processo morre no start com:

```
panic: auth.api_key_pepper must be set to at least 32 bytes;
generate with `openssl rand -base64 48`
```

Daí o `podman secret` no passo 3. **Trocar o valor depois invalida todas
as API keys já emitidas** (não afeta login normal), então ele entra no
backup junto com o volume.

### Sobre a tag da imagem

As releases no GitHub são `v0.26.2`, mas **a tag da imagem não tem o
`v`**: `ghcr.io/sysadminsmedia/homebox:0.26.2`. Copiar o número da página
de releases direto pro `Image=` dá `manifest unknown`.

## Arquivos

```
homebox.container   # unit principal
.env.example        # cadastro, moeda, limite de upload
```

## Pré-requisitos

- Podman rootless com systemd `--user` funcionando
- `podman secret` ([regra 2](../../docs/pt-BR/convencoes.md))

## Instalação

```bash
python3 install.py homebox            # dry-run: mostra o que vai fazer
python3 install.py homebox --apply
```

Só na rede local, `--access local`; na tailnet e na LAN, `--access
both`. Acrescentar `--href-local` faz o link do dashboard apontar pra LAN. O script cria os diretórios, grava o
`.env`, gera os secrets, ajusta o dono dos volumes, sobe o serviço e
imprime o endereço no fim — ver
[Instalando e operando](../../docs/pt-BR/instalacao.md) no README
raiz.

Acessar `http://<ip-do-host>:3100` (ou via [tsdproxy](../tsdproxy/README.pt-BR.md) em
`https://homebox.<your-tailnet>.ts.net`) e criar a conta.

<details>
<summary><b>Instalação manual</b> (avançado) — os mesmos passos, um a um</summary>


```bash
# 1. Baixar a unit (sem precisar clonar o repositório)
mkdir -p ~/.config/containers/systemd
wget -P ~/.config/containers/systemd/ \
  https://raw.githubusercontent.com/wallacepnts/quadlet-homelab/main/apps/homebox/homebox.container

# 2. Diretório + dono correspondente ao User=1000 da unit.
#    `podman unshare` roda o chown DENTRO do user namespace, que é onde
#    o 1000 do container existe (no host isso vira 100999).
mkdir -p ~/.config/containers/volumes/homebox/data
podman unshare chown -R 1000:1000 ~/.config/containers/volumes/homebox/data

# 3. Secret obrigatório (ver acima)
mkdir -p ~/.config/containers/secrets/homebox
openssl rand -base64 48 | tr -d '\n' \
  > ~/.config/containers/secrets/homebox/api-key-pepper.txt
chmod 600 ~/.config/containers/secrets/homebox/api-key-pepper.txt
podman secret create homebox-api-key-pepper \
  ~/.config/containers/secrets/homebox/api-key-pepper.txt

# 4. Variáveis. Subir com o cadastro ABERTO pra criar a sua conta —
#    o passo 6 fecha depois.
mkdir -p ~/.config/containers/env
wget -O ~/.config/containers/env/homebox.env \
  https://raw.githubusercontent.com/wallacepnts/quadlet-homelab/main/apps/homebox/.env.example
sed -i 's/^HBOX_OPTIONS_ALLOW_REGISTRATION=false/HBOX_OPTIONS_ALLOW_REGISTRATION=true/' \
  ~/.config/containers/env/homebox.env

# 5. Subir
systemctl --user daemon-reload
systemctl --user start homebox
```

Acessar `http://<ip-do-host>:3100` (ou via [tsdproxy](../tsdproxy/README.pt-BR.md) em
`https://homebox.<your-tailnet>.ts.net`) e criar a conta.

```bash
# 6. Fechar o cadastro depois de criar a sua conta
sed -i 's/^HBOX_OPTIONS_ALLOW_REGISTRATION=true/HBOX_OPTIONS_ALLOW_REGISTRATION=false/' \
  ~/.config/containers/env/homebox.env
systemctl --user restart homebox
# conferir: allowRegistration deve virar false
curl -s http://127.0.0.1:3100/api/v1/status | grep -o '"allowRegistration":[a-z]*'
```

</details>

## Configuração

O `.env.example` já vem com duas escolhas deste repositório:

- **`HBOX_OPTIONS_CHECK_GITHUB_RELEASE=false`** — o HomeBox consulta a
  API do GitHub sozinho pra avisar de versão nova. Quem faz isso aqui é o
  [wud](../wud/README.pt-BR.md), então é uma saída pra internet a menos.
- **`HBOX_WEB_MAX_UPLOAD_SIZE=50`** — o default são 10 MB, e nota fiscal
  escaneada ou manual em PDF passa disso fácil.

Fora isso, `HBOX_OPTIONS_CURRENCIES=BRL` define a moeda dos valores.

## Auto-update

Sem `AutoUpdate=` — tag explícita (`0.26.2`), bump manual (regra 9 do
convenções). O inventário é dado real seu, e migração de schema entre
versões do HomeBox não é rara: ler as release notes e fazer backup antes.

## Backup & Recuperação

```bash
systemctl --user stop homebox
tar -czf homebox-backup-$(date +%Y%m%d-%H%M%S).tar.gz \
  -C ~/.config/containers/volumes homebox
systemctl --user start homebox
```

O secret (`~/.config/containers/secrets/homebox/`) precisa de backup
separado — sem o mesmo pepper, as API keys emitidas param de valer.

Restaurando em outra máquina, refazer o `podman unshare chown` do passo 2
depois de extrair: o tar preserva o uid antigo, que pode não ser o mesmo
mapeamento no destino.

## Comandos úteis

```bash
systemctl --user status homebox
podman logs -f homebox
curl -s http://127.0.0.1:3100/api/v1/status
```

## Créditos

Deploy Quadlet baseado no
[HomeBox](https://github.com/sysadminsmedia/homebox) da
[Sysadmins Media](https://github.com/sysadminsmedia) (AGPL-3.0), fork
mantido do projeto original de [hay-kot](https://github.com/hay-kot).
