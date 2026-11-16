# Paperless-ngx

<img src="https://cdn.jsdelivr.net/gh/homarr-labs/dashboard-icons/svg/paperless-ngx.svg" width="64" height="64" alt="">

**[🇧🇷 Leia em português](./README.pt-BR.md)**

Scans, OCRs and indexes documents automatically, with full-text search so you never hunt for paper again.

## First run

Open `http://<host-ip>:8091` or `https://paperless.<your-tailnet>.ts.net`.

## Files

```
paperless-ngx-broker.container
paperless-ngx-gotenberg.container
paperless-ngx-tika.container
paperless-ngx.container
paperless-ngx-net.network
.env.example
install.ini
```

Units in this stack:

- `paperless-ngx-broker`
- `paperless-ngx-gotenberg`
- `paperless-ngx-tika`
- `paperless-ngx`
- `paperless-ngx-n`

## Remove

The tailnet node is not deregistered when an app is removed: do that in the Tailscale admin.

## Credits

[paperless-ngx/paperless-ngx](https://github.com/paperless-ngx/paperless-ngx) — GPL-3.0.

[Official documentation](https://docs.paperless-ngx.com/)
