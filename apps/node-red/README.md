# Node-RED — Podman Quadlet (rootless)

**[🇧🇷 Leia em português](./README.pt-BR.md)**

A [Node-RED](https://nodered.org) (flow automation through a visual node
editor — it connects APIs, devices and services without programming from
scratch) deploy via Podman Quadlet, using the official
[`nodered/node-red`](https://hub.docker.com/r/nodered/node-red)
image (the minimal variant).

## Architecture

A single container, running with a **fixed `node-red` uid (1000) and no
internal usermod** — tested in practice: without `UserNS=keep-id` it hangs
right at start with `EACCES: permission denied` while trying to copy the
default `settings.js` into the volume. The same case as
[Immich](../immich/) (an image with a fixed uid and no chown of its own needs
`UserNS=keep-id`; most of the other images here do an internal usermod and so
do not).

A single volume (`/data`) — it holds the flows, the config (`settings.js`,
copied automatically from the image on the first start), the node_modules of
extra nodes installed through the palette, and the credential encryption key.

**The credential key is generated and saved automatically** — on the first
start, Node-RED creates a random `_credentialSecret` and writes it to
`data/.config.runtime.json`, tested in practice. Since `data/` is persisted,
that key survives an ordinary restart (unlike
[Monica](../monica/)/[Authentik](../authentik/), which need a secret of their
own to prevent this) — no extra manual step is needed, but you can pin your
own via `credentialSecret` in `settings.js` if you prefer to control it
explicitly.

**No authentication of its own by default** — the same trust model already
used by [WUD](../wud/)/[Homepage](../homepage/) here: protected only by being
on the tailnet, not by a login. `adminAuth` can be enabled in `settings.js`
later if you want.

## Files

```
node-red.container       # main unit
```

## Prerequisites

- Rootless Podman with systemd `--user` working

## Installation

```bash
python3 install.py node-red            # dry-run: shows what it will do
python3 install.py node-red --apply
```

For the local network only, `--access local`; on the tailnet and the LAN,
`--access both`. Adding `--href-local` points the dashboard link at the LAN.
The script creates the directories, writes the `.env`, generates the secrets,
fixes the volumes' ownership, starts the service and prints the address at the
end — see [Installing and operating](../../docs/installing.md).

Open `http://<host-ip>:1880` (or through [tsdproxy](../tsdproxy/) at
`https://node-red.<your-tailnet>.ts.net`) — it opens straight into the editor,
with no login screen (see "No authentication of its own" above).

<details>
<summary><b>Manual installation</b> (advanced) — the same steps, one at a time</summary>


```bash
# 1. Download the units (no need to clone the repository)
mkdir -p ~/.config/containers/systemd
wget -P ~/.config/containers/systemd/ \
  https://raw.githubusercontent.com/wallacepnts/quadlet-homelab/main/apps/node-red/node-red.container

# 2. Data directory — a bind mount requires it to exist before the start
mkdir -p ~/.config/containers/volumes/node-red/data

# 3. Non-secret env
mkdir -p ~/.config/containers/env
wget -O ~/.config/containers/env/node-red.env \
  https://raw.githubusercontent.com/wallacepnts/quadlet-homelab/main/apps/node-red/.env.example

# 4. Start it
systemctl --user daemon-reload
systemctl --user start node-red
```

Open `http://<host-ip>:1880` (ou via [tsdproxy](../tsdproxy/) em
`https://node-red.<your-tailnet>.ts.net`) — abre direto no editor, sem
with no login screen (see "No authentication of its own" above).

</details>

## Auto-update

No `AutoUpdate=` — an explicit tag (`5.0.4-minimal`), bumped by hand
([rule 9](../../docs/conventions.md)). The image has `wget`/`curl` and a real
healthcheck — `AutoUpdate=registry` could be enabled with working rollback,
but flows and credentials are the user's real data, so review by hand before
updating (palette nodes installed manually may also not be compatible with
every new version).

## Backup & recovery

```bash
systemctl --user stop node-red
tar -czf node-red-backup-$(date +%Y%m%d-%H%M%S).tar.gz \
  -C ~/.config/containers/volumes node-red
systemctl --user start node-red
```

`data/.config.runtime.json` (the credential key) has to be in that backup —
without it, credentials saved in flows that use authenticated nodes (APIs,
databases and so on) become unreadable.

## Useful commands

```bash
systemctl --user status node-red
podman logs -f node-red
podman exec node-red wget -qO- http://127.0.0.1:1880/
```

## Credits

Quadlet deploy based on
[Node-RED](https://github.com/node-red/node-red) (Apache-2.0).
