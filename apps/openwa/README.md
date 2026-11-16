# OpenWA

<img src="https://cdn.jsdelivr.net/gh/rmyndharis/OpenWA@main/docs/logo/openwa.svg" width="64" height="64" alt="">

**[🇧🇷 Leia em português](./README.pt-BR.md)**

A WhatsApp API gateway — turns the account into REST plus webhooks, for n8n and Home Assistant to use.

## First run

Open `http://<host-ip>:2785` or `https://openwa.<your-tailnet>.ts.net`.

## Files

```
openwa.container
.env.example
install.ini
```

## Behaviour change in 0.15.0

While WhatsApp Web reloads its own page — measured around five minutes after a
fresh pairing — every engine route answers `409` instead of the raw `500` it
used to. A client that retries on 5xx and gives up on 4xx will now fail where
it used to recover, so check the flows that call this API.

## Remove

The tailnet node is not deregistered when an app is removed: do that in the Tailscale admin.

## Credits

[rmyndharis/OpenWA](https://github.com/rmyndharis/OpenWA) — MIT

[Official documentation](https://www.open-wa.org)
