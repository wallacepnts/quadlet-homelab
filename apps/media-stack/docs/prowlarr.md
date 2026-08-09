# Prowlarr

<img src="https://cdn.jsdelivr.net/gh/homarr-labs/dashboard-icons/svg/prowlarr.svg" width="64" height="64" alt="">

**[🇧🇷 Leia em português](./pt-BR/prowlarr.md)**

[< Media Stack](../README.md)

Holds the indexer list in one place and pushes it to Sonarr, Radarr and Lidarr.

Port **9696**, unit `media-stack-prowlarr`.

Add the indexers here, then Settings -> Apps, one entry per *arr app with its address (`http://sonarr:8989`) and its API key. From then on an indexer added here appears in all of them.

Configure this one first. Doing the *arr apps before it means adding every indexer three times, and then again whenever one changes.

## Commands

```bash
systemctl --user status media-stack-prowlarr
podman logs -f prowlarr
qh media-stack-prowlarr --update --apply
```

## Credits

[Prowlarr](https://github.com/Prowlarr/Prowlarr) — GPL-3.0

[Official documentation](https://wiki.servarr.com/prowlarr)
