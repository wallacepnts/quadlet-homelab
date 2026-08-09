# Prowlarr

<img src="https://cdn.jsdelivr.net/gh/homarr-labs/dashboard-icons/svg/prowlarr.svg" width="64" height="64" alt="">

**[🇺🇸 Read in English](../prowlarr.md)**

[< Media Stack](../../README.pt-BR.md)

Guarda a lista de indexadores num lugar só e envia para o Sonarr, o Radarr e o Lidarr.

Porta **9696**, unit `media-stack-prowlarr`.

Adicione os indexadores aqui e depois vá em Settings -> Apps, uma entrada por *arr com o endereço (`http://sonarr:8989`) e a API key. A partir daí, indexador acrescentado aqui aparece em todos.

Configure este primeiro. Fazer os *arr antes significa cadastrar cada indexador três vezes — e de novo toda vez que um mudar.

## Comandos

```bash
systemctl --user status media-stack-prowlarr
podman logs -f prowlarr
qh media-stack-prowlarr --update --apply
```

## Créditos

[Prowlarr](https://github.com/Prowlarr/Prowlarr) — GPL-3.0

[Documentação oficial](https://wiki.servarr.com/prowlarr)
