# Sonarr

<img src="https://cdn.jsdelivr.net/gh/homarr-labs/dashboard-icons/svg/sonarr.svg" width="64" height="64" alt="">

**[🇺🇸 Read in English](../sonarr.md)**

[< Media Stack](../../README.pt-BR.md)

Séries: acompanha o que você adiciona, baixa episódios novos e arquiva na biblioteca.

Porta **8989**, unit `media-stack-sonarr`.

Settings -> Media Management, acrescente uma root folder dentro de `/data` (por exemplo `/data/media/tv`). Settings -> Download Clients, acrescente o SABnzbd (`sabnzbd:8080`) ou o Deluge (`deluge:8112`). Os indexadores chegam pelo Prowlarr.

Os downloads caem em `/data/downloads` e a biblioteca fica dentro do mesmo `/data`. É por isso que a raiz inteira é montada de uma vez: arquivar um episódio pronto vira renomear no mesmo sistema de arquivos, não copiar vários gigabytes.

## Comandos

```bash
systemctl --user status media-stack-sonarr
podman logs -f sonarr
qh media-stack-sonarr --update --apply
```

## Créditos

[Sonarr](https://github.com/Sonarr/Sonarr) — GPL-3.0

[Documentação oficial](https://wiki.servarr.com/sonarr)
