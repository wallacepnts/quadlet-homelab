# netboot.xyz — Podman Quadlet (rootless)

**[🇧🇷 Leia em português](./README.pt-BR.md)**

Deploy do [netboot.xyz](https://netboot.xyz/) (menu de boot pela rede — PXE
— pra instalar/testar distros e ferramentas sem precisar de pendrive) via
Podman Quadlet, using the official image
[netbootxyz/docker-netbootxyz](https://github.com/netbootxyz/docker-netbootxyz).

## Architecture

A single container (Alpine + nginx + Node.js + dnsmasq/TFTP), with three
internal services:

- **TFTP** (`69/udp`) — serves the bootloaders
  (`netboot.xyz.kpxe`/`.efi`) to the clients' PXE firmware.
- **nginx** (internal `80`, `NGINX_PORT`) — serves the downloaded assets
  (kernels, initrds, ISOs) the menu loads after the initial boot.
- **The web app** (internal `3000`, `WEB_APP_PORT`) — the menu/asset
  configuration UI.

Volumes:
- `/config` — the menu's persistent configuration
- `/assets` — a cache of downloaded assets (kernels, initrds) — optional;
  without it the assets are downloaded again at every boot

**Important**: TFTP and nginx are for PXE clients on the **LAN**, before they
have an operating system — they are not Tailscale nodes, so they are not part
of the tailnet. [tsdproxy](../tsdproxy/) here only publishes the configuration
web UI (port 3000); ports 69 and 8089 have to be reachable directly on the
host's LAN IP.

## Files

```
netbootxyz.container   # main unit
```

## Prerequisites

- Rootless Podman with systemd `--user` working
- **Port 69/UDP is privileged (<1024)** — rootless cannot publish it without
  adjusting the kernel's unprivileged port floor:
  ```bash
  sudo sysctl -w net.ipv4.ip_unprivileged_port_start=69
  ```
  Tested in practice: without it, `podman run -p 69:69/udp` fails with
  `pasta failed ... Listen failed for HOST UDP port */69: Permission denied`.
  To make it survive reboots:
  ```bash
  echo 'net.ipv4.ip_unprivileged_port_start=69' | sudo tee /etc/sysctl.d/99-netbootxyz-tftp.conf
  ```
- **An external DHCP server already configured** — this container does
  **not** provide DHCP, only TFTP/HTTP. The network's DHCP server (a router,
  pfSense, your own dnsmasq and so on) has to point the PXE clients at this
  host:
  - Option 66 (`next-server`): this host's LAN IP
  - Option 67 (`filename`): `netboot.xyz.kpxe` (BIOS) or `netboot.xyz.efi`
    (UEFI) — the web panel itself shows the exact value
  - Without that step the clients never even make the TFTP request — there is
    no error in the container's log, the request simply never arrives.
- Ports 69/UDP and 8089/TCP opened in the host's firewall **for the LAN**, not
  only for the tailnet ([rule 10](../../docs/conventions.md) —
  `PublishPort=` does not open the firewall on its own).

## Installation

```bash
python3 install.py netbootxyz            # dry-run: shows what it will do
python3 install.py netbootxyz --apply
```

For the local network only, `--access local`; on the tailnet and the LAN,
`--access both`. Adding `--href-local` points the dashboard link at the LAN.
The script creates the directories, writes the `.env`, generates the secrets,
fixes the volumes' ownership, starts the service and prints the address at the
end — see [Installing and operating](../../docs/installing.md).



<details>
<summary><b>Manual installation</b> (advanced) — the same steps, one at a time</summary>


```bash
# 1. Download the unit (no need to clone the repository)
mkdir -p ~/.config/containers/systemd
wget -P ~/.config/containers/systemd/ \
  https://raw.githubusercontent.com/wallacepnts/quadlet-homelab/main/apps/netbootxyz/netbootxyz.container

# 2. Data directories — a bind mount requires them to exist before the start
mkdir -p ~/.config/containers/volumes/netbootxyz/{config,assets}

# 3. Non-secret env
mkdir -p ~/.config/containers/env
wget -O ~/.config/containers/env/netbootxyz.env \
  https://raw.githubusercontent.com/wallacepnts/quadlet-homelab/main/apps/netbootxyz/.env.example

# 4. Start it
systemctl --user daemon-reload
systemctl --user start netbootxyz
```

The configuration UI through [tsdproxy](../tsdproxy/) (tailnet) at
`https://netbootxyz.<your-tailnet>.ts.net`, or locally at
`http://localhost:8088`. The assets live at `http://<lan-ip>:8089/` (used
internally by the menu; there is no need to open it directly).

Once DHCP is configured (see Prerequisites), a PXE client on the same LAN
lands straight in the netboot.xyz menu when it boots.

</details>

## Auto-update

No `AutoUpdate=` — an explicit tag (`0.7.6-nbxyz23`), bumped by hand
([rule 9](../../docs/conventions.md)). The image has `curl` and a real
healthcheck (it could be enabled with genuine rollback), but the boot
loader/menu itself (`/config`) is sensitive to the webapp's version changes —
checking the changelog before changing tag is preferred. `wud.watch=true`
stays on purely for passive visibility (see [wud](../wud/)).

Worth noting: `MENU_VERSION` (if set) and the contents of `/assets` are
updated independently of the image tag — netboot.xyz's menu builder fetches
the latest menu version at every start by default, and that is not controlled
by Podman's `AutoUpdate=`.

**`wud.tag.transform` is required**: a known WUD bug with numeric build
suffixes ([getwud/wud#566](https://github.com/getwud/wud/issues/566)) —
`0.7.6-nbxyz9` is lexically "higher" than `0.7.6-nbxyz23` in the semver
prerelease comparison (it compares as a string, not as a number), producing a
false update pointing at an **older** version. Zero-pad the single-digit
suffix only, leaving 2+ digit tags untouched (tested — confirmed via `podman
inspect` that the `$` survives without doubling; only the `$1` capture group
needs `$$`, [rule 7](../../docs/conventions.md)):
```ini
Label=wud.tag.transform="nbxyz([0-9])$ => nbxyz0$$1"
```

## Backup & recovery

```bash
systemctl --user stop netbootxyz
tar -czf netbootxyz-backup-$(date +%Y%m%d-%H%M%S).tar.gz \
  -C ~/.config/containers/volumes netbootxyz
systemctl --user start netbootxyz
```

`/assets` is only a cache (rebuildable by downloading again) — it can be
excluded from the backup for something smaller, keeping just `/config`.

## Useful commands

```bash
systemctl --user status netbootxyz
podman logs -f netbootxyz
```

## Credits

Deploy Quadlet usando a imagem oficial
[netbootxyz/docker-netbootxyz](https://github.com/netbootxyz/docker-netbootxyz)
(MIT), do projeto [netboot.xyz](https://netboot.xyz/).
