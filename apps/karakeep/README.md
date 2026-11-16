# Karakeep

<img src="https://cdn.jsdelivr.net/gh/homarr-labs/dashboard-icons/svg/karakeep.svg" width="64" height="64" alt="">

**[🇧🇷 Leia em português](./README.pt-BR.md)**

A bookmark manager with full-text search and automatic archiving of every saved page's content.

## First run

Open `http://<host-ip>:8092` or `https://karakeep.<your-tailnet>.ts.net`.

## Files

```
karakeep-chrome.container
karakeep-meilisearch.container
karakeep.container
karakeep-net.network
.env.example
install.ini
```

Units in this stack:

- `karakeep-chrome`
- `karakeep-meilisearch`
- `karakeep`
- `karakeep-n`

## Remove

The tailnet node is not deregistered when an app is removed: do that in the Tailscale admin.

## Credits

[karakeep-app/karakeep](https://github.com/karakeep-app/karakeep) — AGPL-3.0.

[Official documentation](https://karakeep.app)
