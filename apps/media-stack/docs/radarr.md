# Radarr

<img src="https://cdn.jsdelivr.net/gh/homarr-labs/dashboard-icons/svg/radarr.svg" width="64" height="64" alt="">

**[🇧🇷 Leia em português](./pt-BR/radarr.md)**

[< Media Stack](../README.md)

The same as Sonarr, for films.

Port **7878**, unit `media-stack-radarr`.

Same setup: a root folder inside `/data` (`/data/media/movies`), a download client, and the indexers coming from Prowlarr.

Sonarr and Radarr are separate on purpose — a film and a series are named and organised by different rules.

## Commands

```bash
systemctl --user status media-stack-radarr
podman logs -f radarr
qh media-stack-radarr --update --apply
```

## Credits

[Radarr](https://github.com/Radarr/Radarr) — GPL-3.0

[Official documentation](https://wiki.servarr.com/radarr)
