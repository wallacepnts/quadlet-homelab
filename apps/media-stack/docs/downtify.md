# Downtify

<img src="https://cdn.jsdelivr.net/gh/homarr-labs/dashboard-icons/png/downtify.png" width="64" height="64" alt="">

**[🇧🇷 Leia em português](./pt-BR/downtify.md)**

[< Media Stack](../README.md)

Paste a Spotify link and the music lands on disk.

Port **8000**, unit `media-stack-downtify`.

Writes straight into `/data/downloads`, the same folder the download clients use. It does not pass through Lidarr and nothing renames the result — it is the shortcut for one album, not a library.

That subdirectory has to exist before the first start, because it is bind-mounted on its own. The install creates it.

## Commands

```bash
systemctl --user status media-stack-downtify
podman logs -f downtify
qh media-stack-downtify --update --apply
```

## Credits

[Downtify](https://github.com/henriquesebastiao/downtify) — GPL-3.0

[Official documentation](https://github.com/henriquesebastiao/downtify#readme)
