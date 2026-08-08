# quadlet-homelab

**[🇧🇷 Leia em português](./docs/pt-BR/README.md)**

A personal collection of [Podman Quadlet](https://docs.podman.io/en/latest/markdown/podman-systemd.unit.5.html)
(rootless) deployments, one service per folder. This README is the reference
standard — rules and examples verified in practice, to follow for any new
service added here.

## Services in this repository

| Logo | Application | Version | Description |
| --- | --- | --- | --- |
| <img src="https://cdn.jsdelivr.net/gh/homarr-labs/dashboard-icons/svg/actual-budget.svg" width="48" height="48" alt=""> | [Actual Budget](./apps/actual-budget) | `latest` (auto-update) | Fast, privacy-focused personal finance management using the envelope budgeting method |
| <img src="https://cdn.jsdelivr.net/gh/homarr-labs/dashboard-icons/svg/adguard-home.svg" width="48" height="48" alt=""> | [AdGuard Home](./apps/adguardhome) | `v0.107.78` | A recursive DNS server that blocks ads and trackers for the whole network |
| <img src="https://cdn.jsdelivr.net/gh/homarr-labs/dashboard-icons/svg/anytype.svg" width="48" height="48" alt=""> | [any-sync-bundle](./apps/any-sync-bundle) | `1.5.0-2026-07-17` | The Any-Sync protocol backend, which syncs Anytype's data across devices without relying on the company's cloud |
| <img src="https://cdn.jsdelivr.net/gh/homarr-labs/dashboard-icons/svg/audiobookshelf.svg" width="48" height="48" alt=""> | [Audiobookshelf](./apps/audiobookshelf) | `2.36.0` | An audiobook and podcast server, with progress synced across devices |
| <img src="https://cdn.jsdelivr.net/gh/homarr-labs/dashboard-icons/svg/authentik.svg" width="48" height="48" alt=""> | [Authentik](./apps/authentik) | `2026.5.6` | An identity server (SSO, MFA, OIDC/SAML) — only the core is deployed, no forward-auth via tsdproxy yet (see the README) |
| <img src="https://cdn.jsdelivr.net/gh/homarr-labs/dashboard-icons/svg/beszel.svg" width="48" height="48" alt=""> | [Beszel](./apps/beszel) | `0.18.7` | A light dashboard for monitoring this host's resources (CPU/RAM/disk/network/containers) |
| <img src="https://cdn.jsdelivr.net/gh/homarr-labs/dashboard-icons/svg/calibre-web.svg" width="48" height="48" alt=""> | [Calibre-Web-Automated](./apps/calibre-web-automated) | `v4.0.6` | An ebook library with automatic conversion, metadata and covers via Calibre, readable straight in the browser |
| <img src="https://cdn.simpleicons.org/gnubash" width="48" height="48" alt=""> | [CookCLI](./apps/cookcli) | `0.32.1` | Plain-text recipes in the CookLang format — versionable in git, with no database and no forms |
| <img src="https://cdn.jsdelivr.net/gh/homarr-labs/dashboard-icons/svg/copyparty.svg" width="48" height="48" alt=""> | [Copyparty](./apps/copyparty) | `1.20.20` | A file server with browser or phone uploads, resumable transfers and WebDAV |
| <img src="https://cdn.jsdelivr.net/gh/homarr-labs/dashboard-icons/svg/donetick.svg" width="48" height="48" alt=""> | [Donetick](./apps/donetick) | `v0.1.76` | Recurring household chores — who does them, how often, and when they are due |
| <img src="https://cdn.jsdelivr.net/gh/homarr-labs/dashboard-icons/svg/freshrss.svg" width="48" height="48" alt=""> | [FreshRSS](./apps/freshrss) | `1.29.1-alpine` | A self-hosted RSS/Atom feed aggregator, with a compatible API for mobile apps |
| <img src="https://cdn.jsdelivr.net/gh/homarr-labs/dashboard-icons/svg/frigate.svg" width="48" height="48" alt=""> | [Frigate](./apps/frigate) | `0.17.2` | An NVR with AI object detection — CPU-only by default, no camera configured yet (see the README) |
| <img src="https://cdn.simpleicons.org/ghost" width="48" height="48" alt=""> | [Ghost](./apps/ghost) | `6.56.0-alpine` | A self-hosted blog/newsletter (SQLite, development mode — see the README) |
| <img src="https://cdn.jsdelivr.net/gh/homarr-labs/dashboard-icons/svg/gitea.svg" width="48" height="48" alt=""> | [Gitea](./apps/gitea) | `1.27.1` | A light but complete Git server — repositories, issues, pull requests and CI in a single interface |
| <img src="https://cdn.jsdelivr.net/gh/NousResearch/hermes-agent@main/website/static/img/logo.png" width="48" height="48" alt=""> | [Hermes Agent](./apps/hermes-agent) | `v2026.8.3` | A personal AI agent with skills and memory, exposing an OpenAI-compatible API for the other services to call |
| <img src="https://cdn.jsdelivr.net/gh/homarr-labs/dashboard-icons/svg/homebox.svg" width="48" height="48" alt=""> | [HomeBox](./apps/homebox) | `0.26.2` | A home inventory — what you own, where it is, the receipt, the manual and the warranty, with search and labels |
| <img src="https://cdn.jsdelivr.net/gh/homarr-labs/dashboard-icons/svg/home-assistant.svg" width="48" height="48" alt=""> | [Home Assistant](./apps/home-assistant) | `2026.8.1` | The central home automation hub; it brings devices from any manufacturer into a single panel |
| <img src="https://cdn.jsdelivr.net/gh/homarr-labs/dashboard-icons/png/homepage.png" width="48" height="48" alt=""> | [homepage](./apps/homepage) | `latest` (auto-update) | A dashboard that discovers and organises the other containers by itself through labels, with no config to edit per new service |
| <img src="https://cdn.jsdelivr.net/gh/homarr-labs/dashboard-icons/svg/immich.svg" width="48" height="48" alt=""> | [Immich](./apps/immich) | `v3.1.0` | Photo and video backup and organisation, with face recognition and smart search |
| <img src="https://cdn.simpleicons.org/invoiceninja" width="48" height="48" alt=""> | [Invio](./apps/invio) | `v2.1.1` | Self-hosted invoicing and invoice tracking, on SQLite and with no external service |
| <img src="https://cdn.jsdelivr.net/gh/homarr-labs/dashboard-icons/svg/karakeep.svg" width="48" height="48" alt=""> | [Karakeep](./apps/karakeep) | `0.33.1` | A bookmark manager with full-text search and automatic archiving of every saved page's content |
| <img src="https://cdn.jsdelivr.net/gh/homarr-labs/dashboard-icons/png/lubelogger.png" width="48" height="48" alt=""> | [LubeLogger](./apps/lubelogger) | `v1.7.0` | Vehicle maintenance records — oil changes, services, costs and reminders, per vehicle |
| <img src="https://cdn.simpleicons.org/markdown" width="48" height="48" alt=""> | [mdrop](./apps/mdrop) | `latest` (pinned by digest) | Converts PDF, Office, image and audio to Markdown over the web, stateless and without leaving the machine |
|  | [Media Stack](./apps/media-stack) | — | Jellyfin, Dispatcharr, Downtify, Prowlarr, Sonarr, Radarr, Lidarr, Bazarr, Seerr, Gluetun, Deluge, SABnzbd — a media server plus automation, a shared data root, each app on its own version |
| <img src="https://cdn.jsdelivr.net/gh/homarr-labs/dashboard-icons/svg/memos.svg" width="48" height="48" alt=""> | [Memos](./apps/memos) | `0.30.0` | Quick notes, self-hosted and markdown-native |
| <img src="https://cdn.jsdelivr.net/gh/homarr-labs/dashboard-icons/svg/metube.svg" width="48" height="48" alt=""> | [MeTube](./apps/metube) | `2026.08.04` | A web interface for yt-dlp — paste the URL and the video lands on disk |
| <img src="https://cdn.jsdelivr.net/gh/homarr-labs/dashboard-icons/svg/monica.svg" width="48" height="48" alt=""> | [Monica](./apps/monica) | `main` (no pinned tag, see the README) | A personal CRM — relationship history, contacts, reminders |
| <img src="https://cdn.jsdelivr.net/gh/homarr-labs/dashboard-icons/svg/n8n.svg" width="48" height="48" alt=""> | [n8n](./apps/n8n) | `2.33.7` | Workflow automation through a visual node editor |
| <img src="https://cdn.jsdelivr.net/gh/homarr-labs/dashboard-icons/svg/netbootxyz.svg" width="48" height="48" alt=""> | [netboot.xyz](./apps/netbootxyz) | `0.7.6-nbxyz23` | A network boot (PXE) menu for installing or trying distros and tools without writing a USB stick |
| <img src="https://cdn.jsdelivr.net/gh/homarr-labs/dashboard-icons/svg/nginx.svg" width="48" height="48" alt=""> | [nginx](./apps/nginx) | `1.30.4-alpine` | A static file server |
| <img src="https://cdn.jsdelivr.net/gh/homarr-labs/dashboard-icons/svg/node-red.svg" width="48" height="48" alt=""> | [Node-RED](./apps/node-red) | `5.0.4-minimal` | Flow automation through a visual node editor |
| <img src="https://cdn.jsdelivr.net/gh/homarr-labs/dashboard-icons/svg/ntfy.svg" width="48" height="48" alt=""> | [ntfy](./apps/ntfy) | `v2.27.0` | A push notification server — where the uptime-kuma, wud and zerobyte alerts go, with a phone app |
| <img src="https://cdn.jsdelivr.net/gh/homarr-labs/dashboard-icons/svg/open-webui.svg" width="48" height="48" alt=""> | [Open WebUI](./apps/openwebui) | `v0.11.0` (Open WebUI) + `0.32.6` (Ollama) | A web chat interface plus a local LLM server, CPU-only by default (NVIDIA/AMD GPU options are documented) |
| <img src="https://cdn.jsdelivr.net/gh/homarr-labs/dashboard-icons/png/omni-tools.png" width="48" height="48" alt=""> | [Omni Tools](./apps/omni-tools) | `0.6.0` | Converters, generators and calculators that run in the browser — nothing is sent to the server |
| <img src="https://cdn.jsdelivr.net/gh/rmyndharis/OpenWA@main/docs/logo/openwa.svg" width="48" height="48" alt=""> | [OpenWA](./apps/openwa) | `0.14.6` | A WhatsApp API gateway — turns the account into REST plus webhooks, for n8n and Home Assistant to use |
| <img src="https://cdn.jsdelivr.net/gh/homarr-labs/dashboard-icons/svg/owncloud.svg" width="48" height="48" alt=""> | [ownCloud](./apps/owncloud) | `11.0.0-20260802` | File sync and sharing on a cloud of your own |
| <img src="https://cdn.jsdelivr.net/gh/homarr-labs/dashboard-icons/svg/owntracks.svg" width="48" height="48" alt=""> | [OwnTracks](./apps/owntracks) | `1.0.1` | Personal location tracking through a phone app, with its own MQTT broker and a position history |
| <img src="https://cdn.jsdelivr.net/gh/homarr-labs/dashboard-icons/svg/paperless-ngx.svg" width="48" height="48" alt=""> | [Paperless-ngx](./apps/paperless-ngx) | `3.0.5` | Scans, OCRs and indexes documents automatically, with full-text search so you never hunt for paper again |
| <img src="https://cdn.jsdelivr.net/gh/homarr-labs/dashboard-icons/svg/proxmox.svg" width="48" height="48" alt=""> | [Proxmox VE](./apps/proxmox) | `9.2.9` | The Proxmox hypervisor in a container, for trying it without dedicating a machine — runs privileged |
| <img src="https://cdn.jsdelivr.net/gh/homarr-labs/dashboard-icons/svg/radicale.svg" width="48" height="48" alt=""> | [Radicale](./apps/radicale) | `3.7.6.0` | A light, minimal CalDAV/CardDAV server |
| <img src="https://cdn.jsdelivr.net/gh/homarr-labs/dashboard-icons/svg/stirling-pdf.svg" width="48" height="48" alt=""> | [Stirling-PDF](./apps/stirling-pdf) | `2.14.3` | Local PDF manipulation — merge, split, convert, OCR and sign, in place of the "online PDF" sites |
| <img src="https://cdn.jsdelivr.net/gh/homarr-labs/dashboard-icons/svg/syncthing.svg" width="48" height="48" alt=""> | [Syncthing](./apps/syncthing) | `2.1.3` | P2P file sync between devices, with no central server |
| <img src="https://cdn.jsdelivr.net/gh/homarr-labs/dashboard-icons/svg/tailscale.svg" width="48" height="48" alt=""> | [tsdproxy](./apps/tsdproxy) | `2` | Publishes containers on the tailnet automatically, from labels alone — no per-service proxy configuration |
| <img src="https://cdn.jsdelivr.net/gh/containers/containertoolbx.org@main/apple-touch-icon.png" width="48" height="48" alt=""> | [Toolbx](./apps/toolbx) | — | Disposable Arch, Fedora, RHEL and Ubuntu shells, on the official Toolbx images — somewhere to install a one-off tool that is not the host |
| <img src="https://cdn.jsdelivr.net/gh/homarr-labs/dashboard-icons/svg/traccar.svg" width="48" height="48" alt=""> | [Traccar](./apps/traccar) | `6.14.5` | GPS tracking — live map, history, geofences and reports, with a phone app |
| <img src="https://cdn.jsdelivr.net/gh/homarr-labs/dashboard-icons/svg/qemu.svg" width="48" height="48" alt=""> | [VM](./apps/vm) | — | Windows, macOS and 23 Linux distros as VMs in containers, viewed in the browser — needs KVM on the host |
| <img src="https://cdn.jsdelivr.net/gh/homarr-labs/dashboard-icons/svg/uptime-kuma.svg" width="48" height="48" alt=""> | [Uptime Kuma](./apps/uptime-kuma) | `2.5.0` | An uptime monitor for the other services and the tailnet, with history and notifications |
| <img src="https://cdn.jsdelivr.net/gh/homarr-labs/dashboard-icons/svg/vaultwarden.svg" width="48" height="48" alt=""> | [Vaultwarden](./apps/vaultwarden) | `1.37.1-alpine` | A password vault compatible with Bitwarden's protocol, light enough to run anywhere |
| <img src="https://raw.githubusercontent.com/wallacepnts/vaultzap/main/internal/web/static/img/favicon.svg" width="48" height="48" alt=""> | [VaultZap](./apps/vaultzap) | `latest` (auto-update) | A local, browsable archive of exported WhatsApp conversations — search, gallery and calendar, fully offline |
| <img src="https://cdn.jsdelivr.net/gh/homarr-labs/dashboard-icons/svg/wger.svg" width="48" height="48" alt=""> | [wger](./apps/wger) | `2.6.0` | Workout planning and tracking, with an exercise database and body measurements |
| <img src="https://cdn.jsdelivr.net/gh/homarr-labs/dashboard-icons/svg/zigbee2mqtt.svg" width="48" height="48" alt=""> | [Zigbee2MQTT](./apps/zigbee2mqtt) | `2.13.0` | A bridge between Zigbee devices and MQTT, with no proprietary hub — no coordinator plugged in yet (see the README) |
| <img src="https://cdn.jsdelivr.net/gh/getwud/wud@main/ui/public/img/icons/android-chrome-512x512.png" width="48" height="48" alt=""> | [WUD (What's Up Docker)](./apps/wud) | `8.3.1` | Watches for available image updates for the containers, applying nothing itself — it only reports |
| <img src="https://cdn.jsdelivr.net/gh/homarr-labs/dashboard-icons/png/zerobyte.png" width="48" height="48" alt=""> | [Zerobyte](./apps/zerobyte) | `v0.41.0` | Automates backups (via Restic) of every other service's data in this repository |

**AutoUpdate on**: [Actual Budget](./apps/actual-budget/), [homepage](./apps/homepage/), [VaultZap](./apps/vaultzap/)
— everything else uses an explicit tag plus a manual bump (this repository's
default, rule 9). The criteria for turning it on, and why most of it stays
off: see [Auto-update](./docs/auto-update.md).

The Version column mirrors the tag in each service's `.container` `Image=` —
update it here alongside any manual bump, it is not generated automatically.

## On an ARM server

**79 of the 81 images here publish an `arm64` variant.** Those services install
with no change at all — Podman picks the right manifest by itself, and
`install.py <app> --apply` works exactly as on x86.

Two images are `amd64` only, and take their service down with them:

| Image | Service | Why |
| --- | --- | --- |
| `dockurr/macos` | `vm-macos` | no ARM build; it emulates an Intel Mac, and macOS on ARM is a different machine |
| `quay.io/toolbx/arch-toolbox` | `toolbx-arch` | Arch Linux has no official ARM port |

**A matching image is not the whole story for the VM services.** KVM only
accelerates a guest of the same architecture, so what decides is the guest, not
the image — and an x86 guest on an ARM host falls back to emulation and is
unusably slow. `apps/vm` therefore carries a unit per pairing:

| Host | Windows | Linux | macOS |
| --- | --- | --- | --- |
| x86_64 | `vm-windows` | `vm-qemu` | `vm-macos` |
| ARM64 | `vm-windows-arm` | [qemus/qemu-arm](https://github.com/qemus/qemu-arm/), not packaged here | — |

`vm-windows-arm` is written from upstream's documentation rather than measured:
there is no ARM host here to test it on.

To check any image yourself before committing to a host:

```bash
podman manifest inspect docker.io/library/postgres:16-alpine \
  | python3 -c "import sys,json;print(sorted({m['platform']['architecture'] for m in json.load(sys.stdin)['manifests'] if m['platform']['architecture']!='unknown'}))"
```

Docker Hub rate-limits anonymous manifest lookups, so a batch of these will
start failing partway through — space them out, or query the registry API
directly.

## Documentation

| | |
| --- | --- |
| [Installing and operating](./docs/installing.md) | `install.py`: install, update, back up, restore, remove |
| [Recovery and migration](./docs/recovery.md) | the machine died, or you are moving to another server |
| [Tools](./docs/tools.md) | `check.py` and `updates.py`, and what CI runs |
| [Conventions](./docs/conventions.md) | the 22 rules, each with the real case that produced it |
| [Reference](./docs/reference.md) | where every file lives, and an annotated `.container` |
| [Auto-update](./docs/auto-update.md) | why almost everything here updates by hand |

Every one of these is also available in Portuguese, in
[`docs/pt-BR/`](./docs/pt-BR/).

The **manual installation** of each service is in its own README, in a
collapsible *"Manual installation (advanced)"* block — the same steps
`install.py` runs, one at a time.

## Quick start

```bash
# 1. Podman's folders (the only mandatory step)
mkdir -p ~/.config/containers/{systemd,secrets,env,volumes}

# 2. install a service
python3 install.py memos --apply
```

Tailscale and tsdproxy are **optional** — see
[Step zero](#step-zero-preparing-the-host). Without them, `--access local`.

## Step zero: preparing the host

**The minimum, and this is all of it:**

```bash
mkdir -p ~/.config/containers/{systemd,secrets,env,volumes}
```

Every service in this repository publishes a port on the host. With the
folders created and rootless Podman working, you can install any of them and
reach it at `http://<host-ip>:<port>` — nothing here requires an external
network, a domain or a certificate.

### Optional: the tailnet

[Tailscale](https://tailscale.com) and [tsdproxy](./apps/tsdproxy/) are
**optional**. They solve two things: reaching a service from outside your
home without opening a port on the router, and having real per-service HTTPS
(which matters for an app that uses WebCrypto — [Vaultwarden](./apps/vaultwarden/)
only decrypts the session in a secure context).

For whoever wants it, in this order:

**1. Tailscale, and not as a Quadlet.** It needs to integrate with the host's
`systemd-resolved` for MagicDNS to work, and a container does not share the
host's D-Bus/mount namespace (rule 21). On MicroOS:

```bash
sudo transactional-update pkg install tailscale
sudo systemctl reboot            # transactional-update only applies on the next boot
sudo systemctl enable --now tailscaled
sudo tailscale up
```

**2. The `TAILNET` variable**, which resolves the `homepage.href` of every
unit (rule 19):

```bash
mkdir -p ~/.config/environment.d
echo 'TAILNET=<your-tailnet>' > ~/.config/environment.d/tailnet.conf
systemctl --user daemon-reload
```

**3. [tsdproxy](./apps/tsdproxy/)**, which publishes everything else on the
tailnet automatically, from labels:

```bash
python3 install.py tsdproxy --apply
```

`python3 install.py tailscale` repeats these instructions, since Tailscale
has no folder under `apps/`.

### Installing without a tailnet

Only one thing breaks without it: the units' `homepage.href` points at a
`.ts.net` domain that does not exist, and the dashboard link dies. `--local`
swaps that label for the LAN address as the unit is copied:

```bash
python3 install.py memos --apply --local
# Label=homepage.href=http://192.168.1.12:5230
```

It also comments the `tsdproxy.*` labels out (it comments them, it does not
delete them), so turning the tailnet on later means reinstalling the service
without `--local` rather than rewriting the unit by hand. To keep the
tsdproxy node and only change the dashboard link, use `--href-local` on its
own. The `.env.example` files that mention `<your-tailnet>` (vaultwarden,
gitea, karakeep and 14 others) still need reviewing by hand: they are
`DOMAIN`/`ALLOWED_HOSTS` values the app itself writes into its database.
