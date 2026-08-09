# Sonarr

<img src="https://cdn.jsdelivr.net/gh/homarr-labs/dashboard-icons/svg/sonarr.svg" width="64" height="64" alt="">

**[🇧🇷 Leia em português](./pt-BR/sonarr.md)**

[< Media Stack](../README.md)

Series: follows what you add, downloads new episodes and files them under the library.

Port **8989**, unit `media-stack-sonarr`.

Settings -> Media Management, add a root folder inside `/data` (for example `/data/media/tv`). Settings -> Download Clients, add SABnzbd (`sabnzbd:8080`) or Deluge (`deluge:8112`). The indexers arrive from Prowlarr.

Downloads land in `/data/downloads` and the library is under the same `/data`. That is the point of mounting the whole root once: filing a finished episode is a rename on the same filesystem, not a copy of several gigabytes.

## Commands

```bash
systemctl --user status media-stack-sonarr
podman logs -f sonarr
qh media-stack-sonarr --update --apply
```

## Credits

[Sonarr](https://github.com/Sonarr/Sonarr) — GPL-3.0

[Official documentation](https://wiki.servarr.com/sonarr)
