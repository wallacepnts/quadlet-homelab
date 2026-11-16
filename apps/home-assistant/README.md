# Home Assistant

<img src="https://cdn.jsdelivr.net/gh/homarr-labs/dashboard-icons/svg/home-assistant.svg" width="64" height="64" alt="">

**[🇧🇷 Leia em português](./README.pt-BR.md)**

The central home automation hub; it brings devices from any manufacturer into a single panel.

## First run

Open `http://<host-ip>:8123` or `https://home-assistant.<your-tailnet>.ts.net`.

## Files

```
home-assistant.container
.env.example
install.ini
```

## Remove

The tailnet node is not deregistered when an app is removed: do that in the Tailscale admin.

## Credits

[home-assistant/core](https://github.com/home-assistant/core) — Apache-2.0

[Official documentation](https://www.home-assistant.io)
