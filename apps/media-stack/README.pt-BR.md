# Media Stack

**[🇺🇸 Read in English](./README.md)**

Jellyfin mais a cadeia *arr, os downloaders e um gateway de VPN — uma pasta,
doze units.

## Instalar
Jellyfin mais a cadeia *arr, os downloaders e um gateway de VPN — uma pasta, doze units.
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

# 6. Subir (sem o Gluetun — ver seção própria pra ativar VPN). Sem
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

Units da stack:

- `media-stack-bazarr`
- `media-stack-deluge`
- `media-stack-dispatcharr`
- `media-stack-downtify`
- `media-stack-gluetun`
- `media-stack-jellyfin`
- `media-stack-lidarr`
- `media-stack-prowlarr`
- `media-stack-radarr`
- `media-stack-sabnzbd`
- `media-stack-seerr`
- `media-stack-sonarr`

## Atualizar

```bash
qh media-stack --update --apply
```

Fixado em `1.6.0`, `10.11.11`, `2.2.0`. Nada atualiza sozinho — versão nova entra quando você
roda o comando acima.

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

```bash
systemctl --user status media-stack
podman logs -f media-stack
```

## Créditos

[jellyfin/jellyfin](https://github.com/jellyfin/jellyfin) — GPL-2.0

[Documentação oficial](https://jellyfin.org)
