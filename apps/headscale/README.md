# Headscale

<img src="https://cdn.jsdelivr.net/gh/homarr-labs/dashboard-icons/svg/headscale.svg" width="64" height="64" alt="">

**[🇧🇷 Leia em português](./README.pt-BR.md)**

An open implementation of the Tailscale control plane: the part that hands out
keys, decides who may talk to whom, and answers MagicDNS. The same clients,
coordinated by your own server instead of a company's.

It is a server, not a network identity — which is why it is a container here
while `tailscaled` stays installed on the host. The client is what creates the
interface and speaks WireGuard; this only tells it who else exists.

## Install

```bash
qh headscale            # shows the plan
qh headscale --apply
```

Then edit `~/.config/containers/volumes/headscale/config/config.yaml` —
`server_url` has to be the address the clients will reach, and it has to be
HTTPS — and restart with `qh headscale --update --apply`.

Create a user and a key, then point a client at it:

```bash
podman exec headscale headscale users create casa
podman exec headscale headscale preauthkeys create --user casa --expiration 24h

# on the client machine
sudo tailscale up --login-server https://headscale.casa --authkey <key>
```

<details>
<summary><b>Manual install (advanced)</b></summary>

```bash
mkdir -p ~/.config/containers/systemd
mkdir -p ~/.config/containers/volumes/headscale/{config,data}

wget -P ~/.config/containers/systemd/ \
  https://raw.githubusercontent.com/wallacepnts/quadlet-homelab/main/apps/headscale/headscale.container
wget -O ~/.config/containers/volumes/headscale/config/config.yaml \
  https://raw.githubusercontent.com/wallacepnts/quadlet-homelab/main/apps/headscale/config/config.yaml

# The container runs as uid 1000, which is not yours after the mapping
podman unshare chown -R 1000:1000 ~/.config/containers/volumes/headscale

systemctl --user daemon-reload
systemctl --user start headscale
```

</details>

## Files

```
headscale.container   unit
config/config.yaml    the configuration, into the volume
install.ini
```

`data/` holds `db.sqlite` and `noise_private.key`. That key is the server's
identity: lose it and every client has to register again. SQLite is the
project's own default, so there is no second container for a database.

## What this repository changed in the config

The file is headscale's own example with four lines different, and they are
marked at the top of it:

- **`server_url`** — the address clients are pointed at. It must be reachable
  from wherever your devices are, and it must be HTTPS.
- **`listen_addr: 0.0.0.0:8080`** — the example binds `127.0.0.1`, which
  inside a container means nothing outside it can connect.
- **`metrics_listen_addr`** — same reason.
- **`base_domain: casa`** — what MagicDNS appends, so a node answers to
  `laptop.casa`.

The TLS lines are left empty on purpose: [Caddy](../caddy) terminates it in
front, and a server behind a proxy should not be running ACME of its own.

## The part that is not in this repository

Clients have to reach `server_url` **from anywhere**, not only from your LAN.
That means a public address and an open port, or headscale on a VPS. Without
it, devices coordinate at home and nowhere else, which is most of the value
gone.

The relays are the other half: with `derp.server.enabled: false`, as it ships,
NAT traversal falls back to Tailscale's public DERP servers. It works and it
carries no traffic in the clear, but it is still their infrastructure. Turning
on the embedded DERP makes it yours, and needs a reachable UDP port too.

## Hardening

The whole ladder: `ReadOnly=true`, every capability dropped, and `User=1000`.
Measured with the server actually answering — `/health` returning
`{"status":"pass"}` and the database written to the volume.

`/var/run/headscale` is a tmpfs because headscale opens a unix socket there
for its own CLI, and the root filesystem is read-only.

## Update

```bash
qh headscale --update --apply
```

Pinned to `v0.29.3`. Read the release notes before bumping: this is the piece
every device depends on to find every other device.

## Backup

```bash
qh headscale --backup --apply --out ~/backups
```

Stops it, packs the database, the noise key and the config, starts it again.

To restore, over the current data:

```bash
qh headscale --restore ~/backups/headscale-20260811-1200.tar.gz --apply
```

## Remove

```bash
qh headscale --remove --apply           # stops it, keeps the tailnet
qh headscale --remove --purge --apply   # and deletes the database and the key
```

`--purge` ends the tailnet: every client would have to register against a new
server.

## Commands

```bash
systemctl --user status headscale
podman logs -f headscale

podman exec headscale headscale nodes list
podman exec headscale headscale users list
```

## Credits

[juanfont/headscale](https://github.com/juanfont/headscale) — BSD-3-Clause.
Not affiliated with Tailscale Inc.

[Official documentation](https://headscale.net/)
