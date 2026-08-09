# Radarr

<img src="https://cdn.jsdelivr.net/gh/homarr-labs/dashboard-icons/svg/radarr.svg" width="64" height="64" alt="">

**[🇺🇸 Read in English](../radarr.md)**

[< Media Stack](../../README.pt-BR.md)

O mesmo do Sonarr, para filmes.

Porta **7878**, unit `media-stack-radarr`.

Mesma configuração: uma root folder dentro de `/data` (`/data/media/movies`), um cliente de download, e os indexadores vindos do Prowlarr.

Sonarr e Radarr são separados de propósito — filme e série são nomeados e organizados por regras diferentes.

## Comandos

```bash
systemctl --user status media-stack-radarr
podman logs -f radarr
qh media-stack-radarr --update --apply
```

## Créditos

[Radarr](https://github.com/Radarr/Radarr) — GPL-3.0

[Documentação oficial](https://wiki.servarr.com/radarr)
