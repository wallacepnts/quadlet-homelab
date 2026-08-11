# Quadlet Homelab

**[🇧🇷 Leia em português](./docs/pt-BR/README.md)**

65 self-hosted services as [Podman Quadlet](https://docs.podman.io/en/latest/markdown/podman-systemd.unit.5.html)
units, rootless, one service per folder.

## Quick start

```bash
curl -fsSL https://raw.githubusercontent.com/wallacepnts/quadlet-homelab/main/bootstrap.sh | bash
```

Debian and Ubuntu ship neither `curl` nor `wget` in a bare install — measured
on their base images. There you are installing packages anyway, so install
`git`, which the bootstrap needs regardless:

```bash
git clone https://github.com/wallacepnts/quadlet-homelab
bash quadlet-homelab/bootstrap.sh
```

It checks git/python3/podman and `systemd --user`, creates Podman's folders,
clones the repository into `~/quadlet-homelab` and links `qh`, `qh-check` and
`qh-updates` into `~/.local/bin`. No `sudo`, no packages installed, no service
started.

Then:

```bash
qh                   # the services
qh memos             # the plan for one, without installing
qh memos --apply     # do it
```

Every service is reachable at `http://<host-ip>:<port>` with nothing else set
up — no domain, no certificate, no router change.

## Updating

Two different things, in this order.

**The repository** — the units and the recipes. Re-run the same command, or
pull the clone; they do the same thing:

```bash
curl -fsSL https://raw.githubusercontent.com/wallacepnts/quadlet-homelab/main/bootstrap.sh | bash
```

It fast-forwards the clone and refreshes the links. A clone that has diverged
is left alone and told about, so local edits are never dropped.

**The services on the host** — nothing moves until you say so. A newer unit in
the repository does not change the file already installed:

```bash
qh-updates                     # which images are behind their upstream release
qh memos --update --apply      # one service
qh --all --update --apply      # after a round of bumps
```

`--update` re-copies the units, pulls the image and restarts. It touches no
volume, no `.env` and no secret. A service already in sync is skipped — and
that means the running container too, not just the file: Quadlet bakes the
labels in at creation, so a unit correct on disk can still be backed by a
container running the previous ones. A moving tag (`latest`) is always
pulled. To go through anyway, use `--reinstall`.

## Requirements

- **Podman 5.0 or newer.** This is the real floor: `Notify=healthy` arrived
  there, and 92 of the 101 units use it. On 4.x the start returns before the app
  is ready, and the install reports a success it cannot know about.
- **systemd with a user session** and cgroups v2.
- **SELinux**, if your distribution has it. The units carry `:Z` on 125 volume
  lines; where SELinux is absent those are ignored and nothing breaks, but the
  per-container isolation they ask for is not there either.
- `/dev/kvm`, only for the six VM services.

```bash
podman --version
```

Measured, by installing podman in each and reading the version:

| Distribution | Podman | |
| --- | --- | --- |
| Arch | 6.0.2 | works |
| openSUSE Tumbleweed, Slowroll | 6.0.2 | works |
| openSUSE MicroOS, Aeon, Kalpa | 5.8 | works |
| Fedora 42 | 5.8.2 | works |
| Debian 13 | 5.4.2 | works |
| openSUSE Leap 16.0 | 5.4.2 | works |
| Ubuntu 25.04 | 5.4.1 | works |
| Ubuntu 24.04 LTS | 4.9.3 | **too old** |
| openSUSE Leap 15.6 | 4.9.5 | **too old** |
| Debian 12 | 4.3.1 | **too old** |

Aeon and Kalpa are MicroOS with a desktop and share its repositories. Leap
Micro follows the Leap generation it was built from, so its 5.x line inherits
Leap 15's problem — it publishes no container image and was not measured here.

## Services

| Logo | Application | Version | Description |
| --- | --- | --- | --- |
| <img src="https://cdn.jsdelivr.net/gh/homarr-labs/dashboard-icons/svg/actual-budget.svg" width="48" height="48" alt=""> | [Actual Budget](./apps/actual-budget) | `latest` (auto-update) | Fast, privacy-focused personal finance management using the envelope budgeting method |
| <img src="https://cdn.jsdelivr.net/gh/homarr-labs/dashboard-icons/svg/adguard-home.svg" width="48" height="48" alt=""> | [AdGuard Home](./apps/adguardhome) | `v0.107.78` | A recursive DNS server that blocks ads and trackers for the whole network |
| <img src="https://cdn.jsdelivr.net/gh/homarr-labs/dashboard-icons/svg/anytype.svg" width="48" height="48" alt=""> | [any-sync-bundle](./apps/any-sync-bundle) | `1.5.0-2026-07-17` | The Any-Sync protocol backend, which syncs Anytype's data across devices without relying on the company's cloud |
| <img src="https://cdn.jsdelivr.net/gh/homarr-labs/dashboard-icons/svg/audiobookshelf.svg" width="48" height="48" alt=""> | [Audiobookshelf](./apps/audiobookshelf) | `2.36.0` | An audiobook and podcast server, with progress synced across devices |
| <img src="https://cdn.jsdelivr.net/gh/homarr-labs/dashboard-icons/svg/authentik.svg" width="48" height="48" alt=""> | [Authentik](./apps/authentik) | `2026.5.6` | An identity server (SSO, MFA, OIDC/SAML) — only the core is deployed, no forward-auth via tsdproxy yet (see the README) |
| <img src="https://api.iconify.design/mdi/check-circle-outline.svg?color=%23888888" width="48" height="48" alt=""> | [Beaver Habits](./apps/beaverhabits) | `0.10.0` | Habit tracking with no goals and no streak-shaming — you mark the day and move on |
| <img src="https://cdn.jsdelivr.net/gh/homarr-labs/dashboard-icons/svg/beszel.svg" width="48" height="48" alt=""> | [Beszel](./apps/beszel) | `0.18.7` | A light dashboard for monitoring this host's resources (CPU/RAM/disk/network/containers) |
| <img src="https://cdn.jsdelivr.net/gh/homarr-labs/dashboard-icons/svg/calibre-web.svg" width="48" height="48" alt=""> | [Calibre-Web-Automated](./apps/calibre-web-automated) | `v4.0.6` | An ebook library with automatic conversion, metadata and covers via Calibre, readable straight in the browser |
| <img src="https://cdn.jsdelivr.net/gh/homarr-labs/dashboard-icons/svg/collabora-online.svg" width="48" height="48" alt=""> | [Collabora](./apps/collabora) | `26.04.3.1.1` | Editing documents inside ownCloud — writer, spreadsheet and slides, in the browser |
| <img src="https://cdn.simpleicons.org/gnubash" width="48" height="48" alt=""> | [CookCLI](./apps/cookcli) | `0.32.1` | Plain-text recipes in the CookLang format — versionable in git, with no database and no forms |
| <img src="https://cdn.jsdelivr.net/gh/homarr-labs/dashboard-icons/svg/copyparty.svg" width="48" height="48" alt=""> | [Copyparty](./apps/copyparty) | `1.20.20` | A file server with browser or phone uploads, resumable transfers and WebDAV |
| <img src="https://cdn.jsdelivr.net/gh/homarr-labs/dashboard-icons/svg/donetick.svg" width="48" height="48" alt=""> | [Donetick](./apps/donetick) | `v0.1.76` | Recurring household chores — who does them, how often, and when they are due |
| <img src="https://cdn.jsdelivr.net/gh/homarr-labs/dashboard-icons/svg/excalidraw.svg" width="48" height="48" alt=""> | [ExcaliDash](./apps/excalidash) | `0.5.1` | A dashboard for Excalidraw drawings — folders, sharing and multi-user, over your own storage |
| <img src="https://cdn.jsdelivr.net/gh/homarr-labs/dashboard-icons/svg/filebrowser-quantum.svg" width="48" height="48" alt=""> | [FileBrowser Quantum](./apps/filebrowser) | `1.5.1-stable` | A web file manager — search, thumbnails, WebDAV, and a shell over a directory you pick |
| <img src="https://cdn.jsdelivr.net/gh/homarr-labs/dashboard-icons/svg/freshrss.svg" width="48" height="48" alt=""> | [FreshRSS](./apps/freshrss) | `1.29.1-alpine` | A self-hosted RSS/Atom feed aggregator, with a compatible API for mobile apps |
| <img src="https://cdn.jsdelivr.net/gh/homarr-labs/dashboard-icons/png/frigate.png" width="48" height="48" alt=""> | [Frigate](./apps/frigate) | `0.17.2` | An NVR with AI object detection — CPU-only by default, no camera configured yet (see the README) |
| <img src="https://cdn.simpleicons.org/ghost" width="48" height="48" alt=""> | [Ghost](./apps/ghost) | `6.56.0-alpine` | A self-hosted blog/newsletter (SQLite, development mode — see the README) |
| <img src="https://cdn.jsdelivr.net/gh/homarr-labs/dashboard-icons/svg/gitea.svg" width="48" height="48" alt=""> | [Gitea](./apps/gitea) | `1.27.1` | A light but complete Git server — repositories, issues, pull requests and CI in a single interface |
| <img src="https://cdn.jsdelivr.net/gh/NousResearch/hermes-agent@main/website/static/img/logo.png" width="48" height="48" alt=""> | [Hermes Agent](./apps/hermes-agent) | `v2026.8.3` | A personal AI agent with skills and memory, exposing an OpenAI-compatible API for the other services to call |
| <img src="https://cdn.jsdelivr.net/gh/homarr-labs/dashboard-icons/svg/homebox.svg" width="48" height="48" alt=""> | [HomeBox](./apps/homebox) | `0.26.2` | A home inventory — what you own, where it is, the receipt, the manual and the warranty, with search and labels |
| <img src="https://cdn.jsdelivr.net/gh/homarr-labs/dashboard-icons/svg/grafana.svg" width="48" height="48" alt=""> | [Grafana](./apps/grafana) | `13.1.3` | Dashboards over whatever you point it at — it brings no data of its own |
| <img src="https://cdn.jsdelivr.net/gh/homarr-labs/dashboard-icons/svg/home-assistant.svg" width="48" height="48" alt=""> | [Home Assistant](./apps/home-assistant) | `2026.8.1` | The central home automation hub; it brings devices from any manufacturer into a single panel |
| <img src="https://cdn.jsdelivr.net/gh/homarr-labs/dashboard-icons/png/homepage.png" width="48" height="48" alt=""> | [homepage](./apps/homepage) | `latest` (auto-update) | A dashboard that discovers and organises the other containers by itself through labels, with no config to edit per new service |
| <img src="https://cdn.jsdelivr.net/gh/homarr-labs/dashboard-icons/svg/immich.svg" width="48" height="48" alt=""> | [Immich](./apps/immich) | `v3.1.0` | Photo and video backup and organisation, with face recognition and smart search |
| <img src="https://cdn.simpleicons.org/invoiceninja/888888" width="48" height="48" alt=""> | [Invio](./apps/invio) | `v2.1.1` | Self-hosted invoicing and invoice tracking, on SQLite and with no external service |
| <img src="https://api.iconify.design/mdi/microphone-variant.svg?color=%23888888" width="48" height="48" alt=""> | [Karaoke Eternal](./apps/karaoke-eternal) | `2.0.2` | A karaoke party from your own library — everyone queues songs from their phone, one screen plays |
| <img src="https://cdn.jsdelivr.net/gh/homarr-labs/dashboard-icons/svg/karakeep.svg" width="48" height="48" alt=""> | [Karakeep](./apps/karakeep) | `0.33.1` | A bookmark manager with full-text search and automatic archiving of every saved page's content |
| <img src="https://cdn.jsdelivr.net/gh/homarr-labs/dashboard-icons/png/lubelogger.png" width="48" height="48" alt=""> | [LubeLogger](./apps/lubelogger) | `v1.7.0` | Vehicle maintenance records — oil changes, services, costs and reminders, per vehicle |
| <img src="https://cdn.jsdelivr.net/gh/homarr-labs/dashboard-icons/svg/mailpit.svg" width="48" height="48" alt=""> | [Mailpit](./apps/mailpit) | `v1.30.7` | An SMTP server that catches everything your apps send, to read in the browser instead of a real inbox |
| <img src="https://cdn.simpleicons.org/markdown/888888" width="48" height="48" alt=""> | [mdrop](./apps/mdrop) | `latest` (pinned by digest) | Converts PDF, Office, image and audio to Markdown over the web, stateless and without leaving the machine |
| <img src="https://api.iconify.design/mdi/multimedia.svg?color=%23888888" width="48" height="48" alt=""> | [Media Stack](./apps/media-stack) | — | Jellyfin, Navidrome, Seerr, Prowlarr, Sonarr, Radarr, Lidarr, Bazarr, SABnzbd, Deluge, Dispatcharr, Downtify and an optional Gluetun — a media server plus automation, a shared data root, each app on its own version |
| <img src="https://cdn.jsdelivr.net/gh/homarr-labs/dashboard-icons/svg/memos.svg" width="48" height="48" alt=""> | [Memos](./apps/memos) | `0.30.0` | Quick notes, self-hosted and markdown-native |
| <img src="https://cdn.jsdelivr.net/gh/homarr-labs/dashboard-icons/svg/metube.svg" width="48" height="48" alt=""> | [MeTube](./apps/metube) | `2026.08.04` | A web interface for yt-dlp — paste the URL and the video lands on disk |
| <img src="https://cdn.jsdelivr.net/gh/homarr-labs/dashboard-icons/svg/monica.svg" width="48" height="48" alt=""> | [Monica](./apps/monica) | `main` (no pinned tag, see the README) | A personal CRM — relationship history, contacts, reminders |
| <img src="https://cdn.jsdelivr.net/gh/homarr-labs/dashboard-icons/svg/n8n.svg" width="48" height="48" alt=""> | [n8n](./apps/n8n) | `2.33.7` | Workflow automation through a visual node editor |
| <img src="https://api.iconify.design/mdi/web-box.svg?color=%23888888" width="48" height="48" alt=""> | [neko](./apps/neko) | `3.1.5` | A browser running on the server, streamed to yours — shared control, and nothing it opens touches your machine |
| <img src="https://cdn.jsdelivr.net/gh/homarr-labs/dashboard-icons/svg/netbootxyz.svg" width="48" height="48" alt=""> | [netboot.xyz](./apps/netbootxyz) | `0.7.6-nbxyz23` | A network boot (PXE) menu for installing or trying distros and tools without writing a USB stick |
| <img src="https://cdn.jsdelivr.net/gh/homarr-labs/dashboard-icons/svg/nginx.svg" width="48" height="48" alt=""> | [nginx](./apps/nginx) | `1.30.4-alpine` | A static file server |
| <img src="https://cdn.jsdelivr.net/gh/homarr-labs/dashboard-icons/svg/node-red.svg" width="48" height="48" alt=""> | [Node-RED](./apps/node-red) | `5.0.4-minimal` | Flow automation through a visual node editor |
| <img src="https://cdn.jsdelivr.net/gh/homarr-labs/dashboard-icons/svg/ntfy.svg" width="48" height="48" alt=""> | [ntfy](./apps/ntfy) | `v2.27.0` | A push notification server — where the uptime-kuma, wud and zerobyte alerts go, with a phone app |
| <img src="https://cdn.jsdelivr.net/gh/homarr-labs/dashboard-icons/svg/open-webui.svg" width="48" height="48" alt=""> | [Open WebUI](./apps/openwebui) | `v0.11.0` (Open WebUI) + `0.32.6` (Ollama) | A web chat interface plus a local LLM server, CPU-only by default (NVIDIA/AMD GPU options are documented) |
| <img src="https://cdn.jsdelivr.net/gh/homarr-labs/dashboard-icons/png/omni-tools.png" width="48" height="48" alt=""> | [Omni Tools](./apps/omni-tools) | `0.6.0` | Converters, generators and calculators that run in the browser — nothing is sent to the server |
| <img src="https://cdn.jsdelivr.net/gh/rmyndharis/OpenWA@main/docs/logo/openwa.svg" width="48" height="48" alt=""> | [OpenWA](./apps/openwa) | `0.15.0` | A WhatsApp API gateway — turns the account into REST plus webhooks, for n8n and Home Assistant to use |
| <img src="https://cdn.jsdelivr.net/gh/homarr-labs/dashboard-icons/svg/owncloud.svg" width="48" height="48" alt=""> | [ownCloud](./apps/owncloud) | `11.0.0-20260802` | File sync and sharing on a cloud of your own |
| <img src="https://cdn.jsdelivr.net/gh/homarr-labs/dashboard-icons/svg/owntracks.svg" width="48" height="48" alt=""> | [OwnTracks](./apps/owntracks) | `1.0.2` | Personal location tracking through a phone app, with its own MQTT broker and a position history |
| <img src="https://cdn.jsdelivr.net/gh/homarr-labs/dashboard-icons/svg/paperless-ngx.svg" width="48" height="48" alt=""> | [Paperless-ngx](./apps/paperless-ngx) | `3.0.5` | Scans, OCRs and indexes documents automatically, with full-text search so you never hunt for paper again |
| <img src="https://api.iconify.design/mdi/email-fast.svg?color=%23888888" width="48" height="48" alt=""> | [Postfix](./apps/postfix) | `v5.1.0` | An SMTP relay for the other containers — they hand mail to one place, and the credentials of the provider live here only |
| <img src="https://cdn.jsdelivr.net/gh/homarr-labs/dashboard-icons/svg/prometheus.svg" width="48" height="48" alt=""> | [Prometheus](./apps/prometheus) | `v3.13.2` | Scrapes metrics on a schedule and keeps the history — the data source Grafana draws from |
| <img src="https://cdn.jsdelivr.net/gh/homarr-labs/dashboard-icons/svg/proxmox.svg" width="48" height="48" alt=""> | [Proxmox VE](./apps/proxmox) | `9.2.9` | The Proxmox hypervisor in a container, for trying it without dedicating a machine — runs privileged |
| <img src="https://api.iconify.design/mdi/gamepad-variant.svg?color=%23888888" width="48" height="48" alt=""> | [Retrom](./apps/retrom) | `0.8.4` | A game library for emulation — one collection, played in the browser or through the desktop client |
| <img src="https://cdn.jsdelivr.net/gh/homarr-labs/dashboard-icons/svg/radicale.svg" width="48" height="48" alt=""> | [Radicale](./apps/radicale) | `v0.26.0` | A light, minimal CalDAV/CardDAV server, on the rebuild that carries the birthday-calendar script (Radicale 3.7.6.0 inside) |
| <img src="https://cdn.jsdelivr.net/gh/homarr-labs/dashboard-icons/png/searxng.png" width="48" height="48" alt=""> | [SearXNG](./apps/searxng) | `2026.8.10-0a118066d` | Metasearch that queries dozens of engines at once, keeping no profile of you |
| <img src="https://cdn.jsdelivr.net/gh/homarr-labs/dashboard-icons/svg/stirling-pdf.svg" width="48" height="48" alt=""> | [Stirling-PDF](./apps/stirling-pdf) | `2.14.3` | Local PDF manipulation — merge, split, convert, OCR and sign, in place of the "online PDF" sites |
| <img src="https://cdn.jsdelivr.net/gh/homarr-labs/dashboard-icons/svg/syncthing.svg" width="48" height="48" alt=""> | [Syncthing](./apps/syncthing) | `2.1.3` | P2P file sync between devices, with no central server |
| <img src="https://cdn.jsdelivr.net/gh/selfhst/icons/svg/tsdproxy.svg" width="48" height="48" alt=""> | [tsdproxy](./apps/tsdproxy) | `2` | Publishes containers on the tailnet automatically, from labels alone — no per-service proxy configuration |
| <img src="https://cdn.jsdelivr.net/gh/containers/containertoolbx.org@main/apple-touch-icon.png" width="48" height="48" alt=""> | [Toolbx](./apps/toolbx) | — | Disposable Arch, Fedora, RHEL and Ubuntu shells, on the official Toolbx images — somewhere to install a one-off tool that is not the host |
| <img src="https://cdn.jsdelivr.net/gh/homarr-labs/dashboard-icons/svg/traccar.svg" width="48" height="48" alt=""> | [Traccar](./apps/traccar) | `6.14.5` | GPS tracking — live map, history, geofences and reports, with a phone app |
| <img src="https://cdn.jsdelivr.net/gh/homarr-labs/dashboard-icons/svg/qemu.svg" width="48" height="48" alt=""> | [VM](./apps/vm) | — | Windows, macOS, ChromeOS Flex, ZimaOS and 23 Linux distros as VMs in containers, viewed in the browser — needs KVM on the host |
| <img src="https://cdn.jsdelivr.net/gh/homarr-labs/dashboard-icons/svg/uptime-kuma.svg" width="48" height="48" alt=""> | [Uptime Kuma](./apps/uptime-kuma) | `2.5.0` | An uptime monitor for the other services and the tailnet, with history and notifications |
| <img src="https://cdn.jsdelivr.net/gh/homarr-labs/dashboard-icons/png/vaultwarden.png" width="48" height="48" alt=""> | [Vaultwarden](./apps/vaultwarden) | `1.37.1-alpine` | A password vault compatible with Bitwarden's protocol, light enough to run anywhere |
| <img src="https://raw.githubusercontent.com/wallacepnts/vaultzap/main/internal/web/static/img/favicon.svg" width="48" height="48" alt=""> | [VaultZap](./apps/vaultzap) | `latest` (auto-update) | A local, browsable archive of exported WhatsApp conversations — search, gallery and calendar, fully offline |
| <img src="https://cdn.jsdelivr.net/gh/homarr-labs/dashboard-icons/svg/wger.svg" width="48" height="48" alt=""> | [wger](./apps/wger) | `2.6.0` | Workout planning and tracking, with an exercise database and body measurements |
| <img src="https://cdn.jsdelivr.net/gh/homarr-labs/dashboard-icons/svg/zigbee2mqtt.svg" width="48" height="48" alt=""> | [Zigbee2MQTT](./apps/zigbee2mqtt) | `2.13.0` | A bridge between Zigbee devices and MQTT, with no proprietary hub — no coordinator plugged in yet (see the README) |
| <img src="https://cdn.jsdelivr.net/gh/getwud/wud@main/ui/public/img/icons/android-chrome-512x512.png" width="48" height="48" alt=""> | [WUD (What's Up Docker)](./apps/wud) | `8.3.1` | Watches for available image updates for the containers, applying nothing itself — it only reports |
| <img src="https://cdn.jsdelivr.net/gh/homarr-labs/dashboard-icons/png/zerobyte.png" width="48" height="48" alt=""> | [Zerobyte](./apps/zerobyte) | `v0.41.0` | Automates backups (via Restic) of every other service's data in this repository |

**AutoUpdate on**: Actual Budget, homepage, VaultZap. Everything else is
pinned to a tag and updated by hand.

## Optional: the tailnet

[Tailscale](https://tailscale.com) plus tsdproxy give each service its own
HTTPS name, reachable from anywhere without opening a port. Vaultwarden needs
it — it only decrypts the session in a secure context.

`qh tailscale` checks the three steps below against the host and prints only
what is missing.

Install Tailscale for your distribution (see
[tailscale.com/download](https://tailscale.com/download)), then:

```bash
sudo systemctl enable --now tailscaled
sudo tailscale up

mkdir -p ~/.config/environment.d
echo 'TAILNET=<your-tailnet>' > ~/.config/environment.d/tailnet.conf
systemctl --user daemon-reload

qh tsdproxy --apply
```

Without a tailnet, set the rule once and every install follows it:

```bash
qh --set-access local
```

It points the dashboard link at the LAN address and comments the `tsdproxy.*`
labels out instead of deleting them. Turning it on later is an update, which
keeps the data:

```bash
qh --all --update --apply --access tailnet
```

## On an ARM server

Nearly every image here publishes an `arm64` variant and installs unchanged.
Three do not, and take their service with them:

| Image | Service |
| --- | --- |
| `dockurr/macos` | `vm-macos` |
| `dockurr/chromeos` | `vm-chromeos` |
| `quay.io/toolbx/arch-toolbox` | `toolbx-arch` |

For the VM services what decides is the guest, not the image: KVM only
accelerates a guest of the same architecture. `apps/vm` carries `vm-windows`
for x86_64 and `vm-windows-arm` for ARM64.

## Documentation

| | |
| --- | --- |
| [Installing and operating](./docs/installing.md) | install, update, back up, restore, remove |
| [Recovery and migration](./docs/recovery.md) | the machine died, or you are moving hosts |
| [Reference](./docs/reference.md) | where every file lives, and an annotated `.container` |
| [Auto-update](./docs/auto-update.md) | why almost everything updates by hand |
| [Tools](./docs/tools.md) | `qh-check` and `qh-updates` |

All of it is also in Portuguese, in [`docs/pt-BR/`](./docs/pt-BR/).
