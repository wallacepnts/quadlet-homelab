# OpenWA — Podman Quadlet (rootless)

**[🇧🇷 Leia em português](./README.pt-BR.md)**

An [OpenWA](https://github.com/rmyndharis/OpenWA) (self-hosted WhatsApp API
gateway) deploy via Podman Quadlet, using the official
`ghcr.io/rmyndharis/openwa` image.

It turns a WhatsApp account into an HTTP API: link the phone by QR code, then
send and receive messages over REST, with webhooks for incoming events. It is
the piece that lets [n8n](../n8n/) or [Home Assistant](../home-assistant/)
talk to WhatsApp without a paid provider.

**It drives your personal account through the same channel WhatsApp Web uses.**
That is not an official API — the account can be blocked for volume or for
behaviour that looks automated. Treat it as a personal automation, not as a
broadcast tool.

## Architecture

A single container: NestJS, **embedded SQLite**, media stored on local disk.
One volume, `/app/data`, holding the database, the WhatsApp sessions, the
media and the plugins.

The upstream `docker-compose.yml` also ships Postgres, Redis and MinIO — all
three behind Compose **profiles**, so none of them runs by default. SQLite is
the supported alternative for the database (including the full-text search,
which uses FTS5), local disk for storage, and Redis is only needed for
multi-replica deployments. One container is the whole deployment here.

### What was deliberately left out: the Docker socket proxy

Upstream's compose has a fourth service, `tecnativa/docker-socket-proxy`,
which exists so the dashboard can spin up those Postgres/Redis/MinIO
containers by itself ("Infrastructure > built-in toggles"). Its own compose
comments say to disable it if you do not use that feature — and its
`SECURITY.md` states the proxy cannot scope container-create payloads, so a
compromised API container could create containers with host bind mounts.

Handing a WhatsApp-facing, internet-exposed container the Podman socket to
close a feature we do not use is not a trade worth making. `DOCKER_HOST` is
unset, `DockerService` reports Docker unavailable, and orchestration degrades
gracefully — which is exactly the documented behaviour.

## Files

```
openwa.container    # main unit
.env.example        # engine, log level, webhook timeouts
install.ini         # secret recipes
```

## Installation

```bash
python3 install.py openwa            # dry-run: shows what it will do
python3 install.py openwa --apply
```

For the local network only, `--access local`; on the tailnet and the LAN,
`--access both`. Adding `--href-local` points the dashboard link at the LAN.
The script creates the directories, writes the `.env`, generates the secrets,
fixes the volumes' ownership, starts the service and prints the address at the
end — see [Installing and operating](../../docs/installing.md).

Open `http://<host-ip>:2785` (or via [tsdproxy](../tsdproxy/) at
`https://openwa.<your-tailnet>.ts.net`), authenticate with the master key and
link the phone by scanning the QR code.

```bash
podman secret inspect --showsecret openwa-master-key
```

<details>
<summary><b>Manual installation</b> (advanced) — the same steps, one at a time</summary>


```bash
# 1. Download the unit (no need to clone the repository)
mkdir -p ~/.config/containers/systemd
wget -P ~/.config/containers/systemd/ \
  https://raw.githubusercontent.com/wallacepnts/quadlet-homelab/main/apps/openwa/openwa.container

# 2. Directories
mkdir -p ~/.config/containers/volumes/openwa/data
mkdir -p ~/.config/containers/env

# 3. Environment
wget -O ~/.config/containers/env/openwa.env \
  https://raw.githubusercontent.com/wallacepnts/quadlet-homelab/main/apps/openwa/.env.example

# 4. Secrets
podman secret create openwa-master-key - <<< "$(python3 -c 'import secrets;print(secrets.token_urlsafe(48))')"
podman secret create openwa-key-pepper - <<< "$(openssl rand -hex 32)"

# 5. Start it
systemctl --user daemon-reload
systemctl --user start openwa
```

</details>

## The engine

OpenWA supports two, and the choice matters more than any other setting here:

| | `whatsapp-web.js` (default) | `baileys` |
| --- | --- | --- |
| How | a real Chromium driving WhatsApp Web | a WebSocket client, no browser |
| Cost | ~1–2 GB RAM, hundreds of processes | tens of MB |
| Bundled | yes, Chromium ships in the image | yes, loaded lazily |

Left unset, the dashboard governs it (Infrastructure > Engine) and defaults to
`whatsapp-web.js`. Setting `ENGINE_TYPE` in the `.env` always wins over the
dashboard.

**The hardening in the unit is sized for the Chromium engine.** If you pin
`baileys`, `PidsLimit=2048` and `Tmpfs=/tmp:size=512M` are both far larger
than needed — but leaving them oversized costs nothing, and shrinking them
breaks the day you switch back.

## Hardening

Upstream's own compose already runs the container `read_only`, with
`cap_drop: ALL` and `no-new-privileges`, so those came validated. What each
line here costs, in the order of [rule 20](../../docs/conventions.md):

- **`DropCapability=ALL` plus five back.** The entrypoint runs as root, does
  `chown -R openwa /app/data` on the volume and then drops to the `openwa`
  user via `gosu` — that needs `CHOWN`, `DAC_OVERRIDE`, `FOWNER`, `SETGID`
  and `SETUID`. This is upstream's list, not a guess.
- **No `User=`.** Same reason: the image drops privileges by itself. Forcing a
  uid would break the `chown` before it ever reaches `gosu`.
- **`Tmpfs=/tmp:size=512M`, not 64M.** Under `ReadOnly=true`, `HOME`,
  `XDG_CONFIG_HOME` and `XDG_CACHE_HOME` are all redirected into `/tmp`, and
  Chromium treats it as scratch. Measure under real use with
  `podman exec openwa df -h /tmp` before trimming it.
- **`PidsLimit=2048`, not the repository's usual 256.** Upstream's default,
  and the one number here that is not conservative: Chromium spawns a process
  per tab, per renderer and per utility, per linked session.

Memory is not capped in the unit — upstream suggests 2 GB. Add `Memory=2G` if a
runaway session starts to hurt the host; it is left off here because a hard cap
on a browser mid-session shows up as a killed WhatsApp link, not as an error.

## The database is SQLite

`DATABASE_TYPE=sqlite` in the unit, and `DATABASE_NAME` deliberately **unset**
in the `.env` — with SQLite a bare value there becomes the database file
*path*, which under `ReadOnly=true` is a `SQLITE_CANTOPEN` boot-loop
(upstream #677). The default path, `/app/data/openwa.sqlite`, is inside the
volume.

## Auto-update

No `AutoUpdate=` — an explicit tag (`0.14.6`), bumped by hand
([rule 9](../../docs/conventions.md)). A `0.x` project moving fast, holding
WhatsApp sessions that have to be re-linked by QR code if the state breaks:
read the [CHANGELOG](https://github.com/rmyndharis/OpenWA/blob/main/CHANGELOG.md)
and take a backup before bumping.

Upstream also publishes commit-sha tags alongside the versions, hence the
`wud.tag.include=^[0-9]+.[0-9]+.[0-9]+$` in the unit. Note the release tags
carry a `v` prefix (`v0.14.6`) while the image tags do not (`0.14.6`).

## Backup & recovery

```bash
systemctl --user stop openwa
tar -czf openwa-backup-$(date +%Y%m%d-%H%M%S).tar.gz \
  -C ~/.config/containers/volumes openwa
systemctl --user start openwa
```

The sessions are in there. Restoring an old backup over a newer state does not
restore the WhatsApp link — the phone has to scan the QR code again.

The two secrets are **not** in the volume. Losing `openwa-key-pepper` means
every issued API key stops validating; losing `openwa-master-key` locks you
out of the dashboard. Both come back with `install.py`, but the keys issued to
your integrations do not.

## Useful commands

```bash
systemctl --user status openwa
podman logs -f openwa
podman exec openwa df -h /tmp        # is 512M enough?
curl -H "X-Api-Key: $KEY" http://127.0.0.1:2785/api/sessions
```

## Credits

Quadlet deploy based on [OpenWA](https://github.com/rmyndharis/OpenWA) by
[rmyndharis](https://github.com/rmyndharis) (MIT).
