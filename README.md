# Quadlet Homelab

**[🇧🇷 Leia em português](./docs/pt-BR/README.md)**

84 self-hosted services as [Podman Quadlet](https://docs.podman.io/en/latest/markdown/podman-systemd.unit.5.html)
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
clones the repository into `~/quadlet-homelab`, links the tools into `~/.local/bin`, and
**starts the web panel** as a `systemd --user` service of yours. No `sudo`, no packages
installed. It asks once where you will open the panel from (this machine only, the local
network, or the tailnet) and ends by printing the address and the login token:

```
  panel is up: http://127.0.0.1:8484
  login (the token): …
```

**Open that address in a browser: that is how you use this.** The panel has a Store (all
83 services, by category, with screenshots) and My apps (what is installed, as a launcher).
From it you install an app (it asks only what that app needs, and lets you customize ports,
volumes and variables first, or try it for a few hours), update it with one button, back it up,
restore it, change its settings, read its logs live, open a console in its container, pause,
stop or remove it, and see the host's load, memory and temperature. Every button runs the same
`qh` engine a terminal would; nothing in the panel is a second implementation.

Every service is reachable at `http://<host-ip>:<port>` with nothing else set
up — no domain, no certificate, no router change.

<details>
<summary>The terminal, if you prefer it (advanced)</summary>

```bash
qh                   # the services
qh memos             # the plan for one, without installing
qh memos --apply     # do it
```

[Installing and operating](./docs/installing.md) lists every mode.
</details>

## Updating

Two different things, in this order.

**The repository** — the units and the recipes. Re-run the same command, or
pull the clone; they do the same thing:

```bash
curl -fsSL https://raw.githubusercontent.com/wallacepnts/quadlet-homelab/main/bootstrap.sh | bash
```

It fast-forwards the clone and creates the links that are missing — one already
pointing at another clone is named, not moved. A clone that has diverged is left
alone and told about, so local edits are never dropped.

**The services on the host** — nothing moves until you say so. In the panel, an app with a
newer release shows an **Update to X** button, and My apps has **Update all** for the ones that
have something to take (each restarts; a failure does not stop the rest). A newer unit in the
repository does not change the file already installed. The same from a terminal:

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
  there, and 119 of the 127 units use it. On 4.x the start returns before the app
  is ready, and the install reports a success it cannot know about.
- **systemd with a user session** and cgroups v2.
- **`network-online.target` reached at boot.** Quadlet orders every unit it
  generates behind `podman-user-wait-network-online.service`, which loops on
  `until systemctl is-active network-online.target` until its 90s timeout. A
  target is only activated when something wants it, and desktops often want
  nothing — measured on Tumbleweed with KDE, where the one unit asking for it
  was a oneshot that had already finished. The dependency is `Wants=`, so the
  service does come up: ninety seconds late, on every single start.
  `sudo systemctl add-wants multi-user.target network-online.target` settles
  it, and the boot then waits for `NetworkManager-wait-online` — seconds when
  the machine has a network, `NM_ONLINE_TIMEOUT` when it does not.
- **SELinux**, if your distribution has it. The units carry `:Z` on 125 volume
  lines; where SELinux is absent those are ignored and nothing breaks, but the
  per-container isolation they ask for is not there either. The six units that
  mount Podman's socket need more than a label — `:z` alone leaves them healthy
  and blind, seeing no containers at all, so they declare
  `SecurityLabelType=container_runtime_t` (rule 16 of the conventions).
- `/dev/kvm` for the six VM services, and `/dev/net/tun` for those plus
  gluetun. Both are `0666` on a usual install, so rootless reaches them with no
  group change.
- `/dev/dri`, only for `vm-chromeos`, which passes the host GPU through. This
  one is `0660 root:render`, and it works without joining that group only
  because logind puts an ACL on it for the **active session**. A headless host
  running on `enable-linger` with no seat may not have that ACL, and the
  symptom is a container that starts and renders in software. Check it with
  `getfacl /dev/dri/renderD128` before blaming the image.

```bash
podman --version
systemctl is-active network-online.target
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

<!-- services:begin (generated from apps/*/app.json: python3 check.py --readme) -->

| Logo | Application | Description |
| --- | --- | --- |
| <img src="./apps/actual-budget/icon.svg" width="48" height="48" alt=""> | [Actual Budget](./apps/actual-budget) | A simple tool to plan and track your money. |
| <img src="./apps/adguardhome/icon.svg" width="48" height="48" alt=""> | [AdGuard Home](./apps/adguardhome) | Blocks ads and trackers on your whole network. |
| <img src="./apps/anki/icon.svg" width="48" height="48" alt=""> | [Anki](./apps/anki) | A sync server for your Anki flashcards. |
| <img src="./apps/any-sync-bundle/icon.svg" width="48" height="48" alt=""> | [any-sync-bundle](./apps/any-sync-bundle) | A sync server for the Anytype app. |
| <img src="./apps/audiobookshelf/icon.svg" width="48" height="48" alt=""> | [Audiobookshelf](./apps/audiobookshelf) | A server for your audiobooks and podcasts. |
| <img src="./apps/authentik/icon.svg" width="48" height="48" alt=""> | [Authentik](./apps/authentik) | A login and single sign-on server. |
| <img src="./apps/beaverhabits/icon.png" width="48" height="48" alt=""> | [Beaver Habits](./apps/beaverhabits) | A simple habit tracker. |
| <img src="./apps/beszel/icon.svg" width="48" height="48" alt=""> | [Beszel](./apps/beszel) | Shows how busy your server is. |
| <img src="./apps/calibre-web-automated/icon.svg" width="48" height="48" alt=""> | [Calibre-Web-Automated](./apps/calibre-web-automated) | Read and manage your ebook library in the browser. |
| <img src="./apps/casa/icon.svg" width="48" height="48" alt=""> | [CasaOS](./apps/casa) | A home server dashboard. |
| <img src="./apps/changedetection/icon.svg" width="48" height="48" alt=""> | [changedetection.io](./apps/changedetection) | Tells you when a web page changes. |
| <img src="./apps/collabora/icon.svg" width="48" height="48" alt=""> | [Collabora](./apps/collabora) | Edit documents in your browser. |
| <img src="./apps/cookcli/icon.svg" width="48" height="48" alt=""> | [CookCLI](./apps/cookcli) | Keep your recipes as plain text files. |
| <img src="./apps/copyparty/icon.svg" width="48" height="48" alt=""> | [Copyparty](./apps/copyparty) | A file server you can upload to from any device. |
| <img src="./apps/docuseal/icon.svg" width="48" height="48" alt=""> | [DocuSeal](./apps/docuseal) | Sign documents on your own server. |
| <img src="./apps/donetick/icon.svg" width="48" height="48" alt=""> | [Donetick](./apps/donetick) | Keep track of household chores. |
| <img src="./apps/dozzle/icon.svg" width="48" height="48" alt=""> | [Dozzle](./apps/dozzle) | Read your containers' logs in the browser. |
| <img src="./apps/excalidash/icon.svg" width="48" height="48" alt=""> | [ExcaliDash](./apps/excalidash) | A place to organize and share Excalidraw drawings. |
| <img src="./apps/faved/icon.svg" width="48" height="48" alt=""> | [Faved](./apps/faved) | A simple place to save bookmarks. |
| <img src="./apps/ferdium-server/icon.svg" width="48" height="48" alt=""> | [Ferdium Server](./apps/ferdium-server) | A sync server for the Ferdium app. |
| <img src="./apps/filebrowser/icon.svg" width="48" height="48" alt=""> | [FileBrowser Quantum](./apps/filebrowser) | A file manager in your browser. |
| <img src="./apps/fmd-server/icon.svg" width="48" height="48" alt=""> | [FMD Server](./apps/fmd-server) | Find your Android phone from the browser. |
| <img src="./apps/freshrss/icon.svg" width="48" height="48" alt=""> | [FreshRSS](./apps/freshrss) | Read all your news feeds in one place. |
| <img src="./apps/frigate/icon.svg" width="48" height="48" alt=""> | [Frigate](./apps/frigate) | A security camera recorder that spots people and objects. |
| <img src="./apps/ghost/icon.webp" width="48" height="48" alt=""> | [Ghost](./apps/ghost) | A blog and newsletter platform. |
| <img src="./apps/gitea/icon.svg" width="48" height="48" alt=""> | [Gitea](./apps/gitea) | A simple Git server for your code. |
| <img src="./apps/gitea-runner/icon.svg" width="48" height="48" alt=""> | [Gitea Runner](./apps/gitea-runner) | Runs the automated workflows of your Gitea. |
| <img src="./apps/grafana/icon.svg" width="48" height="48" alt=""> | [Grafana](./apps/grafana) | Charts and dashboards for your data. |
| <img src="./apps/headscale/icon.svg" width="48" height="48" alt=""> | [Headscale](./apps/headscale) | Your own server for a private network. |
| <img src="./apps/hermes-agent/icon.png" width="48" height="48" alt=""> | [Hermes Agent](./apps/hermes-agent) | A personal AI assistant. |
| <img src="./apps/home-assistant/icon.svg" width="48" height="48" alt=""> | [Home Assistant](./apps/home-assistant) | Control all your smart home devices in one place. |
| <img src="./apps/homebox/icon.svg" width="48" height="48" alt=""> | [HomeBox](./apps/homebox) | Keep an inventory of everything you own. |
| <img src="./apps/homepage/icon.png" width="48" height="48" alt=""> | [homepage](./apps/homepage) | A start page for your home server. |
| <img src="./apps/immich/icon.svg" width="48" height="48" alt=""> | [Immich](./apps/immich) | Back up and browse your photos and videos. |
| <img src="./apps/instagram-monitor/icon.svg" width="48" height="48" alt=""> | [Instagram Monitor](./apps/instagram-monitor) | Watches Instagram profiles and shows their activity. |
| <img src="./apps/invio/icon.svg" width="48" height="48" alt=""> | [Invio](./apps/invio) | Create and track invoices. |
| <img src="./apps/karakeep/icon.svg" width="48" height="48" alt=""> | [Karakeep](./apps/karakeep) | Save and search your bookmarks. |
| <img src="./apps/karaoke-eternal/icon.svg" width="48" height="48" alt=""> | [Karaoke Eternal](./apps/karaoke-eternal) | Run karaoke parties from your own songs. |
| <img src="./apps/kiwix/icon.svg" width="48" height="48" alt=""> | [Kiwix](./apps/kiwix) | Read Wikipedia and other libraries offline. |
| <img src="./apps/koffan/icon.png" width="48" height="48" alt=""> | [Koffan](./apps/koffan) | A shared shopping list. |
| <img src="./apps/komga/icon.svg" width="48" height="48" alt=""> | [Komga](./apps/komga) | Read your comics and manga. |
| <img src="./apps/lubelogger/icon.png" width="48" height="48" alt=""> | [LubeLogger](./apps/lubelogger) | Track maintenance for your vehicles. |
| <img src="./apps/mailpit/icon.svg" width="48" height="48" alt=""> | [Mailpit](./apps/mailpit) | Catches the emails your apps send so you can read them. |
| <img src="./apps/mdrop/icon.svg" width="48" height="48" alt=""> | [mdrop](./apps/mdrop) | Turn documents into Markdown. |
| <img src="./apps/media-stack/icon.svg" width="48" height="48" alt=""> | [Media Stack](./apps/media-stack) | A media server and the tools that fill it. |
| <img src="./apps/memos/icon.svg" width="48" height="48" alt=""> | [Memos](./apps/memos) | A simple place for quick notes. |
| <img src="./apps/metube/icon.svg" width="48" height="48" alt=""> | [MeTube](./apps/metube) | Download videos from the web. |
| <img src="./apps/monica/icon.svg" width="48" height="48" alt=""> | [Monica](./apps/monica) | Remember the people in your life. |
| <img src="./apps/n8n/icon.svg" width="48" height="48" alt=""> | [n8n](./apps/n8n) | Automate tasks between your apps. |
| <img src="./apps/neko/icon.svg" width="48" height="48" alt=""> | [neko](./apps/neko) | A shared browser you can use together. |
| <img src="./apps/netbootxyz/icon.svg" width="48" height="48" alt=""> | [netboot.xyz](./apps/netbootxyz) | Install an operating system over the network. |
| <img src="./apps/nginx/icon.svg" width="48" height="48" alt=""> | [nginx](./apps/nginx) | A web server for static files. |
| <img src="./apps/node-red/icon.svg" width="48" height="48" alt=""> | [Node-RED](./apps/node-red) | Automate things by connecting blocks. |
| <img src="./apps/ntfy/icon.svg" width="48" height="48" alt=""> | [ntfy](./apps/ntfy) | Send notifications to your phone. |
| <img src="./apps/omni-tools/icon.png" width="48" height="48" alt=""> | [Omni Tools](./apps/omni-tools) | Handy tools that run in your browser. |
| <img src="./apps/openwebui/icon.svg" width="48" height="48" alt=""> | [Open WebUI](./apps/openwebui) | A chat interface for AI models. |
| <img src="./apps/openwa/icon.svg" width="48" height="48" alt=""> | [OpenWA](./apps/openwa) | Send WhatsApp messages from your other apps. |
| <img src="./apps/owncloud/icon.svg" width="48" height="48" alt=""> | [ownCloud](./apps/owncloud) | Your own cloud for files. |
| <img src="./apps/owntracks/icon.svg" width="48" height="48" alt=""> | [OwnTracks](./apps/owntracks) | Track your location from your phone. |
| <img src="./apps/paperless-ngx/icon.svg" width="48" height="48" alt=""> | [Paperless-ngx](./apps/paperless-ngx) | Scan and search your paper documents. |
| <img src="./apps/pkvault/icon.svg" width="48" height="48" alt=""> | [PKVault](./apps/pkvault) | Manage your Pokémon save files. |
| <img src="./apps/postfix/icon.svg" width="48" height="48" alt=""> | [Postfix](./apps/postfix) | Sends email on behalf of your other apps. |
| <img src="./apps/postiz/icon.svg" width="48" height="48" alt=""> | [Postiz](./apps/postiz) | Schedule your social media posts. |
| <img src="./apps/prometheus/icon.svg" width="48" height="48" alt=""> | [Prometheus](./apps/prometheus) | Collects numbers about how your services run. |
| <img src="./apps/proxmox/icon.svg" width="48" height="48" alt=""> | [Proxmox VE](./apps/proxmox) | Try the Proxmox virtualization system. |
| <img src="./apps/radicale/icon.svg" width="48" height="48" alt=""> | [Radicale](./apps/radicale) | A calendar and contacts server. |
| <img src="./apps/rclone/icon.svg" width="48" height="48" alt=""> | [rclone](./apps/rclone) | Move files between your cloud accounts. |
| <img src="./apps/retrom/icon.webp" width="48" height="48" alt=""> | [Retrom](./apps/retrom) | A library for your retro games. |
| <img src="./apps/searxng/icon.png" width="48" height="48" alt=""> | [SearXNG](./apps/searxng) | Search the web without being tracked. |
| <img src="./apps/stirling-pdf/icon.svg" width="48" height="48" alt=""> | [Stirling-PDF](./apps/stirling-pdf) | Edit and convert PDF files. |
| <img src="./apps/syncthing/icon.svg" width="48" height="48" alt=""> | [Syncthing](./apps/syncthing) | Sync files between your devices. |
| <img src="./apps/toolbx/icon.png" width="48" height="48" alt=""> | [Toolbx](./apps/toolbx) | Throwaway Linux shells for trying things. |
| <img src="./apps/traccar/icon.svg" width="48" height="48" alt=""> | [Traccar](./apps/traccar) | Track vehicles and devices by GPS. |
| <img src="./apps/tsdproxy/icon.svg" width="48" height="48" alt=""> | [tsdproxy](./apps/tsdproxy) | Puts your apps on your tailnet automatically. |
| <img src="./apps/uptime-kuma/icon.svg" width="48" height="48" alt=""> | [Uptime Kuma](./apps/uptime-kuma) | Tells you when a service goes down. |
| <img src="./apps/vaultwarden/icon.png" width="48" height="48" alt=""> | [Vaultwarden](./apps/vaultwarden) | A password manager you host yourself. |
| <img src="./apps/vaultzap/icon.svg" width="48" height="48" alt=""> | [VaultZap](./apps/vaultzap) | Browse your exported WhatsApp chats. |
| <img src="./apps/vikunja/icon.svg" width="48" height="48" alt=""> | [Vikunja](./apps/vikunja) | A to-do list for tasks and projects. |
| <img src="./apps/vm/icon.svg" width="48" height="48" alt=""> | [VM](./apps/vm) | Run Windows, macOS and Linux in a container. |
| <img src="./apps/wger/icon.svg" width="48" height="48" alt=""> | [wger](./apps/wger) | Plan and track your workouts. |
| <img src="./apps/wud/icon.png" width="48" height="48" alt=""> | [WUD (What's Up Docker)](./apps/wud) | Tells you when your containers have updates. |
| <img src="./apps/zabbix/icon.svg" width="48" height="48" alt=""> | [Zabbix](./apps/zabbix) | Monitors your servers and network. |
| <img src="./apps/zerobyte/icon.png" width="48" height="48" alt=""> | [Zerobyte](./apps/zerobyte) | Backs up your apps' data. |
| <img src="./apps/zigbee2mqtt/icon.svg" width="48" height="48" alt=""> | [Zigbee2MQTT](./apps/zigbee2mqtt) | Use Zigbee devices without the maker's hub. |

<!-- services:end -->

**Nothing updates on its own.** Every image is pinned — to a version, or to a
digest where upstream publishes none — and updated by hand; see
[auto-update](./docs/auto-update.md).

## The network: Tailscale, Headscale or local only

The tailnet is part of the project, and one choice (asked by `bootstrap.sh`, changed in the panel under
**Settings → Network**, or with `qh --network`) says which:

| Choice | What you get |
| --- | --- |
| **Local only** | No tailnet. The apps open on their LAN port, tsdproxy is stopped. The simplest way. |
| **Tailscale** | The host joins a [Tailscale](https://tailscale.com) tailnet and tsdproxy gives each service its own HTTPS name, reachable from anywhere without opening a port. Vaultwarden needs it: it only decrypts the session in a secure context. |
| **Headscale** | A network of your own, with no account at a third party: the project runs [Headscale](https://headscale.net) (the `headscale` app), and the host and tsdproxy sign in to it. Headscale issues no HTTPS certificate, so the apps are served over HTTP on the tailnet (WireGuard still encrypts it) and the ones that insist on HTTPS (Vaultwarden, Actual) need the Tailscale choice. |

```bash
qh --network                                   # where things stand
qh --network local --apply
qh --network tailscale --apply
qh --network headscale --tailnet <your-tailnet> --apply     # --login-server URL if not the LAN address
```

The part that needs root on the host is only shown, never run: Tailscale is a host package (it has to *be* the
host on the network), so the plan prints what is missing, once —

```bash
sudo transactional-update pkg install tailscale     # an immutable host; then reboot
sudo systemctl enable --now tailscaled
sudo tailscale set --operator=$USER                  # lets the panel sign the host in, without root
```

— and everything else (the login, the Headscale server, its user and key, tsdproxy's secret and `controlUrl`, the
`TAILNET` of the units, updating the apps) is the plan's steps. Under Tailscale, tsdproxy asks for a reusable auth
key from the admin console; under Headscale the project makes it. Switching changes the apps' proxied port label
(an update, which keeps the data) and is reversible: `--network local` then `--network tailscale` is the way
back.

Without a tailnet, `qh --network local` sets the rule and stops tsdproxy; the lower-level rule alone is still
`qh --set-access local`, which comments the `tsdproxy.*` labels out instead of deleting them.

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
| [The app manifest](./docs/manifest.md) | `apps/<app>/app.json`: everything an app says about itself |
| [Auto-update](./docs/auto-update.md) | why nothing updates on its own |
| [Hardening, as measured](./docs/hardening.md) | what each image accepted, and the errors from what it refused |
| [Tools](./docs/tools.md) | `qh-check` and `qh-updates` |

All of it is also in Portuguese, in [`docs/pt-BR/`](./docs/pt-BR/).
