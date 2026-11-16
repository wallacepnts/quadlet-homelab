# WUD (What's Up Docker)

<img src="https://cdn.jsdelivr.net/gh/getwud/wud@main/ui/public/img/icons/android-chrome-512x512.png" width="64" height="64" alt="">

**[🇧🇷 Leia em português](./README.pt-BR.md)**

Watches for available image updates for the containers, applying nothing itself — it only reports.

## First run

Open `http://<host-ip>:8085` or `https://wud.<your-tailnet>.ts.net`.

## Files

```
wud.container
.env.example
install.ini
```

## Remove

The tailnet node is not deregistered when an app is removed: do that in the Tailscale admin.

## Credits

[getwud/wud](https://github.com/getwud/wud) — MIT

[Official documentation](https://getwud.github.io/wud/)
