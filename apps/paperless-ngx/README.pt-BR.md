# Paperless-ngx

<img src="https://cdn.jsdelivr.net/gh/homarr-labs/dashboard-icons/svg/paperless-ngx.svg" width="64" height="64" alt="">

**[🇺🇸 Read in English](./README.md)**

Digitaliza, faz OCR e indexa documentos automaticamente, com busca full-text pra nunca mais procurar papel.

## Primeiro acesso

Abrir `http://<ip-do-host>:8091` ou `https://paperless.<your-tailnet>.ts.net`.

## Arquivos

```
paperless-ngx-broker.container
paperless-ngx-gotenberg.container
paperless-ngx-tika.container
paperless-ngx.container
paperless-ngx-net.network
.env.example
install.ini
```

Units da stack:

- `paperless-ngx-broker`
- `paperless-ngx-gotenberg`
- `paperless-ngx-tika`
- `paperless-ngx`
- `paperless-ngx-n`

## Remover

O nó da tailnet não é desregistrado ao remover um app: isso é no admin do Tailscale.

## Créditos

[paperless-ngx/paperless-ngx](https://github.com/paperless-ngx/paperless-ngx) — GPL-3.0.

[Documentação oficial](https://docs.paperless-ngx.com/)
