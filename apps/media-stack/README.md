# Media Stack — Podman Quadlet (rootless)

**[🇧🇷 Leia em português](./README.pt-BR.md)**

A [Jellyfin](https://jellyfin.org) + [Dispatcharr](https://dispatcharr.github.io/Dispatcharr-Docs/)
+ [Downtify](https://github.com/henriquesebastiao/downtify) + nine
[LinuxServer.io](https://docs.linuxserver.io/)/[Seerr](https://docs.seerr.dev)
services deploy via Podman Quadlet, all seeing the same media/downloads root.

| Logo | Application | Version | Description | Port |
| --- | --- | --- | --- | --- |
| <img src="https://cdn.jsdelivr.net/gh/homarr-labs/dashboard-icons/svg/jellyfin.svg" width="48" height="48" alt=""> | [Jellyfin](https://jellyfin.org) | `10.11.11` | Organises and streams films, TV and music to any device on the network | `8096` |
| <img src="https://cdn.jsdelivr.net/gh/homarr-labs/dashboard-icons/svg/dispatcharr.svg" width="48" height="48" alt=""> | [Dispatcharr](https://dispatcharr.github.io/Dispatcharr-Docs/) | `latest` | Manages IPTV streams, the programme guide (EPG) and VOD, with a built-in proxy and transcoding | `9191` |
| <img src="https://cdn.jsdelivr.net/gh/homarr-labs/dashboard-icons/png/downtify.png" width="48" height="48" alt=""> | [Downtify](https://github.com/henriquesebastiao/downtify) | `2.9.1` | Downloads Spotify songs and playlists as real audio, with full metadata and cover art | `8000` |
| <img src="https://cdn.jsdelivr.net/gh/homarr-labs/dashboard-icons/svg/prowlarr.svg" width="48" height="48" alt=""> | [Prowlarr](https://prowlarr.com) | `2.5.2` | Manages the torrent/usenet indexers and distributes them to Sonarr, Radarr and Lidarr automatically | `9696` |
| <img src="https://cdn.jsdelivr.net/gh/homarr-labs/dashboard-icons/svg/sonarr.svg" width="48" height="48" alt=""> | [Sonarr](https://sonarr.tv) | `4.0.19` | Downloads and organises TV episodes automatically as soon as they are released | `8989` |
| <img src="https://cdn.jsdelivr.net/gh/homarr-labs/dashboard-icons/svg/radarr.svg" width="48" height="48" alt=""> | [Radarr](https://radarr.video) | `6.3.0` | Downloads and organises films automatically from a watchlist | `7878` |
| <img src="https://cdn.jsdelivr.net/gh/homarr-labs/dashboard-icons/svg/lidarr.svg" width="48" height="48" alt=""> | [Lidarr](https://lidarr.audio) | `3.1.0` | Downloads and organises music albums automatically by artist | `8686` |
| <img src="https://cdn.jsdelivr.net/gh/homarr-labs/dashboard-icons/svg/bazarr.svg" width="48" height="48" alt=""> | [Bazarr](https://www.bazarr.media) | `1.6.0` | Finds and downloads subtitles automatically for Sonarr's and Radarr's episodes and films | `6767` |
| <img src="https://cdn.jsdelivr.net/gh/homarr-labs/dashboard-icons/svg/seerr.svg" width="48" height="48" alt=""> | [Seerr](https://docs.seerr.dev) | `v3.4.1` | A film/TV request interface for other users; it triggers the automatic download through Sonarr/Radarr | `5055` |
| <img src="https://cdn.jsdelivr.net/gh/homarr-labs/dashboard-icons/svg/deluge.svg" width="48" height="48" alt=""> | [Deluge](https://deluge-torrent.org) | `2.2.0` | A light torrent client, with a web interface | `8112` |
| <img src="https://cdn.jsdelivr.net/gh/homarr-labs/dashboard-icons/svg/sabnzbd.svg" width="48" height="48" alt=""> | [SABnzbd](https://sabnzbd.org) | `version-5.0.4` | A usenet client; it downloads and organises binary posts automatically | `8081` (`8080` already belongs to [tsdproxy](../tsdproxy/) in this repo) |

A twelfth service, [Gluetun](https://github.com/qdm12/gluetun) (a VPN tunnel
for Deluge), is **optional** — see the dedicated section below.

**About Seerr**: it is the unified continuation of Overseerr (Plex only,
archived in 2024) and Jellyseerr (a community fork for Jellyfin/Emby) — the
two teams merged into this new project, which supports Plex/Jellyfin/Emby in
the same codebase. Since we use Jellyfin here, Seerr is the right choice for a
new installation — neither Overseerr nor Jellyseerr would make sense today.

## Why a single media root, shared by everyone

Sonarr/Radarr/Lidarr **move** a file from `downloads/` into `media/` when they
finish importing — if `downloads/` and `media/` are on different
filesystems/mounts (one path for Deluge, another for Sonarr, another for
Jellyfin), that "move" becomes a copy plus a delete: slower, wasting I/O and
disk space, and there is a window where the file is no longer in `downloads/`
and has not finished appearing in `media/`. With every service mounting the
**same** root as `/data`, that same move is instantaneous (a hardlink or an
atomic rename, on the same filesystem).

The folder structure inside the chosen root (create it after the first start,
through each app's UI or by hand):

```
<sua raiz>/
├── media/
│   ├── movies/
│   ├── tv/
│   └── music/
└── downloads/
    ├── torrents/   # Deluge's category/destination folder
    └── usenet/      # SABnzbd's destination folder
```

**A single path, decided once, applying to all ten** — through a
`MEDIA_DATA_DIR` variable (not a fixed path like `%h/data`; see Installation
for how that is resolved). If your media already lives on another disk or
mount, point the variable straight at it, with no symlink and no copy.

## Architecture

The default bridge network, each service with its own `PublishPort=`. No
dedicated `.network` — they talk to each other over HTTP configured by hand
after starting, not through a shared Podman network.

**Dispatcharr runs in AIO mode** (`DISPATCHARR_ENV=aio`) — a single container
with no database or network of its own: Postgres and Redis run *inside* it
(the image starts `pg_ctl`/Redis internally), all in a single `/data`. Unlike
the modular mode (Postgres/Redis/Celery in separate containers, like
any-sync-bundle) used here originally — switched at the user's request once
the upstream image gained a single `entrypoint.sh` covering both modes. See
the dedicated section below.

Two different mechanisms for mapping file permissions, depending on the image
— see [the conventions' rule on UserNS vs PUID/PGID](../../docs/conventions.md)
for why the two do not mix:

- **LinuxServer.io** (Prowlarr/Sonarr/Radarr/Lidarr/Bazarr/Deluge/SABnzbd):
  `PUID`/`PGID`/`TZ` in a single env file (`media-stack.env`), reused by all of
  them — the image does a `usermod` internally and requires running as real
  root inside the container's own namespace.
- **Jellyfin and Seerr** (not LinuxServer.io — Jellyfin executes the binary
  directly, Seerr runs fixed as uid 1000/"node", and neither has that internal
  usermod mechanism): `UserNS=keep-id`, which maps the container to the same
  uid as the user running Podman. The shared env file's `PUID`/`PGID` are
  ignored by them when present (harmless, but they do nothing).

`Prowlarr` and `Seerr` do not mount `/data` — Prowlarr only manages indexers
and talks to the others over an API, and Seerr only makes requests (talking to
Sonarr/Radarr/Jellyfin over their APIs, never touching a media file).

**Jellyfin on a bridge network, not `host`** — the same logic already applied
to [Home Assistant](../home-assistant/): it loses client autodiscovery on the
LAN (port `7359/udp`, broadcast — which does not cross a bridge/NAT properly),
but keeps this repository's default network isolation. Without autodiscovery,
the Jellyfin clients (TV apps, mobile and so on) ask for the server's address
by hand on first setup — it works normally, it just does not appear in the
list on its own.

## Files

```
media-stack-jellyfin.container
media-stack-dispatcharr.container   # AIO mode — internal Postgres/Redis, a single container
media-stack-downtify.container
media-stack-prowlarr.container
media-stack-sonarr.container
media-stack-radarr.container
media-stack-lidarr.container
media-stack-bazarr.container
media-stack-seerr.container
media-stack-deluge.container
media-stack-sabnzbd.container
media-stack-gluetun.container        # optional — see the VPN section below
```

## Prerequisites

- Rootless Podman with systemd `--user` working

## Installation

```bash
python3 install.py media-stack            # dry-run: shows what it will do
python3 install.py media-stack --apply
```

For the local network only, `--access local`; on the tailnet and the LAN,
`--access both`. Adding `--href-local` points the dashboard link at the LAN.
The script creates the directories, writes the `.env`, generates the secrets,
fixes the volumes' ownership, starts the service and prints the address at the
end — see [Installing and operating](../../docs/installing.md).

Reach each of them through [tsdproxy](../tsdproxy/) (tailnet, e.g.
`https://sonarr.<your-tailnet>.ts.net`) or locally
(`http://localhost:<port>`, see the table above).

<details>
<summary><b>Manual installation</b> (advanced) — the same steps, one at a time</summary>


```bash
# 1. Download the units (no need to clone the repository; this includes
#    media-stack-gluetun.container — it only matters if you use the VPN
#    section below; left unactivated it just sits there at no cost)
mkdir -p ~/.config/containers/systemd/media-stack
for f in jellyfin dispatcharr downtify prowlarr sonarr radarr lidarr \
         bazarr seerr deluge sabnzbd gluetun; do
  wget -P ~/.config/containers/systemd/media-stack/ \
    "https://raw.githubusercontent.com/wallacepnts/quadlet-homelab/main/apps/media-stack/media-stack-$f.container"
done

# 2. The media root — the ONLY path decision in this whole stack, through a
#    systemd environment variable (not an ordinary EnvironmentFile= — this
#    one has to exist in the *manager's* environment to be expanded inside
#    Volume=; see the details in the corresponding rule in the conventions).
mkdir -p ~/.config/environment.d
cat > ~/.config/environment.d/media-stack.conf <<EOF
MEDIA_DATA_DIR=$HOME/data
EOF
mkdir -p "$HOME/data"
# If the media already lives on another disk or mount, use the real path up
# there instead of $HOME/data — no symlinks, the variable already handles it.

# 3. Config directories — a bind mount requires them to exist before the start
mkdir -p ~/.config/containers/volumes/media-stack/jellyfin/{config,cache}
mkdir -p ~/.config/containers/volumes/media-stack/{prowlarr,sonarr,radarr,lidarr,bazarr,seerr,deluge,sabnzbd}/config
mkdir -p ~/.config/containers/volumes/media-stack/dispatcharr/data
mkdir -p ~/.config/containers/volumes/media-stack/downtify/data
# Downtify downloads into downloads/ (inside the media root), the same folder
# where Deluge saves completed torrents — unlike the rest (step 2 above
# already creates the root, but not downloads/, which Deluge only creates
# after its first use; Downtify bind-mounts that subdirectory directly, so it
# has to exist BEFORE the start and cannot wait).
mkdir -p "$HOME/data/downloads"

# 4. The shared env (LinuxServer.io) — download the example and set
#    PUID/PGID to the user running Podman (the same owner as MEDIA_DATA_DIR,
#    otherwise the apps cannot write to it)
mkdir -p ~/.config/containers/env
wget -O ~/.config/containers/env/media-stack.env \
  https://raw.githubusercontent.com/wallacepnts/quadlet-homelab/main/apps/media-stack/.env.example
sed -i "s/^PUID=.*/PUID=$(id -u)/;s/^PGID=.*/PGID=$(id -g)/" \
  ~/.config/containers/env/media-stack.env

# 5. Apply the new env.d (this needs a daemon-reload, not just restarting
#    the service — it is systemd --user that has to re-read the environment)
systemctl --user daemon-reload

# 6. Start them (without Gluetun — see the dedicated section to enable the
#    VPN). No Requires= between services here — Dispatcharr is a single
#    container, with Postgres/Redis coming up inside it.
systemctl --user start media-stack-jellyfin media-stack-dispatcharr media-stack-downtify media-stack-prowlarr media-stack-sonarr media-stack-radarr media-stack-lidarr media-stack-bazarr media-stack-seerr media-stack-deluge media-stack-sabnzbd

```

Reach each of them through [tsdproxy](../tsdproxy/) (tailnet, e.g.
`https://sonarr.<your-tailnet>.ts.net`) or locally
(`http://localhost:<port>`, see the table above).

</details>

## Wiring the services to each other (after the first access)

None of them discovers the others by itself — manual configuration, once,
through each one's UI:

1. **Jellyfin** — the initial wizard (language, admin account, adding a
   library pointing at the path mounted at `/data`, e.g. `/data/media/movies`,
   `/data/media/tv`). Do this **before** Seerr (step 7), which depends on
   Jellyfin already having at least one library configured. See the hardware
   transcoding section below if you will enable it.
2. **Deluge**: the initial password is `deluge` — change it in Preferences →
   Interface → Password as soon as you log in. Download folder:
   `/data/downloads/torrents`.
3. **SABnzbd**: the initial wizard asks for the usenet provider (server,
   username, password). Completed download folder: `/data/downloads/usenet`.
   Reached through tsdproxy, it gives `External internet access denied` —
   SABnzbd blocks by default any access that does not look like it came from
   the local network, and tsdproxy's traffic arrives through Podman's internal
   gateway (`169.254.1.2`, the same address behind
   `host.containers.internal` — see [zerobyte](../zerobyte/)), which does not
   match. Fix it by raising `inet_exposure` — through the UI (Config → General
   → "External internet access", to `Full web interface`, or "- Only external
   access requires login" if you want a password required only from outside)
   or directly in the file, without opening a browser (neither an environment
   variable nor a command-line argument works here — tested in practice:
   `Exec=--inet_exposure 4` in the `.container` breaks startup, because this
   image's init script does not pass extra arguments through to `sabnzbd.py`
   and tries to execute `--inet_exposure` as if it were a program):

   ```bash
   systemctl --user stop media-stack-sabnzbd

   podman unshare sed -i 's/^inet_exposure = 0/inet_exposure = 4/' \
     ~/.config/containers/volumes/media-stack/sabnzbd/config/sabnzbd.ini
   systemctl --user start media-stack-sabnzbd

   ```

   This is different from "Hostname verification failed" (another SABnzbd
   mechanism, based on `host_whitelist` by name, not IP) — this one is
   `inet_exposure`.
4. **Sonarr/Radarr/Lidarr** — in each, Settings → Download Clients → add
   Deluge (`localhost:8112`) and/or SABnzbd (`localhost:8081`; note the
   container's internal port is still 8080, but Sonarr/Radarr run on the host
   and so use the published `8081`). Settings → Media Management → Root
   Folder: `/data/media/tv` (Sonarr), `/data/media/movies` (Radarr),
   `/data/media/music` (Lidarr).
5. **Prowlarr** — Settings → Apps → add Sonarr/Radarr/Lidarr (each asks for
   their API key, under Settings → General in each app). Then Indexers → add
   the trackers/indexers you want — Prowlarr pushes them to every connected
   app by itself.
6. **Bazarr** — Settings → Sonarr/Radarr, the same logic (a local URL plus an
   API key), so it sees the same library and knows where to write subtitles.
7. **Seerr** — the initial wizard asks for a login: with a Jellyfin account
   (`localhost:8096`) or a local one. Then Settings → Services → add Sonarr
   (`localhost:8989`) and Radarr (`localhost:7878`) with their API keys —
   that is how an approved request in Seerr becomes an automatic search in
   Sonarr/Radarr.
8. **Dispatcharr** — the initial wizard asks for an admin account. Then
   Settings → M3U/EPG → add your IPTV playlists (M3U) and EPG sources (XMLTV)
   — that is what it builds the channel guide and the stream proxy from. It
   has no affinity with the rest of the stack (it does not talk to
   Sonarr/Radarr/Jellyfin over an API) — it works in isolation.

## Hardware transcoding (Jellyfin)

Without it, transcoding uses the CPU alone — it works, but it does not scale
well to several simultaneous streams or to 4K. Add this to
`media-stack-jellyfin.container` **before** starting (or edit it and run
`systemctl --user daemon-reload && systemctl --user restart
media-stack-jellyfin` afterwards):


### Intel/AMD (`/dev/dri`, VAAPI/QSV)

```ini
AddDevice=/dev/dri:/dev/dri
```

On a host with SELinux enforcing, this may also be needed:

```bash
sudo setsebool -P container_use_dri_devices 1
```

Then, under Dashboard → Playback, select VAAPI (AMD) or QSV (Intel) as the
hardware acceleration.

### NVIDIA (NVENC/NVDEC) — more work

This needs the
[NVIDIA Container Toolkit](https://docs.nvidia.com/datacenter/cloud-native/container-toolkit/latest/install-guide.html)
installed on the host first (a working NVIDIA driver is an implicit
prerequisite). Then generate the CDI spec — under rootless, in the user's own
namespace:

```bash
mkdir -p ~/.config/cdi
nvidia-ctk cdi generate --output=$HOME/.config/cdi/nvidia.yaml
```

On a host with SELinux enforcing:

```bash
sudo setsebool -P container_use_devices 1
```

Add this to `media-stack-jellyfin.container`:

```ini
AddDevice=nvidia.com/gpu=all
```

Then, under Dashboard → Playback, select NVIDIA NVENC. From NVIDIA Container
Toolkit v1.18.0 onwards there is an `nvidia-cdi-refresh` service that keeps
the CDI spec up to date by itself (an updated driver, a swapped GPU and so on)
— without it, redo the `nvidia-ctk cdi generate` by hand after any driver
change.

## Dispatcharr: AIO mode, with embedded Postgres and Redis

`media-stack-dispatcharr.container` runs in AIO mode
(`Environment=DISPATCHARR_ENV=aio`) — the image starts Postgres and Redis
internally (via `pg_ctl`/uwsgi attach-daemon in `entrypoint.sh`), all inside a
single `/data:Z` (the database in `/data/db`, the Django key in `/data/jwt`,
config and recordings in the rest). Unlike the "modular" mode (external
Postgres/Redis in separate containers) this repository used originally —
switched at the user's request once the upstream image gained a single
`entrypoint.sh` covering both modes, which made AIO viable without giving
anything up.

**No secret**: AIO mode uses a fixed password (`secret`) for the internal
Postgres, which is only reachable over a Unix socket *inside* the container
itself — never exposed on the network, so there is no real secret to manage
here (unlike the modular mode, which exposed Postgres on a shared Podman
network and therefore needed a real password).

**The first boot is slower** than the other services in this stack: the
embedded Postgres's `initdb` plus the Django schema migration plus Redis plus
Celery plus nginx plus uwsgi, all in sequence — tested in practice, within the
`TimeoutStartSec=300` margin already used here.

## Downtify: it downloads into Deluge's folder

`downtify` mounts `${MEDIA_DATA_DIR}/downloads:/downloads:Z` — the same
`downloads/` where Deluge (`torrents/`) and SABnzbd (`usenet/`) also write,
rather than a directory isolated to itself (an explicit decision, not the
original project's default). Since the mount is the whole `downloads/` folder,
Downtify's files sit loose at its root, alongside the other two's `torrents/`
and `usenet/` subfolders. It needs `MEDIA_DATA_DIR` set in
`~/.config/environment.d/` before the start, like the rest of the stack (see
Installation above) — without it the `Volume=` does not expand and the start
fails.

There are no API credentials to configure: the pipeline (scraping Spotify plus
searching YouTube Music) is self-contained and depends on nothing else in the
stack (Prowlarr, indexers and so on).

`DNS=1.1.1.1`/`DNS=1.0.0.1` in the `.container` — a recommendation from the
project itself (the official `docker-compose.yml` already ships it that way),
since reliably resolving `open.spotify.com`/`music.youtube.com` is critical for
the pipeline to work.

## An optional VPN for Deluge, via Gluetun

By default Deluge comes up **without a VPN** — torrent traffic goes out
straight through the host's IP, on the same network as the other services.
`media-stack-gluetun.container` ships alongside in the repository, stopped
until it is activated; activating it later requires no reinstallation.

**If you do activate it**, the recommended pattern is routing Deluge alone
(not the rest — Sonarr/Radarr/Lidarr/Prowlarr/Bazarr do no P2P and need no
VPN; SABnzbd is left out on purpose too, since usenet is a direct, encrypted
connection to the provider, with no IP broadcast to peers as in torrenting):

`media-stack-gluetun.container` already comes ready for that (Deluge's ports
published on it, a healthcheck, `--privileged` — see the justification below).
All that is left:

```bash
# 1. The VPN provider's credentials — download the example and edit it (see
#    the list of supported providers:
#    https://github.com/qdm12/gluetun-wiki/tree/main/setup/providers)
wget -O ~/.config/containers/env/media-stack-gluetun.env \
  https://raw.githubusercontent.com/wallacepnts/quadlet-homelab/main/apps/media-stack/media-stack-gluetun.env.example
# edit ~/.config/containers/env/media-stack-gluetun.env: VPN_SERVICE_PROVIDER,
# WIREGUARD_PRIVATE_KEY, WIREGUARD_ADDRESSES, SERVER_COUNTRIES
chmod 600 ~/.config/containers/env/media-stack-gluetun.env

# 2. Edit media-stack-deluge.container: replace the three PublishPort= lines
#    with Network=container:gluetun, and add to [Unit]:
#      After=media-stack-gluetun.service
#      Requires=media-stack-gluetun.service
#    (a container joining via "container:" declares no PublishPort= of its
#    own and no Network=<name>.network — the port is already published on
#    media-stack-gluetun.container, which is also why the discovery
#    tsdproxy.* labels live there rather than in
#    media-stack-deluge.container)

systemctl --user daemon-reload
systemctl --user stop media-stack-deluge

systemctl --user start media-stack-gluetun media-stack-deluge

```

`Network=container:gluetun` makes Deluge share Gluetun's entire network
stack — all of its traffic (torrents and its own web panel) goes out through
the tunnel. The practical consequence: **if Gluetun goes down, Deluge goes
with it** (it has no network of its own to fall back to) — which in practice
already works as a kill switch: no VPN, no Deluge, no IP leak.

**Why `PodmanArgs=--privileged` on Gluetun** (already the case in this repo's
`media-stack-gluetun.container`) — tested in practice: `AddCapability=NET_ADMIN`
alone (without privileged) blocks on the setup of Gluetun's own internal
firewall, with an `iptables`/`conntrack` error — rootless cannot touch the
host's real netfilter even with the capability granted, only what is inside
its own remapped namespace. With `--privileged` (still confined to the
rootless user namespace — it is **not** real host root, unlike rootful
Podman/Docker) the internal firewall comes up fine. If you would rather not
use `--privileged` at all, Gluetun's internal firewall can be turned off
(`FIREWALL=off` in `media-stack-gluetun.env`) — it works without
`--privileged`, but it loses Gluetun's own kill switch (the "de facto kill
switch" of `Network=container:` described above still remains, so the residual
risk is smaller than it looks).

Check that the outgoing IP is the VPN's, not the host's:
```bash
podman exec gluetun wget -qO- https://ipinfo.io/ip
```

## Auto-update

None of the services has `AutoUpdate=` — explicit tags, bumped by hand
([rule 9](../../docs/conventions.md); this repo's
`media-stack-gluetun.container` and `media-stack-dispatcharr.container` are a
deliberate exception and sit on `:latest`, because the respective projects do
not publish versioned releases in a stable way — to be revisited if that
changes). Jellyfin, the LinuxServer.io apps and Seerr keep a database (SQLite,
mostly) with library, history and download-client state under `/config` — the
same caution as [gitea](../gitea/): a healthcheck only confirms the HTTP
server answers, not that a schema migration ran correctly during a version
change.

**Dispatcharr is this repository's only case with real WUD visibility despite
having no semver tag:**

```ini
Label=wud.watch=true
Label=wud.watch.digest=true
```

With no versioned tag to compare, WUD would normally have no signal at all
(see [wud](../wud/)'s README, the "Non-semver tags are not watched" section) —
`wud.watch.digest` works around that by comparing the digest of the image
published as `:latest` against what is running. Since Dispatcharr's embedded
Postgres holds real data (channels, EPG, DVR) and the project is still in
active development, updating stays manual even with that visibility:

```bash
systemctl --user stop media-stack-dispatcharr

podman pull ghcr.io/dispatcharr/dispatcharr:latest
systemctl --user start media-stack-dispatcharr

```

**Take a backup before updating** (the section below) — in AIO mode, a failed
schema migration affects the only container there is, without the safety net
of isolated containers the modular mode had.

## Backup & recovery

```bash
systemctl --user stop media-stack-jellyfin media-stack-dispatcharr media-stack-downtify media-stack-prowlarr media-stack-sonarr media-stack-radarr media-stack-lidarr media-stack-bazarr media-stack-seerr media-stack-deluge media-stack-sabnzbd

tar -czf media-stack-backup-$(date +%Y%m%d-%H%M%S).tar.gz \
  -C ~/.config/containers/volumes media-stack
systemctl --user start media-stack-jellyfin media-stack-dispatcharr media-stack-downtify media-stack-prowlarr media-stack-sonarr media-stack-radarr media-stack-lidarr media-stack-bazarr media-stack-seerr media-stack-deluge media-stack-sabnzbd

```

Only each service's `config/` and `cache/` folders (API keys, configuration,
download/indexer state, Jellyfin's library and history) — the media itself and
the raw downloads stay out, outside `~/.config/containers/volumes/`, managed
separately by whoever installed them. If you use Gluetun,
`~/.config/containers/env/media-stack-gluetun.env` (the VPN credentials) needs
a separate backup too — without it, the only option is recreating it from
scratch with the provider.

On Dispatcharr (AIO mode), `volumes/media-stack/dispatcharr/data` holds
everything — the database (`data/db`: channels, playlists, EPG, users), the
Django key (`data/jwt`) and the rest (cached logos, DVR recordings). A cold
`tar` works (a file-level backup of the embedded Postgres, valid because
everything stops together), but to restore onto another instance — a
migration, an incompatible Postgres version — `pg_dump`/`pg_restore` is more
reliable than copying `data/db` raw:

```bash
podman exec dispatcharr su - dispatch -c \
  "pg_dump -h /var/run/postgresql -U dispatch -d dispatcharr --format=custom -f /tmp/dispatcharr.pgdump"
podman cp dispatcharr:/tmp/dispatcharr.pgdump ./dispatcharr-backup.pgdump
```

On Downtify, `data/` is what matters (monitored playlists, preferences) —
`downloads/` is only the end result, rebuildable by downloading again if
needed.

## Security considerations — not implemented here

- **Indexer and download-client ports exposed on the tailnet through
  tsdproxy** — like the rest of this repository, they are only reachable from
  inside the tailnet, not from the public internet.

## Useful commands

```bash
systemctl --user status media-stack-jellyfin media-stack-dispatcharr media-stack-downtify media-stack-prowlarr media-stack-sonarr media-stack-radarr media-stack-lidarr media-stack-bazarr media-stack-seerr media-stack-deluge media-stack-sabnzbd

podman logs -f sonarr   # swap in whichever service you want
podman exec dispatcharr su - dispatch -c "psql -h /var/run/postgresql -U dispatch -d dispatcharr -c 'SELECT 1;'"
```

## Credits

Quadlet deploy based on [Jellyfin](https://github.com/jellyfin/jellyfin)
(GPL-2.0), [Dispatcharr](https://github.com/Dispatcharr/Dispatcharr)
(AGPL-3.0), [Downtify](https://github.com/henriquesebastiao/downtify)
(GPL-3.0) by [Henrique Sebastião](https://github.com/henriquesebastiao), and
the [LinuxServer.io](https://github.com/linuxserver) images of
[Prowlarr](https://github.com/Prowlarr/Prowlarr) (GPL-3.0),
[Sonarr](https://github.com/Sonarr/Sonarr) (GPL-3.0),
[Radarr](https://github.com/Radarr/Radarr) (GPL-3.0),
[Lidarr](https://github.com/Lidarr/Lidarr) (GPL-3.0),
[Bazarr](https://github.com/morpheus65535/bazarr) (GPL-3.0),
[Deluge](https://github.com/deluge-torrent/deluge) (GPL-3.0) e
[SABnzbd](https://github.com/sabnzbd/sabnzbd) (GPL-2.0). Media requests come
from [Seerr](https://github.com/seerr-team/seerr) (MIT), the unified successor
to Overseerr/Jellyseerr. The optional VPN tunnel comes from
[Gluetun](https://github.com/qdm12/gluetun) by
[qdm12](https://github.com/qdm12) (MIT).
