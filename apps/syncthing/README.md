# Syncthing

<img src="https://cdn.jsdelivr.net/gh/homarr-labs/dashboard-icons/svg/syncthing.svg" width="64" height="64" alt="">

**[🇧🇷 Leia em português](./README.pt-BR.md)**

P2P file sync between devices, with no central server.

## First run

Open `http://<host-ip>:8384` or `https://syncthing.<your-tailnet>.ts.net`.

## Files

```
syncthing.container
.env.example
```

## Remove

The tailnet node is not deregistered when an app is removed: do that in the Tailscale admin.

## Credits

[syncthing/syncthing](https://github.com/syncthing/syncthing) — MPL-2.0.

[Official documentation](https://syncthing.net/)
