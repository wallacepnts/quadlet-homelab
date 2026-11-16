# Immich

<img src="https://cdn.jsdelivr.net/gh/homarr-labs/dashboard-icons/svg/immich.svg" width="64" height="64" alt="">

**[🇧🇷 Leia em português](./README.pt-BR.md)**

Photo and video backup and organisation, with face recognition and smart search.

## First run

Open `http://<host-ip>:2283` or `https://immich.<your-tailnet>.ts.net`.

## Files

```
immich-machine-learning.container
immich-postgres.container
immich-redis.container
immich.container
immich-net.network
.env.example
install.ini
```

Units in this stack:

- `immich-machine-learning`
- `immich-postgres`
- `immich-redis`
- `immich`
- `immich-n`

## Remove

The tailnet node is not deregistered when an app is removed: do that in the Tailscale admin.

## Credits

[immich-app/immich](https://github.com/immich-app/immich) — AGPL-3.0.

[Official documentation](https://immich.app)
