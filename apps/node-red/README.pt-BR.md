# Node-RED — Podman Quadlet (rootless)

**[🇬🇧 Read in English](./README.md)**

Deploy do [Node-RED](https://nodered.org) (automação de fluxos via
editor visual de nós — conecta APIs, dispositivos e serviços sem
programar do zero) via Podman Quadlet, usando a imagem oficial
[`nodered/node-red`](https://hub.docker.com/r/nodered/node-red)
(variante minimal).

## Arquitetura

Container único, roda com **uid fixo `node-red` (1000), sem usermod
interno** — testado na prática: sem `UserNS=keep-id`, trava logo no
start com `EACCES: permission denied` tentando copiar o `settings.js`
padrão pro volume. Mesmo caso do [Immich](../immich/README.pt-BR.md) (imagem com uid
fixo e sem chown próprio precisa de `UserNS=keep-id`; a maioria das
outras imagens deste repositório faz usermod internamente e por isso
não precisa).

Um volume só (`/data`) — guarda flows, config (`settings.js`,
copiado automaticamente da imagem no primeiro start), node_modules dos
nodes extras instalados pela paleta, e a chave de criptografia de
credenciais.

**Chave de credenciais gerada e salva automaticamente** — no primeiro
start, o Node-RED cria uma `_credentialSecret` aleatória e grava em
`data/.config.runtime.json`, testado na prática. Como `data/` é
persistido, essa chave sobrevive a restart normal (diferente do
[Monica](../monica/README.pt-BR.md)/[Authentik](../authentik/README.pt-BR.md), que exigem secret
próprio pra isso não acontecer) — não precisa de nenhum passo manual
extra, mas dá pra fixar a sua própria via `credentialSecret` em
`settings.js` se preferir controlar isso explicitamente.

**Sem autenticação própria por padrão** — mesmo modelo de confiança já
usado pelo [WUD](../wud/README.pt-BR.md)/[Homepage](../homepage/README.pt-BR.md) neste repositório:
protegido só por estar na tailnet, não por login. Dá pra habilitar
`adminAuth` em `settings.js` depois, se quiser.

## Arquivos

```
node-red.container       # unit principal
```

## Pré-requisitos

- Podman rootless com systemd `--user` funcionando

## Instalação

```bash
python3 install.py node-red            # dry-run: mostra o que vai fazer
python3 install.py node-red --apply
```

Só na rede local, `--access local`; na tailnet e na LAN, `--access
both`. Acrescentar `--href-local` faz o link do dashboard apontar pra LAN. O script cria os diretórios, grava o
`.env`, gera os secrets, ajusta o dono dos volumes, sobe o serviço e
imprime o endereço no fim — ver
[Instalando e operando](../../docs/pt-BR/instalacao.md) no README
raiz.

Acessar `http://<ip-do-host>:1880` (ou via [tsdproxy](../tsdproxy/README.pt-BR.md) em
`https://node-red.<your-tailnet>.ts.net`) — abre direto no editor, sem
tela de login (ver "Sem autenticação própria" acima).

<details>
<summary><b>Instalação manual</b> (avançado) — os mesmos passos, um a um</summary>


```bash
# 1. Baixar as units (sem precisar clonar o repositório)
mkdir -p ~/.config/containers/systemd
wget -P ~/.config/containers/systemd/ \
  https://raw.githubusercontent.com/wallacepnts/quadlet-homelab/main/apps/node-red/node-red.container

# 2. Diretório de dados — bind mount exige que já exista antes do start
mkdir -p ~/.config/containers/volumes/node-red/data

# 3. Env não-secreto
mkdir -p ~/.config/containers/env
wget -O ~/.config/containers/env/node-red.env \
  https://raw.githubusercontent.com/wallacepnts/quadlet-homelab/main/apps/node-red/.env.example

# 4. Subir
systemctl --user daemon-reload
systemctl --user start node-red
```

Acessar `http://<ip-do-host>:1880` (ou via [tsdproxy](../tsdproxy/README.pt-BR.md) em
`https://node-red.<your-tailnet>.ts.net`) — abre direto no editor, sem
tela de login (ver "Sem autenticação própria" acima).

</details>

## Auto-update

Sem `AutoUpdate=` — tag explícita (`5.0.4-minimal`), bump manual (regra
9 das convenções). A imagem tem `wget`/`curl`/healthcheck real — daria
pra habilitar `AutoUpdate=registry` com rollback funcional, mas
flows/credenciais são dado real do usuário, revisão manual antes de
atualizar (nodes de paleta instalados manualmente também podem não ser
compatíveis com toda versão nova).

## Backup & Recuperação

```bash
systemctl --user stop node-red
tar -czf node-red-backup-$(date +%Y%m%d-%H%M%S).tar.gz \
  -C ~/.config/containers/volumes node-red
systemctl --user start node-red
```

`data/.config.runtime.json` (chave de credenciais) precisa estar nesse
backup — sem ela, credenciais salvas em flows que usam nodes
autenticados (APIs, bancos, etc.) ficam ilegíveis.

## Comandos úteis

```bash
systemctl --user status node-red
podman logs -f node-red
podman exec node-red wget -qO- http://127.0.0.1:1880/
```

## Créditos

Deploy Quadlet baseado no
[Node-RED](https://github.com/node-red/node-red) (Apache-2.0).
