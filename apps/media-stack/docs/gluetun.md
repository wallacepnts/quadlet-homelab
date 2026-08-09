# Gluetun

<img src="https://cdn.jsdelivr.net/gh/homarr-labs/dashboard-icons/svg/gluetun.svg" width="64" height="64" alt="">

**[🇧🇷 Leia em português](./pt-BR/gluetun.md)**

[< Media Stack](../README.md)

**Optional.** A VPN tunnel to put Deluge inside. Nothing in the stack depends on it.

Unit `media-stack-gluetun`.

Installed with the folder and idle until configured. Fill `~/.config/containers/env/media-stack-gluetun.env` with the provider, the key and the server — the file that ships is an example, and `WIREGUARD_ADDRESSES` has a placeholder that has to be replaced.

Then uncomment the ports and the labels in this unit and comment the matching ones in `media-stack-deluge.container`. Deluge stops having an interface of its own: it reuses this container's network stack, and the address on the host becomes Gluetun's.

It runs `--privileged` because it creates a network interface and rewrites the routing table. It is the only container in this repository that does.

## Commands

```bash
systemctl --user status media-stack-gluetun
podman logs -f gluetun
qh media-stack-gluetun --update --apply
```

## Credits

[Gluetun](https://github.com/qdm12/gluetun) — MIT

[Official documentation](https://github.com/qdm12/gluetun/wiki)
