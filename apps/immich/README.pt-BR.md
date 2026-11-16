# Immich

<img src="https://cdn.jsdelivr.net/gh/homarr-labs/dashboard-icons/svg/immich.svg" width="64" height="64" alt="">

**[🇺🇸 Read in English](./README.md)**

Backup e organização de fotos/vídeos, com reconhecimento facial e busca smart.

## Primeiro acesso

Abrir `http://<ip-do-host>:2283` ou `https://immich.<your-tailnet>.ts.net`.

## Arquivos

```
immich-machine-learning.container
immich-postgres.container
immich-redis.container
immich.container
immich-net.network
.env.example
install.ini
```

Units da stack:

- `immich-machine-learning`
- `immich-postgres`
- `immich-redis`
- `immich`
- `immich-n`

## Remover

O nó da tailnet não é desregistrado ao remover um app: isso é no admin do Tailscale.

## Créditos

[immich-app/immich](https://github.com/immich-app/immich) — AGPL-3.0.

[Documentação oficial](https://immich.app)
