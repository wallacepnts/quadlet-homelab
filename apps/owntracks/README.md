# OwnTracks

<img src="https://cdn.jsdelivr.net/gh/homarr-labs/dashboard-icons/svg/owntracks.svg" width="64" height="64" alt="">

**[🇧🇷 Leia em português](./README.pt-BR.md)**

Personal location tracking through a phone app, with its own MQTT broker and a position history.

## First run

Open `http://<host-ip>:1883` or `https://owntracks-ui.<your-tailnet>.ts.net`.

## Files

```
owntracks-frontend.container
owntracks-mosquitto.container
owntracks-recorder.container
owntracks-net.network
.env.example
install.ini
```

Units in this stack:

- `owntracks-frontend`
- `owntracks-mosquitto`
- `owntracks-recorder`
- `owntracks-n`

## Remove

The tailnet node is not deregistered when an app is removed: do that in the Tailscale admin.

## Credits

[owntracks/recorder](https://github.com/owntracks/recorder) — GPL-2.0

[Official documentation](https://owntracks.org/booklet/)
