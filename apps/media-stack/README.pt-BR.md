# Media Stack

<img src="https://api.iconify.design/mdi/multimedia.svg?color=%23888888" width="64" height="64" alt="">

**[🇺🇸 Read in English](./README.md)**

Jellyfin mais a cadeia *arr e os downloaders — uma pasta, doze units, cada
uma na sua porta. O Gluetun está ali para quem quiser o Deluge atrás de uma
VPN; nada depende dele.

## Primeiro acesso

Cada unit publica a própria porta e o próprio nome na tailnet; os endereços
saem no fim da instalação.

## Arquivos

```
media-stack-<app>.container       uma unit por app, doze delas
.env.example                      compartilhado: PUID, PGID e TZ
media-stack-gluetun.env.example   o provedor de VPN, só se usar o Gluetun
install.ini
docs/                             uma página por app
```

Config em `~/.config/containers/volumes/media-stack/<app>/`, mídia dentro do
`$MEDIA_DATA_DIR`. A porta de cada app está na página dele, abaixo.

O stack é uma corrente: o **Seerr** recebe o pedido, os ***arr** procuram o
título pelo **Prowlarr**, entregam o download ao **SABnzbd** ou ao **Deluge**,
renomeiam o arquivo dentro da raiz de mídia, e o **Jellyfin** ou o **Navidrome** reproduz. Cada
peça roda sozinha e serve sem as outras.

| | App | Para que serve | Versão |
| --- | --- | --- | --- |
| <img src="https://cdn.jsdelivr.net/gh/homarr-labs/dashboard-icons/svg/jellyfin.svg" width="28" height="28" alt=""> | [Jellyfin](./docs/pt-BR/jellyfin.md) | Reproduz a biblioteca — filmes, séries, música — no navegador, na TV ou no celular | `12.1` |
| <img src="https://cdn.jsdelivr.net/gh/homarr-labs/dashboard-icons/svg/navidrome.svg" width="28" height="28" alt=""> | [Navidrome](./docs/pt-BR/navidrome.md) | Toca a música que a corrente trouxe, por qualquer cliente Subsonic | `0.64.2` |
| <img src="https://cdn.jsdelivr.net/gh/homarr-labs/dashboard-icons/svg/seerr.svg" width="28" height="28" alt=""> | [Seerr](./docs/pt-BR/seerr.md) | Onde você pede um título. Repassa o pedido ao Sonarr ou ao Radarr | `v3.5.0` |
| <img src="https://cdn.jsdelivr.net/gh/homarr-labs/dashboard-icons/svg/prowlarr.svg" width="28" height="28" alt=""> | [Prowlarr](./docs/pt-BR/prowlarr.md) | Guarda a lista de indexadores e alimenta os outros *arr | `2.6.5` |
| <img src="https://cdn.jsdelivr.net/gh/homarr-labs/dashboard-icons/svg/sonarr.svg" width="28" height="28" alt=""> | [Sonarr](./docs/pt-BR/sonarr.md) | Séries: acompanha episódios novos, baixa e arquiva | `4.0.20` |
| <img src="https://cdn.jsdelivr.net/gh/homarr-labs/dashboard-icons/svg/radarr.svg" width="28" height="28" alt=""> | [Radarr](./docs/pt-BR/radarr.md) | O mesmo, para filmes | `6.4.4` |
| <img src="https://cdn.jsdelivr.net/gh/homarr-labs/dashboard-icons/svg/lidarr.svg" width="28" height="28" alt=""> | [Lidarr](./docs/pt-BR/lidarr.md) | O mesmo, para músicas | `3.1.0` |
| <img src="https://cdn.jsdelivr.net/gh/homarr-labs/dashboard-icons/svg/bazarr.svg" width="28" height="28" alt=""> | [Bazarr](./docs/pt-BR/bazarr.md) | Busca legendas para o que o Sonarr e o Radarr trouxeram | `1.6.2` |
| <img src="https://cdn.jsdelivr.net/gh/homarr-labs/dashboard-icons/svg/sabnzbd.svg" width="28" height="28" alt=""> | [SABnzbd](./docs/pt-BR/sabnzbd.md) | Baixa da Usenet | `version-5.1.3` |
| <img src="https://cdn.jsdelivr.net/gh/homarr-labs/dashboard-icons/svg/deluge.svg" width="28" height="28" alt=""> | [Deluge](./docs/pt-BR/deluge.md) | Baixa torrents | `2.2.0` |
| <img src="https://cdn.jsdelivr.net/gh/homarr-labs/dashboard-icons/svg/gluetun.svg" width="28" height="28" alt=""> | [Gluetun](./docs/pt-BR/gluetun.md) | **Opcional.** Túnel VPN para colocar o Deluge atrás | `v3.41.3` |
| <img src="https://cdn.jsdelivr.net/gh/homarr-labs/dashboard-icons/svg/dispatcharr.svg" width="28" height="28" alt=""> | [Dispatcharr](./docs/pt-BR/dispatcharr.md) | IPTV: canais, EPG e VOD, à parte da corrente acima | `0.31.0` |
| <img src="https://cdn.jsdelivr.net/gh/homarr-labs/dashboard-icons/png/downtify.png" width="28" height="28" alt=""> | [Downtify](./docs/pt-BR/downtify.md) | Baixa músicas do Spotify na raiz de mídia | `3.4.0` |

Cada página acima diz o que o app precisa no primeiro uso e como ele se liga
aos outros. O Gluetun é a única peça opcional: o Deluge publica a porta dele e
funciona sem ele.

## Atualizar

Cada unit tem a própria tag — a tabela acima lista todas. Nada atualiza
sozinho; o comando acima aplica o que o repositório pinou.

## Remover

O nó da tailnet não é desregistrado ao remover um app: isso é no admin do Tailscale.

## Créditos

[Jellyfin](https://github.com/jellyfin/jellyfin) — GPL-2.0 ·
[Sonarr](https://github.com/Sonarr/Sonarr) ·
[Radarr](https://github.com/Radarr/Radarr) ·
[Lidarr](https://github.com/Lidarr/Lidarr) ·
[Prowlarr](https://github.com/Prowlarr/Prowlarr) ·
[Bazarr](https://github.com/morpheus65535/bazarr) ·
[Seerr](https://github.com/seerr-team/seerr) ·
[SABnzbd](https://github.com/sabnzbd/sabnzbd) ·
[Deluge](https://github.com/deluge-torrent/deluge) ·
[Gluetun](https://github.com/qdm12/gluetun) ·
[Dispatcharr](https://github.com/Dispatcharr/Dispatcharr) ·
[Downtify](https://github.com/henriquesebastiao/downtify)

A maioria das imagens vem do [LinuxServer.io](https://www.linuxserver.io/).

[Documentação oficial](https://jellyfin.org)
