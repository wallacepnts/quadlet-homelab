# ntfy

<img src="https://cdn.jsdelivr.net/gh/homarr-labs/dashboard-icons/svg/ntfy.svg" width="64" height="64" alt="">

**[🇧🇷 Leia em português](./README.pt-BR.md)**

A push notification server — where the uptime-kuma, wud and zerobyte alerts go, with a phone app.

## First run

Open `http://<host-ip>:2586` or `https://ntfy.<your-tailnet>.ts.net`.

## Files

```
ntfy.container
.env.example
```

## Remove

The tailnet node is not deregistered when an app is removed: do that in the Tailscale admin.

## Credits

[binwiederhier/ntfy](https://github.com/binwiederhier/ntfy) — Apache-2.0

[Official documentation](https://ntfy.sh)
