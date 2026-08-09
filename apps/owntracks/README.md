# OwnTracks

<img src="https://cdn.jsdelivr.net/gh/homarr-labs/dashboard-icons/svg/owntracks.svg" width="64" height="64" alt="">

**[🇧🇷 Leia em português](./README.pt-BR.md)**

Personal location tracking through a phone app, with its own MQTT broker and a position history.

## Install

```bash
qh owntracks            # shows the plan
qh owntracks --apply
```

Open `http://<host-ip>:1883` or `https://owntracks-ui.<your-tailnet>.ts.net`.

<details>
<summary><b>Manual install</b></summary>

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
#     it into a secret rather than leaving it as a loose file in the volume.
#     A secret mounted as a file comes
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

</details>

## Files

```
owntracks-frontend.container
owntracks-mosquitto.container
owntracks-recorder.container
owntracks-net.network
.env.example
install.ini
```

Units in this stack:

- `owntracks-frontend`
- `owntracks-mosquitto`
- `owntracks-recorder`
- `owntracks-n`

## Update

```bash
qh owntracks --update --apply
```

Pinned to `1.0.1`, `2.1.2-alpine`, `2.15.3`. Nothing updates on its own — a new version is applied
when you run the command above.

## Backup

```bash
qh owntracks --backup --apply --out ~/backups
```

It stops the service, packs the data, the `.env` and the secrets, and starts
it again. Cold on purpose: copying a live database gives an archive that only
fails when you restore it.

To restore, over the current data:

```bash
qh owntracks --restore ~/backups/owntracks-20260809-1200.tar.gz --apply
```

It asks you to type `owntracks` to confirm, because the current data is deleted
before the archive is unpacked.

## Remove

```bash
qh owntracks --remove --apply           # stops it, keeps the data
qh owntracks --remove --purge --apply   # and deletes volumes, secrets and .env
```

`--purge` asks for the typed name too. The tailnet node is not deregistered by
this — that is done in the Tailscale admin.

## Commands

```bash
systemctl --user status owntracks
podman logs -f owntracks
```

## Credits

[owntracks/recorder](https://github.com/owntracks/recorder) — GPL-2.0

[Official documentation](https://owntracks.org/booklet/)
