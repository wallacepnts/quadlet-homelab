# Lidarr

<img src="https://cdn.jsdelivr.net/gh/homarr-labs/dashboard-icons/svg/lidarr.svg" width="64" height="64" alt="">

**[🇺🇸 Read in English](../lidarr.md)**

[< Media Stack](../../README.pt-BR.md)

O mesmo do Sonarr, para músicas: acompanha artistas e busca o que sai.

Porta **8686**, unit `media-stack-lidarr`.

Mesma configuração: uma root folder dentro de `/data` (`/data/media/music`), um cliente de download, e o Prowlarr para indexadores.

Para pegar um álbum ou uma faixa sem seguir um artista, o Downtify é o caminho mais curto.

## Comandos

```bash
systemctl --user status media-stack-lidarr
podman logs -f lidarr
qh media-stack-lidarr --update --apply
```

## Créditos

[Lidarr](https://github.com/Lidarr/Lidarr) — GPL-3.0

[Documentação oficial](https://wiki.servarr.com/lidarr)
