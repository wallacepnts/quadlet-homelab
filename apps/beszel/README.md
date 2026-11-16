# Beszel

<img src="https://cdn.jsdelivr.net/gh/homarr-labs/dashboard-icons/svg/beszel.svg" width="64" height="64" alt="">

**[🇧🇷 Leia em português](./README.pt-BR.md)**

A light dashboard for monitoring this host's resources (CPU/RAM/disk/network/containers).

## First run

Open `http://<host-ip>:8090` or `https://beszel.<your-tailnet>.ts.net`.

## Files

```
beszel-agent.container
beszel.container
beszel-net.network
.env.example
install.ini
```

Units in this stack:

- `beszel-agent`
- `beszel`
- `beszel-n`

## Remove

The tailnet node is not deregistered when an app is removed: do that in the Tailscale admin.

## Credits

[henrygd/beszel](https://github.com/henrygd/beszel) — MIT

[Official documentation](https://beszel.dev)
