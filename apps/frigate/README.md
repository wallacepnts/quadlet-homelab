# Frigate

<img src="https://cdn.jsdelivr.net/gh/selfhst/icons/svg/frigate.svg" width="64" height="64" alt="">

**[🇧🇷 Leia em português](./README.pt-BR.md)**

An NVR with AI object detection — CPU-only by default, no camera configured yet.

## First run

Open `http://<host-ip>:8971` or `https://frigate.<your-tailnet>.ts.net`.

## Files

```
frigate.container
install.ini         the default for FRIGATE_MEDIA_DIR, offered when it is unset
```

## Remove

The tailnet node is not deregistered when an app is removed: do that in the Tailscale admin.

## Credits

[blakeblackshear/frigate](https://github.com/blakeblackshear/frigate) — MIT

[Official documentation](https://frigate.video)
