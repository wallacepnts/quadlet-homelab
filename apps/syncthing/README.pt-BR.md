# Syncthing — Podman Quadlet (rootless)

**[🇬🇧 Read in English](./README.md)**

Deploy do [Syncthing](https://syncthing.net) (sincronização de arquivos
P2P entre dispositivos, sem servidor central/nuvem de terceiros) via
Podman Quadlet, seguindo o
[guia oficial de Docker](https://github.com/syncthing/syncthing/blob/main/README-Docker.md).

## Arquitetura

Container único. PUID/PGID (default LSIO-like, sem `UserNS=keep-id` —
a própria imagem ajusta o dono do volume no primeiro start). Um volume
só (`/var/syncthing`), que guarda config, chaves e — por padrão — as
próprias pastas sincronizadas (`Sync/` dentro dele); dá pra apontar
pastas adicionais de fora depois, pela própria UI.

**Rede bridge, não `host`**: o guia oficial recomenda `network_mode: host`
pra descoberta de peers na LAN funcionar via broadcast — mesma troca já
feita pro [Home Assistant](../home-assistant/README.pt-BR.md)/Jellyfin (no
[media-stack](../media-stack/README.pt-BR.md)): perde a descoberta automática de LAN,
mantém o isolamento de rede padrão deste repositório. Descoberta
**global** (pela internet, via servidor de discovery do próprio
Syncthing) continua funcionando normal; conexão direta com um peer na
LAN ainda funciona configurando o endereço manualmente no dispositivo
remoto, só não é automático.

## Arquivos

```
syncthing.container   # unit principal
```

## Pré-requisitos

- Podman rootless com systemd `--user` funcionando

## Instalação

```bash
python3 install.py syncthing            # dry-run: mostra o que vai fazer
python3 install.py syncthing --apply
```

Só na rede local, `--access local`; na tailnet e na LAN, `--access
both`. Acrescentar `--href-local` faz o link do dashboard apontar pra LAN. O script cria os diretórios, grava o
`.env`, gera os secrets, ajusta o dono dos volumes, sobe o serviço e
imprime o endereço no fim — ver
[Instalando e operando](../../docs/pt-BR/instalacao.md) no README
raiz.

Acessar via [tsdproxy](../tsdproxy/README.pt-BR.md) (tailnet) em
`https://syncthing.<your-tailnet>.ts.net`, ou local em
`http://localhost:8384`.

<details>
<summary><b>Instalação manual</b> (avançado) — os mesmos passos, um a um</summary>


```bash
# 1. Baixar a unit (sem precisar clonar o repositório)
mkdir -p ~/.config/containers/systemd
wget -P ~/.config/containers/systemd/ \
  https://raw.githubusercontent.com/wallacepnts/quadlet-homelab/main/apps/syncthing/syncthing.container

# 2. Diretório de dados — bind mount exige que já exista antes do start
mkdir -p ~/.config/containers/volumes/syncthing/data
podman unshare chown -R 1000:1000 ~/.config/containers/volumes/syncthing   # a unit usa User=1000

# 3. Env não-secreto — baixar o exemplo, ajustar PUID/PGID pro usuário
#    que roda o Podman (mesmo dono do volume acima)
mkdir -p ~/.config/containers/env
wget -O ~/.config/containers/env/syncthing.env \
  https://raw.githubusercontent.com/wallacepnts/quadlet-homelab/main/apps/syncthing/.env.example
sed -i "s/^PUID=.*/PUID=$(id -u)/;s/^PGID=.*/PGID=$(id -g)/" \
  ~/.config/containers/env/syncthing.env

# 4. Subir
systemctl --user daemon-reload
systemctl --user start syncthing
```

Acessar via [tsdproxy](../tsdproxy/README.pt-BR.md) (tailnet) em
`https://syncthing.<your-tailnet>.ts.net`, ou local em
`http://localhost:8384`.

</details>

## Proteger a GUI (obrigatório logo no primeiro acesso)

**A imagem oficial não tem variável de ambiente pra pré-configurar
usuário/senha da GUI** (pedido em aberto desde
[syncthing/syncthing#8791](https://github.com/syncthing/syncthing/issues/8791),
sem previsão) — o Syncthing sobe **sem autenticação nenhuma** por
padrão, escutando em `0.0.0.0`. Configurar direto na UI assim que
acessar pela primeira vez: **Ações → Configurações → GUI**, preencher
usuário e senha, salvar (reinicia sozinho). Até fazer isso, qualquer um
que alcance a porta 8384 (tailnet inteira, não só você) tem acesso total
— inclusive pra adicionar pastas/dispositivos.

## Auto-update

Sem `AutoUpdate=` — tag explícita (`2.1.3`), bump manual (regra 9 do
convenções). A imagem tem `curl`/healthcheck real (daria pra habilitar
com rollback de verdade), mas os arquivos sincronizados são dado real do
usuário — revisão manual antes de atualizar, mesmo raciocínio do
[ownCloud](../owncloud/README.pt-BR.md).

## Backup & Recuperação

```bash
systemctl --user stop syncthing
tar -czf syncthing-backup-$(date +%Y%m%d-%H%M%S).tar.gz \
  -C ~/.config/containers/volumes syncthing
systemctl --user start syncthing
```

`data/` inclui tanto a config/chaves do próprio Syncthing quanto as
pastas sincronizadas que estiverem dentro dele (`data/Sync/` por
padrão) — se você apontar pastas de fora do volume pela UI, fazer backup
delas separadamente.

## Comandos úteis

```bash
systemctl --user status syncthing
podman logs -f syncthing
podman exec syncthing curl -fkLsS -m 2 127.0.0.1:8384/rest/noauth/health
```

## Créditos

Deploy Quadlet baseado no [Syncthing](https://github.com/syncthing/syncthing).
Licença original: MPL-2.0.
