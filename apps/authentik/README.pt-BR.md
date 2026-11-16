# Authentik

<img src="https://cdn.jsdelivr.net/gh/homarr-labs/dashboard-icons/svg/authentik.svg" width="64" height="64" alt="">

**[🇺🇸 Read in English](./README.md)**

Servidor de identidade.

## Primeiro acesso

Abrir `http://<ip-do-host>:9000` ou `https://authentik.<your-tailnet>.ts.net`.

## Arquivos

```
authentik-postgres.container
authentik-worker.container
authentik.container
authentik-net.network
install.ini
```

Units da stack:

- `authentik-postgres`
- `authentik-worker`
- `authentik`
- `authentik-n`

## Remover

O nó da tailnet não é desregistrado ao remover um app: isso é no admin do Tailscale.

## Créditos

[goauthentik/authentik](https://github.com/goauthentik/authentik) — MIT

[Documentação oficial](https://goauthentik.io)
