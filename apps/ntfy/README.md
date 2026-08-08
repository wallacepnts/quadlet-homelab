# ntfy — Podman Quadlet (rootless)

**[🇧🇷 Leia em português](./README.pt-BR.md)**

An [ntfy](https://github.com/binwiederhier/ntfy) (push notification server)
deploy via Podman Quadlet, using the official
`docker.io/binwiederhier/ntfy` image.

## Why it exists here

This repository has three services whose job is to *tell you about
something* — [uptime-kuma](../uptime-kuma/) (a service went down),
[wud](../wud/) (a new image is available) and [zerobyte](../zerobyte/) (a
backup failed) — and until now none of them had anywhere to send the alert.
All three support ntfy natively. See "Wiring up the alerts" below.

On the phone side, the ntfy app subscribes to the topics and receives push
without depending on a third-party server (not even FCM, if you use the F-Droid
build).

## Architecture

A single container, Go, with embedded SQLite. Two volumes:

| Volume | What for |
| --- | --- |
| `/var/cache/ntfy` | the message cache (`cache.db`) and attachments |
| `/var/lib/ntfy` | the user and permission database (`user.db`) |

**It is the most hardened service in the repository**, alongside
[uptime-kuma](../uptime-kuma/) e [homebox](../homebox/): `ReadOnly=true`,
`DropCapability=ALL` e `User=1000`.

### The trick that avoided a capability

By default ntfy listens on **port 80 inside the container**, and a port <1024
requires `NET_BIND_SERVICE` — exactly [vaultwarden](../vaultwarden/)'s case,
which needs that capability for this reason. Here, `NTFY_LISTEN_HTTP=:2586`
moves the listener to a high port and the need disappears: the container runs
with **zero** capabilities.

It holds as a general method
([conventions, rule 20](../../docs/conventions.md)): before granting a
capability, see whether the need for it can be removed.

## Security: the server starts out open

With no configuration, **anyone who reaches the port publishes to and
subscribes to any topic**. An open notification server is a spam relay waiting
to happen.

The unit already ships `NTFY_AUTH_DEFAULT_ACCESS=deny-all`, tested in
practice: an anonymous request gets a `403`, and only a user created with
`ntfy user add` gets through. The users are **imperative**, like this
repository's `podman secret` entries — do not version them; create them in
step 4 of the installation.

## Files

```
ntfy.container   # main unit
.env.example     # the canonical URL, retention and attachment limits
```

## Prerequisites

- Rootless Podman with systemd `--user` working

## Installation

```bash
python3 install.py ntfy            # dry-run: shows what it will do
python3 install.py ntfy --apply
```

For the local network only, `--access local`; on the tailnet and the LAN,
`--access both`. Adding `--href-local` points the dashboard link at the LAN.
The script creates the directories, writes the `.env`, generates the secrets,
fixes the volumes' ownership, starts the service and prints the address at the
end — see [Installing and operating](../../docs/installing.md).

Open `http://<host-ip>:8098` (or through [tsdproxy](../tsdproxy/) at
`https://ntfy.<your-tailnet>.ts.net`).

<details>
<summary><b>Manual installation</b> (advanced) — the same steps, one at a time</summary>


```bash
# 1. Download the unit (no need to clone the repository)
mkdir -p ~/.config/containers/systemd
wget -P ~/.config/containers/systemd/ \
  https://raw.githubusercontent.com/wallacepnts/quadlet-homelab/main/apps/ntfy/ntfy.container

# 2. Directories, with the owner matching the unit's User=1000.
#    `podman unshare` runs the chown INSIDE the user namespace, which is
#    where the container's 1000 exists (on the host that becomes 100999).
mkdir -p ~/.config/containers/volumes/ntfy/{cache,lib}
podman unshare chown -R 1000:1000 ~/.config/containers/volumes/ntfy

# 3. Variables — set NTFY_BASE_URL to your own tailnet domain
mkdir -p ~/.config/containers/env
wget -O ~/.config/containers/env/ntfy.env \
  https://raw.githubusercontent.com/wallacepnts/quadlet-homelab/main/apps/ntfy/.env.example

# 4. Start it
systemctl --user daemon-reload
systemctl --user start ntfy

# 5. Create the administrator user (imperative, not versioned). The
#    password goes through an environment variable so it stays out of the
#    shell history.
read -rs NTFY_PASSWORD && export NTFY_PASSWORD
podman exec -e NTFY_PASSWORD ntfy ntfy user add --role=admin admin
unset NTFY_PASSWORD
```

Open `http://<host-ip>:8098` (or through [tsdproxy](../tsdproxy/) at
`https://ntfy.<your-tailnet>.ts.net`).

**`NTFY_BASE_URL` matters.** ntfy builds attachment and web push links from
it; pointing it at IP:port means those links do not open from outside the
host. Use the tailnet address.

</details>

## Testing

```bash
# should give 403 — a closed server, as expected
curl -s -o /dev/null -w '%{http_code}\n' -d test http://127.0.0.1:8098/alerts

# with credentials, publish and read it back
curl -u admin:<password> -d "it worked" http://127.0.0.1:8098/alerts
curl -u admin:<password> 'http://127.0.0.1:8098/alerts/json?poll=1'
```

## Wiring up the other services' alerts

A separate user per service, with access only to its own topic, beats reusing
the admin — if one leaks, the damage is one topic.

```bash
read -rs NTFY_PASSWORD && export NTFY_PASSWORD
podman exec -e NTFY_PASSWORD ntfy ntfy user add alerts
unset NTFY_PASSWORD
podman exec ntfy ntfy access alerts 'uptime-kuma' write-only
podman exec ntfy ntfy access alerts 'wud' write-only
podman exec ntfy ntfy access alerts 'backup' write-only
# and read access for you, on the phone
podman exec ntfy ntfy access admin '*' read-write
```

One detail about addresses applies to all three: under rootless, this
repository's containers do not share a bridge network, so they do **not**
resolve each other by container name. The address that works from inside any
of them is the tailnet one (`https://ntfy.<your-tailnet>.ts.net`, via
[tsdproxy](../tsdproxy/), with real TLS) — confirmed by resolving it from
inside uptime-kuma. `http://<host-ip>:8098` also works, in clear text.

- **[uptime-kuma](../uptime-kuma/)** — Settings → Notifications → new, of
  type `ntfy`. Server `https://ntfy.<your-tailnet>.ts.net`, topic
  `uptime-kuma`, with the username and password above.
- **[wud](../wud/)** — a native trigger, through environment variables in
  `wud.env`:
  ```bash
  WUD_TRIGGER_NTFY_ALERTS_URL=https://ntfy.<your-tailnet>.ts.net
  WUD_TRIGGER_NTFY_ALERTS_TOPIC=wud
  WUD_TRIGGER_NTFY_ALERTS_AUTH_USER=alerts
  WUD_TRIGGER_NTFY_ALERTS_AUTH_PASSWORD=<password>
  ```
- **[zerobyte](../zerobyte/)** — in the job's notifications, a `POST` webhook
  to `https://ntfy.<your-tailnet>.ts.net/backup` with the header
  `Authorization: Basic <base64 of alerts:password>`.

## Auto-update

No `AutoUpdate=` — an explicit tag (`v2.27.0`), bumped by hand
(rule 9 of the [conventions](../../docs/conventions.md)). The `wud.tag.include` restricts it to `vX.Y.Z`.

## Backup & recovery

```bash
systemctl --user stop ntfy
tar -czf ntfy-backup-$(date +%Y%m%d-%H%M%S).tar.gz \
  -C ~/.config/containers/volumes ntfy
systemctl --user start ntfy
```

Only `lib/user.db` really matters (the users and permissions) — the message
cache is disposable by definition.

## Useful commands

```bash
systemctl --user status ntfy
podman logs -f ntfy
podman exec ntfy ntfy user list
podman exec ntfy ntfy access
curl -s http://127.0.0.1:8098/v1/health
```

## Credits

Quadlet deploy based on [ntfy](https://github.com/binwiederhier/ntfy)
by [binwiederhier](https://github.com/binwiederhier)
(Apache-2.0/GPL-2.0).
