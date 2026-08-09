# Seerr

<img src="https://cdn.jsdelivr.net/gh/homarr-labs/dashboard-icons/svg/seerr.svg" width="64" height="64" alt="">

**[🇧🇷 Leia em português](./pt-BR/seerr.md)**

[< Media Stack](../README.md)

Where a title is asked for. It hands the request to Sonarr or Radarr and reports back when it lands.

Port **5055**, unit `media-stack-seerr`.

The wizard asks for Jellyfin first (`http://jellyfin:8096`), then for Sonarr and Radarr. Each of those wants its API key, in Settings -> General of the app itself.

This is the piece to hand to someone who should ask for things without touching the rest. It is the only one in the stack meant for more than one person.

## Commands

```bash
systemctl --user status media-stack-seerr
podman logs -f seerr
qh media-stack-seerr --update --apply
```

## Credits

[Seerr](https://github.com/seerr-team/seerr) — MIT

[Official documentation](https://docs.seerr.dev/)
