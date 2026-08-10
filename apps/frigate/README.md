# Frigate

<img src="https://cdn.jsdelivr.net/gh/homarr-labs/dashboard-icons/png/frigate.png" width="64" height="64" alt="">

**[🇧🇷 Leia em português](./README.pt-BR.md)**

An NVR with AI object detection — CPU-only by default, no camera configured yet.

## Install

```bash
qh frigate            # shows the plan
qh frigate --apply
```

Open `http://<host-ip>:8971` or `https://frigate.<your-tailnet>.ts.net`.

<details>
<summary><b>Manual install</b></summary>

```bash
# 1. Download the units (no need to clone the repository)
mkdir -p ~/.config/containers/systemd
wget -P ~/.config/containers/systemd/ \
  https://raw.githubusercontent.com/wallacepnts/quadlet-homelab/main/apps/frigate/frigate.container

# 2. Config directory — a bind mount requires it to exist before the start
mkdir -p ~/.config/containers/volumes/frigate/config

# 3. Recording path — decide where the recordings will live (a disk with
#    spare room; it can be outside ~/.config/containers/volumes)
mkdir -p ~/.config/environment.d
cat > ~/.config/environment.d/frigate.conf <<EOF
FRIGATE_MEDIA_DIR=$HOME/frigate-media
EOF
mkdir -p "$HOME/frigate-media"
# If you prefer another disk or mount, use the real path up there.

# 4. Apply the new env.d (this needs a daemon-reload, not just restarting
#    the service — it is systemd --user that has to re-read the environment)
systemctl --user daemon-reload

# 5. Start it
systemctl --user start frigate

# 6. Capture the admin password BEFORE the restart in the next step —
#    tested in practice: this message appears in the log ONCE ONLY, on the
#    first start with an empty user database; restarting afterwards (step 7)
#    does not recreate the user (it already exists, persisted in the volume),
#    so the message does not come back, even though the account stays valid.
#    Wait for it to go healthy before checking.
until podman inspect frigate --format '{{.State.Health.Status}}' 2>/dev/null | grep -qE 'healthy|unhealthy'; do sleep 3; done
podman logs frigate 2>&1 | grep -A3 "Created a default user"
# Write down the username and password shown above — they will not appear
# again after the restart below.

# 7. Clear out the example camera the image generates by itself on the first
#    start (see the warning above) — without this, it keeps trying to connect
#    to a fake IP and polluting the logs until you configure a real camera
cat > ~/.config/containers/volumes/frigate/config/config.yaml <<EOF
mqtt:
  enabled: False

cameras: {}
EOF
systemctl --user restart frigate
```

</details>

## Files

```
frigate.container
```

## Update

```bash
qh frigate --update --apply
```

Pinned to `0.17.2`. Nothing updates on its own — a new version is applied
when you run the command above.

## Backup

```bash
qh frigate --backup --apply --out ~/backups
```

It stops the service, packs the data, the `.env` and the secrets, and starts
it again. Cold on purpose: copying a live database gives an archive that only
fails when you restore it.

To restore, over the current data:

```bash
qh frigate --restore ~/backups/frigate-20260809-1200.tar.gz --apply
```

It asks you to type `frigate` to confirm, because the current data is deleted
before the archive is unpacked.

## Remove

```bash
qh frigate --remove --apply           # stops it, keeps the data
qh frigate --remove --purge --apply   # and deletes volumes, secrets and .env
```

`--purge` asks for the typed name too. The tailnet node is not deregistered by
this — that is done in the Tailscale admin.

## Commands

```bash
systemctl --user status frigate
podman logs -f frigate
```

## Credits

[blakeblackshear/frigate](https://github.com/blakeblackshear/frigate) — MIT

[Official documentation](https://frigate.video)
