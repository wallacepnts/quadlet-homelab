# OwnTracks — Podman Quadlet (rootless)

**[🇧🇷 Leia em português](./README.pt-BR.md)**

An [OwnTracks Recorder](https://owntracks.org/booklet/clients/recorder/)
(a self-hosted location tracking backend, receiving positions from the
official OwnTracks apps for Android/iOS) + [Mosquitto](https://mosquitto.org)
(an MQTT broker) + [OwnTracks Frontend](https://github.com/owntracks/frontend)
(a Vue.js web interface fuller than the recorder's built-in viewer) deploy via
Podman Quadlet, migrated from the official
[`docker-compose-mqtt.yml`](https://github.com/owntracks/docker-recorder/blob/master/docker-compose-mqtt.yml)
.

## Architecture

Three containers on the `owntracks-net.network` network:

- `mosquitto` — the MQTT broker, exposing `1883` (the native MQTT protocol,
  which is where the phone apps publish their location) and `9001` (the same
  broker over WebSockets, for browser/JS-based MQTT clients — the official
  phone app uses `1883`, not this one)
- `owntracks-recorder` — it subscribes to `owntracks/#` on the broker, stores
  every position received and exposes `8083` (a web interface with a map and
  history, plus an HTTP API)
- `owntracks-frontend` — a separate Vue.js SPA, exposing `80` (mapped to
  `8087` on the host). The image's internal nginx reverse-proxies `/api/` and
  `/ws/` to `owntracks-recorder` (via `SERVER_HOST`/`SERVER_PORT`) and serves
  the static assets — it does not talk to Mosquitto, only to the recorder. It
  only starts once the recorder is up (`Requires=`/`After=`).

The recorder's basic built-in viewer (`owntracks.<your-tailnet>.ts.net`) and
the Vue.js frontend (`owntracks-ui.<your-tailnet>.ts.net`) coexist — both read
the same API and data; the frontend simply has more features (a heat map,
filters and so on).

**Unlike the official
[`docker-compose-mqtt.yml`](https://github.com/owntracks/docker-recorder/blob/master/docker-compose-mqtt.yml)
**, which brings Mosquitto up with `mosquitto -c /mosquitto-no-auth.conf`
(anyone on the network publishes and subscribes with no authentication — it
only serves to test the recorder on its own, as the compose's own comment
warns). Here Mosquitto comes up with `allow_anonymous false` plus a
`password_file` from the first start — the same MQTT username and password is
used both by `owntracks-recorder` and by the phone apps (see "Configuring the
app" below).

**Tested in practice: `ot-recorder` does not tolerate an unavailable broker at
start** — it exits with `Connection refused` instead of waiting or retrying on
its own, which is why `owntracks-recorder` only starts once `mosquitto`
reports `healthy` (`Requires=`/`After=`, the same pattern as
[karakeep](../karakeep/)/[any-sync-bundle](../any-sync-bundle/));
`Restart=always` covers the case of Mosquitto still not being ready on the
first attempt anyway.

## Files

```
owntracks-net.network          # the dedicated network
owntracks-mosquitto.container  # the MQTT broker
owntracks-recorder.container   # the application (backend + basic viewer)
owntracks-frontend.container   # the separate Vue.js UI
mosquitto.conf                 # the broker's config (auth enabled)
frontend-config.js             # the frontend's config (empty by default)
```

## Prerequisites

- Rootless Podman with systemd `--user` working
- `openssl` (to generate the MQTT password)

## Installation

```bash
python3 install.py owntracks            # dry-run: shows what it will do
python3 install.py owntracks --apply
```

For the local network only, `--access local`; on the tailnet and the LAN,
`--access both`. Adding `--href-local` points the dashboard link at the LAN.
The script creates the directories, writes the `.env`, generates the secrets,
fixes the volumes' ownership, starts the service and prints the address at the
end — see [Installing and operating](../../docs/installing.md).



<details>
<summary><b>Manual installation</b> (advanced) — the same steps, one at a time</summary>


```bash
# 1. Download the units (no need to clone the repository)
mkdir -p ~/.config/containers/systemd/owntracks
for f in owntracks-net.network owntracks-mosquitto.container \
         owntracks-recorder.container owntracks-frontend.container; do
  wget -P ~/.config/containers/systemd/owntracks/ \
    "https://raw.githubusercontent.com/wallacepnts/quadlet-homelab/main/apps/owntracks/$f"
done

# 2. Directories — a bind mount requires them to exist before the start
mkdir -p ~/.config/containers/volumes/owntracks/{mosquitto/config,mosquitto/data,store,config}
wget -O ~/.config/containers/volumes/owntracks/mosquitto/config/mosquitto.conf \
  https://raw.githubusercontent.com/wallacepnts/quadlet-homelab/main/apps/owntracks/mosquitto.conf
wget -O ~/.config/containers/volumes/owntracks/frontend-config.js \
  https://raw.githubusercontent.com/wallacepnts/quadlet-homelab/main/apps/owntracks/frontend-config.js

# 3. The MQTT password — generated once, used by the phone app to
#    authenticate with the broker. The two secrets below (Mosquitto's passwd
#    file and the recorder's OTR_PASS) embed the SAME password.
mkdir -p ~/.config/containers/secrets/owntracks
MQTT_PW=$(openssl rand -base64 24 | tr -d '\n')

# 3a. Mosquitto's passwd — mosquitto_passwd generates the hash, and we turn
#     it into a secret rather than leaving it as a loose file in the volume
#     ([rule 2](../../docs/conventions.md)). A secret mounted as a file comes
#     out 0444 (world-readable) by Podman's default — which works even with
#     mosquitto running internally as the non-root "mosquitto" user.
podman run --rm --entrypoint mosquitto_passwd \
  -v ~/.config/containers/secrets/owntracks:/secrets:Z \
  docker.io/library/eclipse-mosquitto:2.1.2-alpine \
  -b -c /secrets/mosquitto-passwd owntracks "$MQTT_PW"
podman secret create owntracks-mosquitto-passwd ~/.config/containers/secrets/owntracks/mosquitto-passwd

# 3b. The recorder's OTR_PASS — the same password, raw (not hashed), so the
#     recorder's own MQTT client can authenticate with the broker
echo -n "$MQTT_PW" > ~/.config/containers/secrets/owntracks/mqtt-password.txt
chmod 600 ~/.config/containers/secrets/owntracks/mqtt-password.txt
podman secret create owntracks-mqtt-password ~/.config/containers/secrets/owntracks/mqtt-password.txt
echo "MQTT password (configure this in the phone app): $MQTT_PW"

# 4. Non-secret env — download the example
#    created above; only edit it if you want a username other than
#    "owntracks", redoing step 3 with that name)
mkdir -p ~/.config/containers/env
wget -O ~/.config/containers/env/owntracks-recorder.env \
  https://raw.githubusercontent.com/wallacepnts/quadlet-homelab/main/apps/owntracks/.env.example

# 5. Start it (mosquitto comes up first via Requires=; the frontend comes up
#    after the recorder, by the same logic)
systemctl --user daemon-reload
systemctl --user start owntracks-frontend
```

The recorder's basic built-in viewer through [tsdproxy](../tsdproxy/)
(tailnet) at `https://owntracks.<your-tailnet>.ts.net`, or locally at
`http://localhost:8086`. The fuller Vue.js UI at
`https://owntracks-ui.<your-tailnet>.ts.net`, or locally at
`http://localhost:8087` — a map with the history of received positions (empty
until the first phone app publishes something).

**Neither web interface has authentication of its own** — the same trust model
already used by [WUD](../wud/)/[Homepage](../homepage/) here: protected only
by being on the tailnet, not by a login.

</details>

## Configuring the OwnTracks app on the phone

In the app (Android/iOS), reporting mode **MQTT** (not HTTP):

| Field | Value |
| --- | --- |
| Host | the **host's own** tailnet hostname (`<this-host-name>.<your-tailnet>.ts.net`, see `tailscale status` on it) or its local IP — **not** `owntracks.<your-tailnet>.ts.net` (see the note below) |
| Port | `1883` |
| TLS | off (no certificate is configured here — see the note below) |
| Username | `owntracks` (or whatever was used in step 3 of the installation) |
| Password | the password printed in step 3 |
| ClientID/DeviceID | one per device, your choice |
| Protocol level (session) | `4` (MQTT 3.1.1) |
| URL | blank |
| Encryption key | blank |

**Why the host's hostname and not `owntracks.<your-tailnet>.ts.net`**: tested
in practice — raw TCP proxying (`tsdproxy.port.*`, the same mechanism as
[any-sync-bundle](../any-sync-bundle/)) hangs permanently at
"Starting"/`NeedsLogin` on tsdproxy 2.3.4 and never reaches `Running`
(any-sync-bundle shows the same symptom in its logs — a health check failing
in a loop — so it is not specific to this app). `owntracks-mosquitto.container`
declares no tsdproxy labels because of that. Since `PublishPort=1883:1883`
already exposes the port on **every** host interface — including the tailnet's
own, not just localhost — the host's hostname works directly, with no tsdproxy
in that path. The web interface (`owntracks.<your-tailnet>.ts.net`) keeps
working as usual; it is only the MQTT port that does not go through tsdproxy.

**URL blank**: that field belongs to **HTTP** mode (an endpoint like
`https://.../pub`), not MQTT — the app shows both groups of fields on the same
screen regardless of the mode chosen. It has no effect here, since the mode is
MQTT.

**Encryption key blank**: it encrypts the location payload before publishing
it to the broker — designed for when the broker is shared or public and you do
not trust whoever else has access to it. Since this Mosquitto is only
reachable from inside the tailnet and is for personal use, it adds no real
security, only complexity (the recorder would have to load the same key via
`ocat --load=keys` to be able to decode the positions).

**Protocol level `4`, not `3`/`5`**: this is the MQTT CONNECT packet's
"protocol level" — `3` = MQTT 3.1, `4` = MQTT 3.1.1, `5` = MQTT 5.0. Mosquitto
2.1.2 accepts all three, but `4`/3.1.1 is the most tested and compatible, and
the one `ot-recorder` itself uses — MQTT 5.0 brings features neither the
recorder nor most clients exploit, with no practical gain here.

**Why `1883`, not `8883`**: `8883` is the standard port for MQTT **with TLS**
(MQTTS) — since this deploy configures no certificate at all (see the note
below), there is no TLS listener to answer there. `1883` is the right port for
native, plain-text MQTT, which is what is running here.

**No TLS**: the MQTT traffic goes out in clear text (only the password
travels, using the protocol's basic authentication, without being behind
HTTPS) — acceptable here because, like the rest of this repository, it is only
reachable from inside the tailnet and never from the public internet. Adding
TLS later is possible (an extra `listener` in `mosquitto.conf` with
`certfile`/`keyfile`/`cafile`, see the official
[`docker-compose-ssl.yml`](https://github.com/owntracks/docker-recorder/blob/master/docker-compose-ssl.yml)
), but it is not this deploy's default.

## WebSockets (port `9001`)

Besides `1883` (native MQTT, used by the phone app), Mosquitto also listens on
`9001` with `protocol websockets` — useful only if you ever want to connect a
browser/JS-based MQTT client (a dashboard of your own, say) straight to the
broker. The same authentication (the username and password from step 3)
applies to both listeners, since `mosquitto.conf` does not use
`per_listener_settings`. Neither of this deploy's containers (the recorder or
any viewer) uses that listener — it stays available but idle until something
does.

**In the phone app, do not enable or use WebSockets — leave it on native MQTT
(`1883`, see the table above).** WebSockets exists to work around environments
where a socket can only be opened over HTTP (mainly browsers and JS, which
have no access to a raw TCP socket). The official OwnTracks app
(Android/iOS) implements MQTT natively, without that limitation — using
WebSockets there would only add overhead, with no gain at all.

## Auto-update

No `AutoUpdate=` — explicit tags (`1.0.1` on the recorder, `2.15.3` on the
frontend, `2.1.2-alpine` on mosquitto), bumped by hand
([rule 9](../../docs/conventions.md)). All three images also publish variants
with a build suffix (`1.0.1-43`, `2.1.2-alpine` vs. a bare `2.1.2`) that would
confuse WUD's semver parser — `wud.watch=true` is on `owntracks-recorder` and
`owntracks-frontend` (the two user-facing apps), with `wud.tag.include`
restricting candidates to plain `X.Y.Z`; `mosquitto` is left out (an internal
dependency, the same pattern already applied to databases and caches across
the rest of the repository).

## Backup & recovery

```bash
systemctl --user stop owntracks-frontend owntracks-recorder owntracks-mosquitto
tar -czf owntracks-backup-$(date +%Y%m%d-%H%M%S).tar.gz \
  -C ~/.config/containers/volumes owntracks
systemctl --user start owntracks-frontend
```

`store/` is the real location history (LMDB) — what genuinely matters here.
`mosquitto/data/` holds only the broker's persistence file (retained messages,
if any); losing it is inconvenient, not destructive. `frontend-config.js` only
matters if you have customised something beyond the empty default.
`~/.config/containers/secrets/owntracks/` (the raw password plus Mosquitto's
passwd hash) needs a separate backup too — without it, the phones lose access
to the broker until the password is reconfigured.

## Useful commands

```bash
systemctl --user status owntracks-frontend owntracks-recorder owntracks-mosquitto
podman logs -f owntracks-recorder
podman logs -f owntracks-frontend
podman logs -f mosquitto
curl -s http://127.0.0.1:8086/api/0/list   # the users and devices already registered
```

## Credits

Quadlet deploy based on [OwnTracks Recorder](https://github.com/owntracks/recorder)
(GPL-2.0), by [Jan-Piet Mens](https://github.com/jpmens), and on the official
[docker-recorder](https://github.com/owntracks/docker-recorder) (the image
plus the reference `docker-compose-mqtt.yml`). The web interface comes from
[OwnTracks Frontend](https://github.com/owntracks/frontend) (MIT). The MQTT
broker comes from
[Eclipse Mosquitto](https://github.com/eclipse-mosquitto/mosquitto)
(EPL-2.0/EDL-1.0).
