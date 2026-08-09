# Media Stack

**[🇺🇸 Read in English](./README.md)**

Jellyfin mais a cadeia *arr e os downloaders — uma pasta, doze units, cada
uma na sua porta. O Gluetun está ali para quem quiser o Deluge atrás de uma
VPN; nada depende dele.

## Instalar
```bash
qh media-stack            # mostra o plano
qh media-stack --apply
```

Cada unit publica a própria porta e o próprio nome na tailnet; os endereços
saem no fim da instalação.

<details>
<summary><b>Instalação manual</b></summary>

```bash
# 1. Baixar as units (sem precisar clonar o repositório; inclui
#    media-stack-gluetun.container — só importa se for usar a seção de VPN abaixo,
#    sem ativar fica parado sem nenhum custo)
mkdir -p ~/.config/containers/systemd/media-stack
for f in jellyfin dispatcharr downtify prowlarr sonarr radarr lidarr \
         bazarr seerr deluge sabnzbd gluetun; do
  wget -P ~/.config/containers/systemd/media-stack/ \
    "https://raw.githubusercontent.com/wallacepnts/quadlet-homelab/main/apps/media-stack/media-stack-$f.container"
done

# 2. Raiz de mídia — a ÚNICA decisão de path desta stack inteira, via uma
#    variável de ambiente do systemd (não um EnvironmentFile= comum —
#    essa precisa existir no ambiente do *manager* pra ser expandida
#    dentro de Volume=; ver detalhes na regra correspondente do README
#    raiz).
mkdir -p ~/.config/environment.d
cat > ~/.config/environment.d/media-stack.conf <<EOF
MEDIA_DATA_DIR=$HOME/data
EOF
mkdir -p "$HOME/data"
# Se a mídia já mora em outro disco/mount, usar o path real ali em cima
# em vez de $HOME/data — nada de symlink, a variável já resolve isso.

# 3. Diretórios de config — bind mount exige que já existam antes do start
mkdir -p ~/.config/containers/volumes/media-stack/jellyfin/{config,cache}
mkdir -p ~/.config/containers/volumes/media-stack/{prowlarr,sonarr,radarr,lidarr,bazarr,seerr,deluge,sabnzbd}/config
mkdir -p ~/.config/containers/volumes/media-stack/dispatcharr/data
mkdir -p ~/.config/containers/volumes/media-stack/downtify/data
# Downtify baixa em downloads/ (dentro da raiz de mídia), a mesma pasta
# onde o Deluge salva os torrents completos — diferente do resto (passo
# 2 acima já cria a raiz, mas não downloads/, criado pelo Deluge só
# depois do primeiro uso; Downtify bind-monta esse subdiretório direto,
# então precisa existir ANTES do start, não pode esperar).
mkdir -p "$HOME/data/downloads"

# 4. Env compartilhado (LinuxServer.io) — baixar o exemplo e ajustar
#    PUID/PGID pro usuário que roda o Podman (mesmo dono de
#    MEDIA_DATA_DIR, senão os apps não conseguem escrever nela)
mkdir -p ~/.config/containers/env
wget -O ~/.config/containers/env/media-stack.env \
  https://raw.githubusercontent.com/wallacepnts/quadlet-homelab/main/apps/media-stack/.env.example
sed -i "s/^PUID=.*/PUID=$(id -u)/;s/^PGID=.*/PGID=$(id -g)/" \
  ~/.config/containers/env/media-stack.env

# 5. Aplicar a env.d nova (precisa de daemon-reload, não só reiniciar
#    o serviço — é o systemd --user que precisa reler o ambiente)
systemctl --user daemon-reload

# 6. Subir. O Gluetun fica de fora: não faz nada até você configurar um
#    provedor. Sem
#    Requires= entre serviços aqui — Dispatcharr é um container só,
#    Postgres/Redis sobem dentro dele mesmo.
systemctl --user start media-stack-jellyfin media-stack-dispatcharr media-stack-downtify media-stack-prowlarr media-stack-sonarr media-stack-radarr media-stack-lidarr media-stack-bazarr media-stack-seerr media-stack-deluge media-stack-sabnzbd

```

</details>

## Arquivos

```
media-stack-bazarr.container
media-stack-deluge.container
media-stack-dispatcharr.container
media-stack-downtify.container
media-stack-gluetun.container
media-stack-jellyfin.container
media-stack-lidarr.container
media-stack-prowlarr.container
media-stack-radarr.container
media-stack-sabnzbd.container
media-stack-seerr.container
media-stack-sonarr.container
.env.example
media-stack-gluetun.env.example
install.ini
```

O stack é uma corrente: o **Seerr** recebe o pedido, os ***arr** procuram o
título pelo **Prowlarr**, entregam o download ao **SABnzbd** ou ao **Deluge**,
renomeiam o arquivo dentro da raiz de mídia, e o **Jellyfin** reproduz. Cada
peça roda sozinha e serve sem as outras.

| | App | Para que serve | Versão |
| --- | --- | --- | --- |
| <img src="https://cdn.jsdelivr.net/gh/homarr-labs/dashboard-icons/svg/jellyfin.svg" width="28" height="28" alt=""> | [Jellyfin](./docs/pt-BR/jellyfin.md) | Reproduz a biblioteca — filmes, séries, música — no navegador, na TV ou no celular | `10.11.11` |
| <img src="https://cdn.jsdelivr.net/gh/homarr-labs/dashboard-icons/svg/seerr.svg" width="28" height="28" alt=""> | [Seerr](./docs/pt-BR/seerr.md) | Onde você pede um título. Repassa o pedido ao Sonarr ou ao Radarr | `v3.4.1` |
| <img src="https://cdn.jsdelivr.net/gh/homarr-labs/dashboard-icons/svg/prowlarr.svg" width="28" height="28" alt=""> | [Prowlarr](./docs/pt-BR/prowlarr.md) | Guarda a lista de indexadores e alimenta os outros *arr | `2.5.2` |
| <img src="https://cdn.jsdelivr.net/gh/homarr-labs/dashboard-icons/svg/sonarr.svg" width="28" height="28" alt=""> | [Sonarr](./docs/pt-BR/sonarr.md) | Séries: acompanha episódios novos, baixa e arquiva | `4.0.19` |
| <img src="https://cdn.jsdelivr.net/gh/homarr-labs/dashboard-icons/svg/radarr.svg" width="28" height="28" alt=""> | [Radarr](./docs/pt-BR/radarr.md) | O mesmo, para filmes | `6.3.0` |
| <img src="https://cdn.jsdelivr.net/gh/homarr-labs/dashboard-icons/svg/lidarr.svg" width="28" height="28" alt=""> | [Lidarr](./docs/pt-BR/lidarr.md) | O mesmo, para músicas | `3.1.0` |
| <img src="https://cdn.jsdelivr.net/gh/homarr-labs/dashboard-icons/svg/bazarr.svg" width="28" height="28" alt=""> | [Bazarr](./docs/pt-BR/bazarr.md) | Busca legendas para o que o Sonarr e o Radarr trouxeram | `1.6.0` |
| <img src="https://cdn.jsdelivr.net/gh/homarr-labs/dashboard-icons/svg/sabnzbd.svg" width="28" height="28" alt=""> | [SABnzbd](./docs/pt-BR/sabnzbd.md) | Baixa da Usenet | `version-5.0.4` |
| <img src="https://cdn.jsdelivr.net/gh/homarr-labs/dashboard-icons/svg/deluge.svg" width="28" height="28" alt=""> | [Deluge](./docs/pt-BR/deluge.md) | Baixa torrents | `2.2.0` |
| <img src="https://cdn.jsdelivr.net/gh/homarr-labs/dashboard-icons/svg/gluetun.svg" width="28" height="28" alt=""> | [Gluetun](./docs/pt-BR/gluetun.md) | **Opcional.** Túnel VPN para colocar o Deluge atrás | `latest` |
| <img src="https://cdn.jsdelivr.net/gh/homarr-labs/dashboard-icons/svg/dispatcharr.svg" width="28" height="28" alt=""> | [Dispatcharr](./docs/pt-BR/dispatcharr.md) | IPTV: canais, EPG e VOD, à parte da corrente acima | `latest` |
| <img src="https://cdn.jsdelivr.net/gh/homarr-labs/dashboard-icons/png/downtify.png" width="28" height="28" alt=""> | [Downtify](./docs/pt-BR/downtify.md) | Baixa músicas do Spotify na raiz de mídia | `2.9.1` |

Cada página acima diz o que o app precisa no primeiro uso e como ele se liga
aos outros. O Gluetun é a única peça opcional: o Deluge publica a porta dele e
funciona sem ele.

## Atualizar

```bash
qh media-stack --update --apply
```

Cada unit tem a própria tag — a tabela acima lista todas. Nada atualiza
sozinho; o comando acima aplica o que o repositório pinou.

## Backup

```bash
qh media-stack --backup --apply --out ~/backups
```

Ele para o serviço, empacota os dados, o `.env` e os secrets, e sobe de novo.
A frio de propósito: copiar banco vivo dá um arquivo que só falha na hora de
restaurar.

Pra restaurar, por cima dos dados atuais:

```bash
qh media-stack --restore ~/backups/media-stack-20260809-1200.tar.gz --apply
```

Ele pede que você digite `media-stack` pra confirmar, porque os dados atuais são
apagados antes de o arquivo ser extraído.

## Remover

```bash
qh media-stack --remove --apply           # para e tira, mantendo os dados
qh media-stack --remove --purge --apply   # e apaga volumes, secrets e .env
```

O `--purge` também pede o nome digitado. O nó da tailnet não é desregistrado
por isso — isso é no admin do Tailscale.

## Comandos

Não existe unit `media-stack` — aja sobre a peça que você quer:

```bash
systemctl --user status media-stack-jellyfin
podman logs -f jellyfin
qh media-stack-sonarr --update --apply   # uma unit da pasta
```

Com o Deluge atrás da VPN, a interface responde na porta do Gluetun e o log do
túnel é o `podman logs -f gluetun`.

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
