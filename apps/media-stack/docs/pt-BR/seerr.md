# Seerr

<img src="https://cdn.jsdelivr.net/gh/homarr-labs/dashboard-icons/svg/seerr.svg" width="64" height="64" alt="">

**[🇺🇸 Read in English](../seerr.md)**

[< Media Stack](../../README.pt-BR.md)

Onde um título é pedido. Ele repassa o pedido ao Sonarr ou ao Radarr e avisa quando chega.

Porta **5055**, unit `media-stack-seerr`.

O assistente pede primeiro o Jellyfin (`http://jellyfin:8096`) e depois o Sonarr e o Radarr. Cada um deles quer a API key, que fica em Settings -> General do próprio app.

É a peça para dar a alguém que deve pedir sem mexer no resto. É a única do stack pensada para mais de uma pessoa.

## Comandos

```bash
systemctl --user status media-stack-seerr
podman logs -f seerr
qh media-stack-seerr --update --apply
```

## Créditos

[Seerr](https://github.com/seerr-team/seerr) — MIT

[Documentação oficial](https://docs.seerr.dev/)
