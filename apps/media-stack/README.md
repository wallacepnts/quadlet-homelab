# Media Stack

<img src="https://api.iconify.design/mdi/multimedia.svg?color=%23888888" width="64" height="64" alt="">

**[🇧🇷 Leia em português](./README.pt-BR.md)**

Jellyfin plus the *arr chain and the downloaders — one folder, twelve units,
each on its own port. Gluetun is there for whoever wants Deluge behind a VPN;
nothing depends on it.

## First run

Each unit publishes its own port and its own tailnet name; the addresses are
printed at the end of the install.

## Files

```
media-stack-<app>.container       one unit per app, twelve of them
.env.example                      shared: PUID, PGID and TZ
media-stack-gluetun.env.example   the VPN provider, only if you use Gluetun
install.ini
docs/                             a page per app
```

Config in `~/.config/containers/volumes/media-stack/<app>/`, media under
`$MEDIA_DATA_DIR`. Each app's port is on its own page below.

The stack is a chain: **Seerr** takes the request, the ***arr** apps look the
title up through **Prowlarr**, hand the download to **SABnzbd** or **Deluge**,
rename the file into the media root, and **Jellyfin** or **Navidrome** plays it. Each piece runs
on its own and is useful without the rest.

| | App | What it does | Version |
| --- | --- | --- | --- |
| <img src="https://cdn.jsdelivr.net/gh/homarr-labs/dashboard-icons/svg/jellyfin.svg" width="28" height="28" alt=""> | [Jellyfin](./docs/jellyfin.md) | Plays the library — films, series, music — to a browser, a TV or a phone | `12.1` |
| <img src="https://cdn.jsdelivr.net/gh/homarr-labs/dashboard-icons/svg/navidrome.svg" width="28" height="28" alt=""> | [Navidrome](./docs/navidrome.md) | Plays the music the chain brought in, through any Subsonic client | `0.64.2` |
| <img src="https://cdn.jsdelivr.net/gh/homarr-labs/dashboard-icons/svg/seerr.svg" width="28" height="28" alt=""> | [Seerr](./docs/seerr.md) | Where you ask for a title. Passes the request to Sonarr or Radarr | `v3.5.0` |
| <img src="https://cdn.jsdelivr.net/gh/homarr-labs/dashboard-icons/svg/prowlarr.svg" width="28" height="28" alt=""> | [Prowlarr](./docs/prowlarr.md) | Holds the indexer list and feeds it to the other *arr apps | `2.6.5` |
| <img src="https://cdn.jsdelivr.net/gh/homarr-labs/dashboard-icons/svg/sonarr.svg" width="28" height="28" alt=""> | [Sonarr](./docs/sonarr.md) | Series: watches for new episodes, downloads and files them | `4.0.20` |
| <img src="https://cdn.jsdelivr.net/gh/homarr-labs/dashboard-icons/svg/radarr.svg" width="28" height="28" alt=""> | [Radarr](./docs/radarr.md) | The same, for films | `6.4.4` |
| <img src="https://cdn.jsdelivr.net/gh/homarr-labs/dashboard-icons/svg/lidarr.svg" width="28" height="28" alt=""> | [Lidarr](./docs/lidarr.md) | The same, for music | `3.1.0` |
| <img src="https://cdn.jsdelivr.net/gh/homarr-labs/dashboard-icons/svg/bazarr.svg" width="28" height="28" alt=""> | [Bazarr](./docs/bazarr.md) | Fetches subtitles for what Sonarr and Radarr brought in | `1.6.2` |
| <img src="https://cdn.jsdelivr.net/gh/homarr-labs/dashboard-icons/svg/sabnzbd.svg" width="28" height="28" alt=""> | [SABnzbd](./docs/sabnzbd.md) | Downloads from Usenet | `version-5.1.3` |
| <img src="https://cdn.jsdelivr.net/gh/homarr-labs/dashboard-icons/svg/deluge.svg" width="28" height="28" alt=""> | [Deluge](./docs/deluge.md) | Downloads torrents | `2.2.0` |
| <img src="https://cdn.jsdelivr.net/gh/homarr-labs/dashboard-icons/svg/gluetun.svg" width="28" height="28" alt=""> | [Gluetun](./docs/gluetun.md) | **Optional.** A VPN tunnel to put Deluge behind | `v3.41.3` |
| <img src="https://cdn.jsdelivr.net/gh/homarr-labs/dashboard-icons/svg/dispatcharr.svg" width="28" height="28" alt=""> | [Dispatcharr](./docs/dispatcharr.md) | IPTV: channels, EPG and VOD, apart from the chain above | `0.31.0` |
| <img src="https://cdn.jsdelivr.net/gh/homarr-labs/dashboard-icons/png/downtify.png" width="28" height="28" alt=""> | [Downtify](./docs/downtify.md) | Downloads music from Spotify into the media root | `3.4.0` |

Each page above says what its app needs on the first run and how it connects to
the others. Gluetun is the only optional piece: Deluge publishes its own port
and works without it.

## Update

Each unit carries its own tag — the table above lists them. Nothing updates
on its own; the command above applies whatever the repository pins.

## Remove

The tailnet node is not deregistered when an app is removed: do that in the Tailscale admin.

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
