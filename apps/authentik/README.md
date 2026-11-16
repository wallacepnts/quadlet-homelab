# Authentik

<img src="https://cdn.jsdelivr.net/gh/homarr-labs/dashboard-icons/svg/authentik.svg" width="64" height="64" alt="">

**[🇧🇷 Leia em português](./README.pt-BR.md)**

An identity server.

## First run

Open `http://<host-ip>:9000` or `https://authentik.<your-tailnet>.ts.net`.

## Files

```
authentik-postgres.container
authentik-worker.container
authentik.container
authentik-net.network
install.ini
```

Units in this stack:

- `authentik-postgres`
- `authentik-worker`
- `authentik`
- `authentik-n`

## Remove

The tailnet node is not deregistered when an app is removed: do that in the Tailscale admin.

## Credits

[goauthentik/authentik](https://github.com/goauthentik/authentik) — MIT

[Official documentation](https://goauthentik.io)
