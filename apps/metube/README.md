# MeTube — Podman Quadlet (rootless)

**[🇧🇷 Leia em português](./README.pt-BR.md)**

A [MeTube](https://github.com/alexta69/metube) (`yt-dlp` web interface)
deploy via Podman Quadlet, using the official `ghcr.io/alexta69/metube` image.

Paste the URL, pick a format and quality, and the file lands on disk. The
[media-stack](../media-stack/) handles films and TV through the \*arr apps;
this one is for the one-off video.

## Architecture

A single container, Python + `yt-dlp`. **No database**: the queue state
lives in `.metube/` inside the downloads volume itself.

### The hardening ladder inverted

Worth recording because it runs against intuition
([conventions, rule 20](../../docs/conventions.md)):
`DropCapability=ALL` **on its own is refused** —

```
chown: changing ownership of '/app/ui/dist/metube/3rdpartylicenses.txt':
Operation not permitted
```

— because the entrypoint adjusts ownership at start. But with **`User=1000`
the entrypoint has nothing to adjust** (the image's `PUID` is already 1000),
the `chown` disappears, and the strongest level passes. In other words: the
highest rung works and the middle one does not. The practical lesson is not to
give up at the first `chown` in the log — sometimes going up a rung fixes it
instead of granting the capability.

## Files

```
metube.container   # main unit
```

## Installation

```bash
python3 install.py metube            # dry-run: shows what it will do
python3 install.py metube --apply
```

For the local network only, `--access local`; on the tailnet and the LAN,
`--access both`. Adding `--href-local` points the dashboard link at the LAN.
The script creates the directories, writes the `.env`, generates the secrets,
fixes the volumes' ownership, starts the service and prints the address at the
end — see [Installing and operating](../../docs/installing.md).

Open `http://<host-ip>:8100` (or through [tsdproxy](../tsdproxy/) at
`https://metube.<your-tailnet>.ts.net`).

<details>
<summary><b>Manual installation</b> (advanced) — the same steps, one at a time</summary>


```bash
# 1. Download the unit (no need to clone the repository)
mkdir -p ~/.config/containers/systemd
wget -P ~/.config/containers/systemd/ \
  https://raw.githubusercontent.com/wallacepnts/quadlet-homelab/main/apps/metube/metube.container

# 2. Directory, with the owner matching the unit's User=1000
mkdir -p ~/.config/containers/volumes/metube/downloads
podman unshare chown -R 1000:1000 ~/.config/containers/volumes/metube

# 3. Start it
systemctl --user daemon-reload
systemctl --user start metube
```

Open `http://<host-ip>:8100` (ou via [tsdproxy](../tsdproxy/) em
`https://metube.<your-tailnet>.ts.net`).

</details>

## Security

**There is no authentication.** Whoever reaches the port downloads whatever
they like onto your disk. On the tailnet that is acceptable; do not expose it
beyond that. To put a login in front of it, the route is
[Authentik](../authentik/).

## Downloading into the media-stack

For [Jellyfin](../media-stack/) to see what MeTube downloads, the route is to
point the downloads volume inside the media-stack's shared data root instead
of its own directory — change the unit's `Volume=` line and redo the `chown`.
MeTube writes as uid 1000 (100999 on the host), so check that Jellyfin can
read it.

## Auto-update

No `AutoUpdate=` — an explicit tag, bumped by hand
([rule 9](../../docs/conventions.md)).
**The tag is the build date** (`2026.08.04`), not semver, hence the
`wud.tag.include=^[0-9]{4}.[0-9]{2}.[0-9]{2}$`.

One remark worth making: the embedded `yt-dlp` breaks whenever YouTube
changes, and the fix arrives in a new image. This is the service in this
repository with the strongest case for updating often.

## Backup & recovery

Nothing to do beyond copying the videos, if you want them: there is no
database and no configuration outside the downloads volume.

## Useful commands

```bash
systemctl --user status metube
podman logs -f metube
podman exec metube yt-dlp --version
```

## Credits

Quadlet deploy based on [MeTube](https://github.com/alexta69/metube)
de [alexta69](https://github.com/alexta69) (AGPL-3.0), que embrulha o
[yt-dlp](https://github.com/yt-dlp/yt-dlp).
