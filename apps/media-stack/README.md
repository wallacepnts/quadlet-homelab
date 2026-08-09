# Media Stack

**[🇧🇷 Leia em português](./README.pt-BR.md)**

Jellyfin plus the *arr chain and the downloaders — one folder, twelve units,
each on its own port. Gluetun is there for whoever wants Deluge behind a VPN;
nothing depends on it.

## Install

```bash
qh media-stack            # shows the plan
qh media-stack --apply
```

Each unit publishes its own port and its own tailnet name; the addresses are
printed at the end of the install.

<details>
<summary><b>Manual install</b></summary>

```bash
# 1. Download the units (no need to clone the repository; this includes
#    media-stack-gluetun.container — only used if you put Deluge behind the
#    VPN; left alone it costs nothing)
mkdir -p ~/.config/containers/systemd/media-stack
for f in jellyfin dispatcharr downtify prowlarr sonarr radarr lidarr \
         bazarr seerr deluge sabnzbd gluetun; do
  wget -P ~/.config/containers/systemd/media-stack/ \
    "https://raw.githubusercontent.com/wallacepnts/quadlet-homelab/main/apps/media-stack/media-stack-$f.container"
done

# 2. The media root — the ONLY path decision in this whole stack, through a
#    systemd environment variable (not an ordinary EnvironmentFile= — this
#    one has to exist in the *manager's* environment to be expanded inside
#    Volume=; see the details in the corresponding rule in the conventions).
mkdir -p ~/.config/environment.d
cat > ~/.config/environment.d/media-stack.conf <<EOF
MEDIA_DATA_DIR=$HOME/data
EOF
mkdir -p "$HOME/data"
# If the media already lives on another disk or mount, use the real path up
# there instead of $HOME/data — no symlinks, the variable already handles it.

# 3. Config directories — a bind mount requires them to exist before the start
mkdir -p ~/.config/containers/volumes/media-stack/jellyfin/{config,cache}
mkdir -p ~/.config/containers/volumes/media-stack/{prowlarr,sonarr,radarr,lidarr,bazarr,seerr,deluge,sabnzbd}/config
mkdir -p ~/.config/containers/volumes/media-stack/dispatcharr/data
mkdir -p ~/.config/containers/volumes/media-stack/downtify/data
# Downtify downloads into downloads/ (inside the media root), the same folder
# where Deluge saves completed torrents — unlike the rest (step 2 above
# already creates the root, but not downloads/, which Deluge only creates
# after its first use; Downtify bind-mounts that subdirectory directly, so it
# has to exist BEFORE the start and cannot wait).
mkdir -p "$HOME/data/downloads"

# 4. The shared env (LinuxServer.io) — download the example and set
#    PUID/PGID to the user running Podman (the same owner as MEDIA_DATA_DIR,
#    otherwise the apps cannot write to it)
mkdir -p ~/.config/containers/env
wget -O ~/.config/containers/env/media-stack.env \
  https://raw.githubusercontent.com/wallacepnts/quadlet-homelab/main/apps/media-stack/.env.example
sed -i "s/^PUID=.*/PUID=$(id -u)/;s/^PGID=.*/PGID=$(id -g)/" \
  ~/.config/containers/env/media-stack.env

# 5. Apply the new env.d (this needs a daemon-reload, not just restarting
#    the service — it is systemd --user that has to re-read the environment)
systemctl --user daemon-reload

# 6. Start them. No Requires= between these — each is independent, and
#    Dispatcharr is a single container with Postgres/Redis inside it.
#    Gluetun is left out: it does nothing until you configure a provider.
systemctl --user start media-stack-jellyfin media-stack-dispatcharr media-stack-downtify media-stack-prowlarr media-stack-sonarr media-stack-radarr media-stack-lidarr media-stack-bazarr media-stack-seerr media-stack-deluge media-stack-sabnzbd

```

</details>

## Files

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

The stack is a chain: **Seerr** takes the request, the ***arr** apps look the
title up through **Prowlarr**, hand the download to **SABnzbd** or **Deluge**,
rename the file into the media root, and **Jellyfin** plays it. Each piece runs
on its own and is useful without the rest.

| | Unit | What it does | Port | Version |
| --- | --- | --- | --- | --- |
| <img src="https://cdn.jsdelivr.net/gh/homarr-labs/dashboard-icons/svg/jellyfin.svg" width="28" height="28" alt=""> | `media-stack-jellyfin` | Plays the library — films, series, music — to a browser, a TV or a phone | 8096 | `10.11.11` |
| <img src="https://cdn.jsdelivr.net/gh/homarr-labs/dashboard-icons/svg/seerr.svg" width="28" height="28" alt=""> | `media-stack-seerr` | Where you ask for a title. Passes the request to Sonarr or Radarr | 5055 | `v3.4.1` |
| <img src="https://cdn.jsdelivr.net/gh/homarr-labs/dashboard-icons/svg/prowlarr.svg" width="28" height="28" alt=""> | `media-stack-prowlarr` | Holds the indexer list and feeds it to the other *arr apps, so you configure them once | 9696 | `2.5.2` |
| <img src="https://cdn.jsdelivr.net/gh/homarr-labs/dashboard-icons/svg/sonarr.svg" width="28" height="28" alt=""> | `media-stack-sonarr` | Series: watches for new episodes, downloads and files them | 8989 | `4.0.19` |
| <img src="https://cdn.jsdelivr.net/gh/homarr-labs/dashboard-icons/svg/radarr.svg" width="28" height="28" alt=""> | `media-stack-radarr` | The same, for films | 7878 | `6.3.0` |
| <img src="https://cdn.jsdelivr.net/gh/homarr-labs/dashboard-icons/svg/lidarr.svg" width="28" height="28" alt=""> | `media-stack-lidarr` | The same, for music | 8686 | `3.1.0` |
| <img src="https://cdn.jsdelivr.net/gh/homarr-labs/dashboard-icons/svg/bazarr.svg" width="28" height="28" alt=""> | `media-stack-bazarr` | Fetches subtitles for what Sonarr and Radarr brought in | 6767 | `1.6.0` |
| <img src="https://cdn.jsdelivr.net/gh/homarr-labs/dashboard-icons/svg/sabnzbd.svg" width="28" height="28" alt=""> | `media-stack-sabnzbd` | Downloads from Usenet | 8081 | `version-5.0.4` |
| <img src="https://cdn.jsdelivr.net/gh/homarr-labs/dashboard-icons/svg/deluge.svg" width="28" height="28" alt=""> | `media-stack-deluge` | Downloads torrents | 8112 | `2.2.0` |
| <img src="https://cdn.jsdelivr.net/gh/homarr-labs/dashboard-icons/svg/gluetun.svg" width="28" height="28" alt=""> | `media-stack-gluetun` | **Optional.** A VPN tunnel to put Deluge behind — off unless you set it up | — | `latest` |
| <img src="https://cdn.jsdelivr.net/gh/homarr-labs/dashboard-icons/svg/dispatcharr.svg" width="28" height="28" alt=""> | `media-stack-dispatcharr` | IPTV: channels, EPG and VOD, apart from the chain above | 9191 | `latest` |
| <img src="https://cdn.jsdelivr.net/gh/homarr-labs/dashboard-icons/png/downtify.png" width="28" height="28" alt=""> | `media-stack-downtify` | Downloads music from Spotify into the media root | 8000 | `2.9.1` |

Gluetun is the only optional piece. Deluge publishes its own port and works
without it; installing the folder brings Gluetun along, where it sits idle
until you configure a provider. Putting Deluge behind the VPN is a swap, not an
addition — the comments at the top of both units say which lines to move, and
the two cannot publish 8112 at the same time.

## Update

```bash
qh media-stack --update --apply
```

Each unit carries its own tag — the table above lists them. Nothing updates
on its own; the command above applies whatever the repository pins.

## Backup

```bash
qh media-stack --backup --apply --out ~/backups
```

It stops the service, packs the data, the `.env` and the secrets, and starts
it again. Cold on purpose: copying a live database gives an archive that only
fails when you restore it.

To restore, over the current data:

```bash
qh media-stack --restore ~/backups/media-stack-20260809-1200.tar.gz --apply
```

It asks you to type `media-stack` to confirm, because the current data is deleted
before the archive is unpacked.

## Remove

```bash
qh media-stack --remove --apply           # stops it, keeps the data
qh media-stack --remove --purge --apply   # and deletes volumes, secrets and .env
```

`--purge` asks for the typed name too. The tailnet node is not deregistered by
this — that is done in the Tailscale admin.

## Commands

There is no `media-stack` unit — act on the piece you mean:

```bash
systemctl --user status media-stack-jellyfin
podman logs -f jellyfin
qh media-stack-sonarr --update --apply   # one unit of the folder
```

With Deluge behind the VPN, the interface answers on Gluetun's port and the
tunnel's own log is `podman logs -f gluetun`.

## Credits

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

Most images come from [LinuxServer.io](https://www.linuxserver.io/).

[Official documentation](https://jellyfin.org)
