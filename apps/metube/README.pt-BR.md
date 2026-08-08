# MeTube — Podman Quadlet (rootless)

**[🇬🇧 Read in English](./README.md)**

Deploy do [MeTube](https://github.com/alexta69/metube) (interface web do
`yt-dlp`) via Podman Quadlet, usando a imagem oficial
`ghcr.io/alexta69/metube`.

Cola a URL, escolhe formato e qualidade, o arquivo cai no disco. O
[media-stack](../media-stack/README.pt-BR.md) cuida de filme e série pelos \*arr; isto
aqui é pro vídeo avulso.

## Arquitetura

Container único, Python + `yt-dlp`. **Sem banco**: o estado das filas
fica em `.metube/` dentro do próprio volume de downloads.

### A inversão da escada de hardening

Vale registrar porque contraria a intuição ([convenções, regra 20](../../docs/pt-BR/convencoes.md)):
`DropCapability=ALL` **sozinho é recusado** —

```
chown: changing ownership of '/app/ui/dist/metube/3rdpartylicenses.txt':
Operation not permitted
```

— porque o entrypoint ajusta dono no start. Mas com **`User=1000` o
entrypoint não tem o que ajustar** (o `PUID` da imagem já é 1000), o
`chown` some, e o nível mais forte passa. Ou seja: o degrau mais alto
funciona e o do meio não. A lição prática é não desistir no primeiro
`chown` do log — às vezes subir um degrau resolve em vez de conceder a
capability.

## Arquivos

```
metube.container   # unit principal
```

## Instalação

```bash
python3 install.py metube            # dry-run: mostra o que vai fazer
python3 install.py metube --apply
```

Só na rede local, `--access local`; na tailnet e na LAN, `--access
both`. Acrescentar `--href-local` faz o link do dashboard apontar pra LAN. O script cria os diretórios, grava o
`.env`, gera os secrets, ajusta o dono dos volumes, sobe o serviço e
imprime o endereço no fim — ver
[Instalando e operando](../../docs/pt-BR/instalacao.md) no README
raiz.

Acessar `http://<ip-do-host>:8100` (ou via [tsdproxy](../tsdproxy/README.pt-BR.md) em
`https://metube.<your-tailnet>.ts.net`).

<details>
<summary><b>Instalação manual</b> (avançado) — os mesmos passos, um a um</summary>


```bash
# 1. Baixar a unit (sem precisar clonar o repositório)
mkdir -p ~/.config/containers/systemd
wget -P ~/.config/containers/systemd/ \
  https://raw.githubusercontent.com/wallacepnts/quadlet-homelab/main/apps/metube/metube.container

# 2. Diretório + dono correspondente ao User=1000 da unit
mkdir -p ~/.config/containers/volumes/metube/downloads
podman unshare chown -R 1000:1000 ~/.config/containers/volumes/metube

# 3. Subir
systemctl --user daemon-reload
systemctl --user start metube
```

Acessar `http://<ip-do-host>:8100` (ou via [tsdproxy](../tsdproxy/README.pt-BR.md) em
`https://metube.<your-tailnet>.ts.net`).

</details>

## Segurança

**Não tem autenticação.** Quem alcança a porta baixa o que quiser pro seu
disco. Na tailnet isso é aceitável; não expor pra fora dela. Pra colocar
login na frente, o caminho é o [Authentik](../authentik/README.pt-BR.md).

## Baixando pro media-stack

Pra que o [Jellyfin](../media-stack/README.pt-BR.md) enxergue o que o MeTube baixa, o
caminho é apontar o volume de downloads pra dentro da raiz de dados
compartilhada do media-stack em vez do diretório próprio — trocar a linha
`Volume=` da unit e refazer o `chown`. O MeTube grava como uid 1000
(100999 no host), então conferir se o Jellyfin consegue ler.

## Auto-update

Sem `AutoUpdate=` — tag explícita, bump manual ([regra 9](../../docs/pt-BR/convencoes.md)).
**A tag é a data do build** (`2026.08.04`), não semver, daí o
`wud.tag.include=^[0-9]{4}.[0-9]{2}.[0-9]{2}$`.

Vale um comentário: o `yt-dlp` embutido quebra quando o YouTube muda,
e o conserto vem numa imagem nova. É o serviço deste repositório com o
melhor argumento pra atualizar com frequência.

## Backup & Recuperação

Nada pra fazer além de copiar os vídeos, se quiser: não há banco nem
configuração fora do volume de downloads.

## Comandos úteis

```bash
systemctl --user status metube
podman logs -f metube
podman exec metube yt-dlp --version
```

## Créditos

Deploy Quadlet baseado no [MeTube](https://github.com/alexta69/metube)
de [alexta69](https://github.com/alexta69) (AGPL-3.0), que embrulha o
[yt-dlp](https://github.com/yt-dlp/yt-dlp).
