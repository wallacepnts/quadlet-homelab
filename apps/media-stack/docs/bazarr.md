# Bazarr

<img src="https://cdn.jsdelivr.net/gh/homarr-labs/dashboard-icons/svg/bazarr.svg" width="64" height="64" alt="">

**[🇧🇷 Leia em português](./pt-BR/bazarr.md)**

[< Media Stack](../README.md)

Fetches subtitles for what Sonarr and Radarr brought in.

Port **6767**, unit `media-stack-bazarr`.

Settings -> Sonarr and Settings -> Radarr, with the address (`http://sonarr:8989`) and the API key of each. Then Settings -> Languages, choose the languages, and Settings -> Providers, choose where to look.

It reads the library through the *arr apps, so it only sees what they know about. A file dropped into the folder by hand does not show up.

## Commands

```bash
systemctl --user status media-stack-bazarr
podman logs -f bazarr
qh media-stack-bazarr --update --apply
```

## Credits

[Bazarr](https://github.com/morpheus65535/bazarr) — GPL-3.0

[Official documentation](https://wiki.bazarr.media/)
