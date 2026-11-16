# Monica

<img src="https://cdn.jsdelivr.net/gh/homarr-labs/dashboard-icons/svg/monica.svg" width="64" height="64" alt="">

**[🇧🇷 Leia em português](./README.pt-BR.md)**

A personal CRM — relationship history, contacts, reminders.

## First run

Open `http://<host-ip>:9092` or `https://monica.<your-tailnet>.ts.net`.

## Files

```
monica.container
.env.example
install.ini
```

## Update

By digest, because `monica-next` publishes no versioned image — only `main` and
`main-fpm`, rebuilt as the branch moves. The digest freezes one build of it.

## Remove

The tailnet node is not deregistered when an app is removed: do that in the Tailscale admin.

## Credits

[monicahq/monica](https://github.com/monicahq/monica) — AGPL-3.0

[Official documentation](https://beta.monicahq.com)
