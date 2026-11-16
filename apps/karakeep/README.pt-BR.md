# Karakeep

<img src="https://cdn.jsdelivr.net/gh/homarr-labs/dashboard-icons/svg/karakeep.svg" width="64" height="64" alt="">

**[🇺🇸 Read in English](./README.md)**

Gerenciador de bookmarks com busca full-text e arquivamento automático do conteúdo de cada página salva.

## Primeiro acesso

Abrir `http://<ip-do-host>:8092` ou `https://karakeep.<your-tailnet>.ts.net`.

## Arquivos

```
karakeep-chrome.container
karakeep-meilisearch.container
karakeep.container
karakeep-net.network
.env.example
install.ini
```

Units da stack:

- `karakeep-chrome`
- `karakeep-meilisearch`
- `karakeep`
- `karakeep-n`

## Remover

O nó da tailnet não é desregistrado ao remover um app: isso é no admin do Tailscale.

## Créditos

[karakeep-app/karakeep](https://github.com/karakeep-app/karakeep) — AGPL-3.0.

[Documentação oficial](https://karakeep.app)
