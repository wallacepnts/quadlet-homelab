# homepage — Podman Quadlet (rootless)

**[🇧🇷 Leia em português](./README.pt-BR.md)**

A [Homepage](https://gethomepage.dev) deploy via Podman Quadlet — a
dashboard that discovers and displays other containers automatically, through
labels, with no `services.yaml` to edit by hand for each service.

## Architecture

Homepage reads the Podman socket (via `podman.socket`, the same mechanism
[tsdproxy](../tsdproxy/) already uses) purely to list containers and labels —
**read-only** access (`:ro`). Any container with `Label=homepage.group=...`
(the bare minimum) shows up on the dashboard automatically; no manual
`services.yaml` entry is needed when using labels.

## Files

```
homepage.container   # main unit

config/
├── docker.yaml           # defines the discovery source (the Podman socket)
└── settings.yaml         # statusStyle: dot (a status dot instead of text)
```

## Prerequisites

- Rootless Podman with systemd `--user` working
- `podman.socket` enabled (already required if [tsdproxy](../tsdproxy/) is
  installed — the same socket, reused)

## Installation

```bash
python3 install.py homepage            # dry-run: shows what it will do
python3 install.py homepage --apply
```

For the local network only, `--access local`; on the tailnet and the LAN,
`--access both`. Adding `--href-local` points the dashboard link at the LAN.
The script creates the directories, writes the `.env`, generates the secrets,
fixes the volumes' ownership, starts the service and prints the address at the
end — see [Installing and operating](../../docs/installing.md).

Open it at `http://localhost:3000` or, over the tailnet, at
`https://homepage.<your-tailnet>.ts.net` (the `.container` already ships the
[tsdproxy](../tsdproxy/) labels — its own node is created automatically, like
any-sync-bundle's).

<details>
<summary><b>Manual installation</b> (advanced) — the same steps, one at a time</summary>


```bash
# 1. Download the unit (no need to clone the repository)
mkdir -p ~/.config/containers/systemd
wget -P ~/.config/containers/systemd/ \
  https://raw.githubusercontent.com/wallacepnts/quadlet-homelab/main/apps/homepage/homepage.container

# 2. Config — it has to exist before the start; if the folder is empty
#    Homepage generates the rest itself the first time (bookmarks.yaml etc.)
mkdir -p ~/.config/containers/volumes/homepage/config
wget -P ~/.config/containers/volumes/homepage/config/ \
  https://raw.githubusercontent.com/wallacepnts/quadlet-homelab/main/apps/homepage/config/docker.yaml \
  https://raw.githubusercontent.com/wallacepnts/quadlet-homelab/main/apps/homepage/config/settings.yaml

# 2b. Custom icons (optional) — this only needs to exist if you use them,
#     see "Marking a service" below
mkdir -p ~/.config/containers/volumes/homepage/icons

# 3. Env — download the example. HOMEPAGE_ALLOWED_HOSTS is mandatory (a
#    Host-header allowlist, in host:port form; it accepts several,
#    comma-separated). The .container already ships tsdproxy labels (a
#    "homepage" node on the tailnet), so include the MagicDNS hostname here
#    too, otherwise Homepage rejects the requests coming from tsdproxy with
#    "Host not allowed".
mkdir -p ~/.config/containers/env
wget -O ~/.config/containers/env/homepage.env \
  https://raw.githubusercontent.com/wallacepnts/quadlet-homelab/main/apps/homepage/.env.example
# edit ~/.config/containers/env/homepage.env: HOMEPAGE_ALLOWED_HOSTS

# 4. The Podman socket
systemctl --user enable --now podman.socket

# 5. Start it
systemctl --user daemon-reload
systemctl --user start homepage

# 6. Auto-update (see the dedicated section below) — a daily timer, shared
#    with any other service on this host that also uses AutoUpdate=
systemctl --user enable --now podman-auto-update.timer
```

Open it at `http://localhost:3000` or, over the tailnet, at
`https://homepage.<your-tailnet>.ts.net` (the `.container` already ships the
[tsdproxy](../tsdproxy/) labels — its own node is created automatically, like
any-sync-bundle's).

</details>

## Marking a service to appear on the dashboard

In any `.container` (from this repo or not), add `homepage.*` labels — purely
opt-in; a container without those labels simply does not show up:

```ini
Label=homepage.group=Category
Label=homepage.name="Displayed name"
Label=homepage.icon=si-icon-name
Label=homepage.href=http://address:port
Label=homepage.description="A short description"
```

Values with a space need quotes (`Label=key="value with a space"`) — without
them Quadlet truncates at the first space, with no error and no warning
([rule 12](../../docs/conventions.md)).

**`href`: `localhost` only works when viewing the dashboard locally.** If
Homepage is also reached from another device (through tsdproxy/tailnet, see
above), `http://localhost:port` points at the viewer's own device, not at the
server — the link simply opens nothing. If the service is also exposed on the
tailnet, use that address instead of (or as well as) `localhost`:

```ini
Label=homepage.href=https://<service-name>.<your-tailnet>.ts.net
```

**`${TAILNET}` is an `environment.d` variable, set once for the whole host**
([rule 19](../../docs/conventions.md)) — every `.container` in this repo uses
it instead of the real name, because the repo is public. Set it before
starting any service:

```bash
mkdir -p ~/.config/environment.d
echo "TAILNET=$(tailscale status --json | jq -r '.MagicDNSSuffix' | cut -d. -f1)" \
  > ~/.config/environment.d/tailnet.conf
systemctl --user daemon-reload   # mandatory: the manager has to re-read the environment
```

Tested in practice: the expansion works in `Label=` just as it does in
`Volume=`, and the real value shows up in the container
(`podman inspect <app> --format '{{index .Config.Labels "homepage.href"}}'`
confirms it; `systemctl cat` shows a literal `${TAILNET}`, which is expected).

**If `TAILNET` is not set, it expands to an empty string** and the link
becomes `https://app..ts.net` — broken, with no error whatsoever in the log.
The effect is indirect and annoying: the dashboard card does not open, and the
reflex becomes reaching it at `http://<host-ip>:<port>`. For most services
that is merely inconvenient, but on [vaultwarden](../vaultwarden/) it really
breaks the login — the browser only allows WebCrypto over HTTPS or on
`localhost`, and the Bitwarden client fails with "your access token could not
be decrypted" (it happened here, back when the placeholder was still literal).

An example: this repo's `tsdproxy.container` uses
`homepage.href=http://localhost:8080`, which only works locally. tsdproxy
itself already creates a `dash` node on the tailnet for its own dashboard —
changing it to `homepage.href=https://dash.<your-tailnet>.ts.net` would make
the link work from any device.

`icon` accepts `name.png`/`.svg` (the
[dashboard-icons](https://github.com/homarr-labs/dashboard-icons) library),
`mdi-name` (Material Design Icons), `si-name` (Simple Icons) or an absolute
URL. Always include the extension explicitly (`radicale.svg`, not `radicale`)
— without it, Homepage specifically tries `.png` (it does not "detect the best
format"), and if only `.svg` exists the icon breaks.

**`si-`/`mdi-` render differently from `dashboard-icons`.** The prefixed ones
(`si-`/`mdi-`) become a **single-colour CSS mask** (a gradient by default, or
the theme's colour if `iconStyle: theme` is set in `settings.yaml`) — they do
not show the original image. "Loose" dashboard-icons entries
(`name.svg`/`.png`) show the original artwork, with its real colours. Prefer
dashboard-icons where an equivalent exists (check whether `name.svg` answers
before falling back to `si-`/`mdi-`), to keep the cards looking consistent.
Examples already in use here:
[`any-sync-bundle.container`](../any-sync-bundle/any-sync-bundle.container)
(`anytype.svg`, with no `href` — it is not a browsable HTTP service) and
[`tsdproxy.container`](../tsdproxy/tsdproxy.container) (`tailscale.svg`).

**A custom icon, with no equivalent in dashboard-icons/`si-`/`mdi-`:** put the
file in `~/.config/containers/volumes/homepage/icons/` and reference it as
`Label=homepage.icon=/icons/<file>` (`/icons/my-service.png`, say). Homepage
itself has to be restarted after adding a new icon — a limitation of Next.js's
static server, which does not detect a new file on its own (unlike container
labels, which are picked up live).

After adding labels to an existing container: `systemctl --user daemon-reload
&& systemctl --user restart <name>` — Homepage notices the updated container
by itself, there is no need to restart Homepage.

## Auto-update

Unlike any-sync-bundle, the image is Alpine with `wget` available — a real
`HealthCmd`, so `AutoUpdate=registry` has genuine automatic rollback (see
[rule 9](../../docs/conventions.md)). **On by default** in this repo:
`Image=...:latest` + `AutoUpdate=registry` in the `.container`, with
`podman-auto-update.timer` (daily) handling the rest — the same pattern as
[actual-budget](../actual-budget/). Check the candidates before trusting it
blindly: `podman auto-update --dry-run`.

## Useful commands

```bash
systemctl --user status homepage
podman logs -f homepage
```

## Credits

Quadlet deploy based on [Homepage](https://github.com/gethomepage/homepage).
Original licence: GPL-3.0.
