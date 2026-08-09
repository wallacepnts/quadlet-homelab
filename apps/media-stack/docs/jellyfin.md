# Jellyfin

<img src="https://cdn.jsdelivr.net/gh/homarr-labs/dashboard-icons/svg/jellyfin.svg" width="64" height="64" alt="">

**[🇧🇷 Leia em português](./pt-BR/jellyfin.md)**

[< Media Stack](../README.md)

Plays what the stack collected — films, series and music — in a browser, on a TV or on a phone.

Port **8096**, unit `media-stack-jellyfin`.

Open the port and run the wizard: create the administrator, then add one library per kind of content, pointing at the folders under `/data`.

The media root is mounted **read-only** here. Jellyfin plays and never writes, so a wrong click in the interface cannot delete the library — the *arr apps are what organise it.

## Commands

```bash
systemctl --user status media-stack-jellyfin
podman logs -f jellyfin
qh media-stack-jellyfin --update --apply
```

## Credits

[Jellyfin](https://github.com/jellyfin/jellyfin) — GPL-2.0

[Official documentation](https://jellyfin.org/docs/)
