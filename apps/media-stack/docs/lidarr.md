# Lidarr

<img src="https://cdn.jsdelivr.net/gh/homarr-labs/dashboard-icons/svg/lidarr.svg" width="64" height="64" alt="">

**[🇧🇷 Leia em português](./pt-BR/lidarr.md)**

[< Media Stack](../README.md)

The same as Sonarr, for music: follows artists and fetches what comes out.

Port **8686**, unit `media-stack-lidarr`.

Same setup: a root folder inside `/data` (`/data/media/music`), a download client, and Prowlarr for indexers.

For grabbing one album or one track without following an artist, Downtify is the shorter path.

## Commands

```bash
systemctl --user status media-stack-lidarr
podman logs -f lidarr
qh media-stack-lidarr --update --apply
```

## Credits

[Lidarr](https://github.com/Lidarr/Lidarr) — GPL-3.0

[Official documentation](https://wiki.servarr.com/lidarr)
