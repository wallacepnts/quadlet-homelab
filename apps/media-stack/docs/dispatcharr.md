# Dispatcharr

<img src="https://cdn.jsdelivr.net/gh/homarr-labs/dashboard-icons/svg/dispatcharr.svg" width="64" height="64" alt="">

**[🇧🇷 Leia em português](./pt-BR/dispatcharr.md)**

[< Media Stack](../README.md)

IPTV: organises channel lists, the guide and video on demand.

Port **9191**, unit `media-stack-dispatcharr`.

Apart from the chain: it does not use Prowlarr, the *arr apps or the download clients, and it keeps its own data instead of writing to the media root.

Add the M3U list and the EPG source in the interface. It carries Postgres and Redis inside the same container, which is why it is one unit and not three.

## Commands

```bash
systemctl --user status media-stack-dispatcharr
podman logs -f dispatcharr
qh media-stack-dispatcharr --update --apply
```

## Credits

[Dispatcharr](https://github.com/Dispatcharr/Dispatcharr) — CC-BY-NC-SA-4.0

[Official documentation](https://dispatcharr.github.io/Dispatcharr-Docs/)
