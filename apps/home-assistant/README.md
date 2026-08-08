# Home Assistant — Podman Quadlet (rootless)

**[🇧🇷 Leia em português](./README.pt-BR.md)**

Deploy do [Home Assistant Container](https://www.home-assistant.io/installation/alternative/)
via Podman Quadlet.

## This deploy's decisions

The official installation recommends `network_mode: host` + `privileged:
true` + access to the host's D-Bus, for automatic device discovery
(mDNS/SSDP — Hue, Chromecast, HomeKit...) e passthrough de hardware
(dongle Zigbee/Z-Wave via `/dev/ttyUSB0`). Nenhum dos dois foi usado
here, on purpose:

- **An ordinary bridge network** (`PublishPort=8123:8123`), not `host`. It
  loses automatic mDNS/SSDP discovery — devices have to be added by hand
  through the UI (Settings → Devices and services). In exchange, it keeps the
  same network isolation everything else here has; `host` would put HA
  literally on the host's network, outside the pattern used here.
- **Sem dispositivo USB passado** — sem dongle Zigbee/Z-Wave neste setup
  for now. If one ever arrives, see the dedicated section below for
  adicionar via `AddDevice=`.
- **No D-Bus/Bluetooth** — the same logic; an integration over the host's
  Bluetooth does not work without it, but it is not needed for current use.

A visible, harmless consequence in the log: `Cannot watch for dhcp
packets: Operation not permitted` — o watcher de DHCP (mais um
another automatic discovery mechanism, via passive DHCP packets) requires
`CAP_NET_RAW`, which a bridge network without privileged does not grant. It
does not stop HA working, it is just one more automatic discovery avenue left
without effect — consistent with the decision above.

If any of those three ever comes up (mDNS, USB, Bluetooth), the solution
mais simples costuma ser `network_mode: host` mesmo — tentar replicar
mDNS discovery through a bridge is fragile (it would need an mDNS proxy
tipo `avahi`/[repeater](https://github.com/dmitrykim/mdns-repeater), sem
official HA support). Reassess then.

## Architecture

A single container, on the official image (Debian + Python). A single volume
(`/config`) holds the entire configuration, the automations, the state history
(an embedded SQLite database by default) and the logs.

## Files

```
home-assistant.container   # main unit
```

## Prerequisites

- Rootless Podman with systemd `--user` working

## Installation

```bash
python3 install.py home-assistant            # dry-run: shows what it will do
python3 install.py home-assistant --apply
```

For the local network only, `--access local`; on the tailnet and the LAN,
`--access both`. Adding `--href-local` points the dashboard link at the LAN.
The script creates the directories, writes the `.env`, generates the secrets,
fixes the volumes' ownership, starts the service and prints the address at the
end — see [Installing and operating](../../docs/installing.md).

Reach it through [tsdproxy](../tsdproxy/) (tailnet) at
`https://home-assistant.<your-tailnet>.ts.net`, or locally at
`http://localhost:8123` — the root redirects to the installation wizard the
first time (create an account, name the location, choose units, and so on).

<details>
<summary><b>Manual installation</b> (advanced) — the same steps, one at a time</summary>


```bash
# 1. Download the unit (no need to clone the repository)
mkdir -p ~/.config/containers/systemd
wget -P ~/.config/containers/systemd/ \
  https://raw.githubusercontent.com/wallacepnts/quadlet-homelab/main/apps/home-assistant/home-assistant.container

# 2. Data directory — a bind mount requires it to exist before the start
mkdir -p ~/.config/containers/volumes/home-assistant/config

# 3. Env — baixar o exemplo
mkdir -p ~/.config/containers/env
wget -O ~/.config/containers/env/home-assistant.env \
  https://raw.githubusercontent.com/wallacepnts/quadlet-homelab/main/apps/home-assistant/.env.example

# 4. Start it
systemctl --user daemon-reload
systemctl --user start home-assistant
```

Reach it through [tsdproxy](../tsdproxy/) (tailnet) at
`https://home-assistant.<your-tailnet>.ts.net`, or locally at
`http://localhost:8123` — the root redirects to the installation wizard the
first time (create an account, name the location, choose units, and so on).

**Trusted proxies — genuinely required, not an "in case it happens".** When
reached through tsdproxy (a reverse proxy), HA refuses the connection with
`400: Bad Request` and logs `A request from a reverse proxy was received from
169.254.1.2, but your HTTP integration is not set-up for reverse proxies`.
`169.254.1.2` is rootless Podman's internal gateway (via pasta — the same
address behind `host.containers.internal`, see [zerobyte](../zerobyte/) for
another case where it turns up), and it is where tsdproxy's traffic arrives
from. Add this to
`~/.config/containers/volumes/home-assistant/config/configuration.yaml`
**before** trying to reach it over the tailnet, then `systemctl --user restart
home-assistant`:

```yaml
http:
  use_x_forwarded_for: true
  trusted_proxies:
    - 169.254.1.2
```

</details>

## Adding a USB device (Zigbee/Z-Wave) later

```ini
AddDevice=/dev/ttyUSB0
```

Check the real path with `ls -la /dev/serial/by-id/` on the host (more
stable than `/dev/ttyUSB0`, whose number can change between boots) and use
that instead. Without `--privileged` or host networking, that should already
be enough for the dongle to appear inside the container — test it before
re-enabling `network_mode: host`.

## Auto-update

No `AutoUpdate=` — an explicit tag (`2026.8.0`), bumped by hand
(rule 9 of the [conventions](../../docs/conventions.md)). HA's releases are monthly and sometimes bring *breaking changes* documented
in the release notes (a discontinued integration, a config change) — review by
hand before changing version, the same
cautela do [immich](../immich/).

## Backup & recovery

```bash
systemctl --user stop home-assistant
tar -czf home-assistant-backup-$(date +%Y%m%d-%H%M%S).tar.gz \
  -C ~/.config/containers/volumes home-assistant
systemctl --user start home-assistant
```

HA also has a built-in backup in the UI (Settings → System → Backups) — more
practical day to day (it does not require stopping the container); the tar
above is the "cold" equivalent for when the UI is not enough or the container
no longer starts.

## Useful commands

```bash
systemctl --user status home-assistant
podman logs -f home-assistant
```

## Credits

Quadlet deploy based on [Home Assistant](https://github.com/home-assistant/core).
Original licence: Apache-2.0.
