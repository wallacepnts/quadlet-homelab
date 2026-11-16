# Vaultwarden

<img src="https://cdn.jsdelivr.net/gh/homarr-labs/dashboard-icons/png/vaultwarden.png" width="64" height="64" alt="">

**[🇧🇷 Leia em português](./README.pt-BR.md)**

A password vault compatible with Bitwarden's protocol, light enough to run anywhere.

## First run

Open `https://vaultwarden.<your-tailnet>.ts.net`.

The vault is reachable over the tailnet only. `PublishPort=8082:80` ships
commented out in the unit: publishing it would also answer to anyone on the
LAN, which is a wider door than a password vault needs. Uncomment it if you
want `http://<host-ip>:8082` too.

## Files

```
vaultwarden.container
.env.example
install.ini
```

## Remove

The tailnet node is not deregistered when an app is removed: do that in the Tailscale admin.

## Credits

[dani-garcia/vaultwarden](https://github.com/dani-garcia/vaultwarden) — AGPL-3.0.

[Official documentation](https://github.com/dani-garcia/vaultwarden/wiki)
