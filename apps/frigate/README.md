# Frigate — Podman Quadlet (rootless)

**[🇧🇷 Leia em português](./README.pt-BR.md)**

A [Frigate](https://frigate.video) (an NVR with real-time AI object
detection from IP cameras) deploy via Podman Quadlet, using the official
`ghcr.io/blakeblackshear/frigate` image.

**Deployed with no camera configured yet** — it comes up and goes healthy, but
it has nothing to record or detect until you add at least one camera to
`config.yml` (see the dedicated section below).

## Architecture

A single container. **CPU-only by decision** — no Coral and no GPU passed
into the container by default (the project itself advises against CPU-only
detection for real use, but it is fine for exploring and testing; see
"Enabling hardware acceleration" below to turn it on later). Hence **no
`--privileged`** — that is only needed when a device (Coral/GPU) is passed
into the container, which is not the case here.

**The authenticated port (`8971`) speaks HTTPS internally, not HTTP** — tested
in practice: the image itself embeds an nginx with a self-signed certificate
on that port; hitting it with plain HTTP returns "400 The plain HTTP request
was sent to HTTPS port". That is why the `HealthCmd` uses `curl -k https://`
(not `http://`) and the tsdproxy label is `.../https` on the internal side,
unlike the `.../http` default used across the rest of this repository.

**The recording path is your decision**, through an `environment.d` variable
([rule 19](../../docs/conventions.md)) — not a fixed path such as
`%h/.config/containers/volumes/frigate/media`, because camera recordings grow
fast and need not live on the same disk as the other services. See step 3 of
the installation.

`/tmp/cache` (temporary recording segments) is a `tmpfs`, not a bind mount —
it avoids wearing the disk out with constant writes.

## Files

```
frigate.container       # main unit
```

No `config.yml` is versioned in this repository. **Careful**: with no config
present, the image **generates one itself** at `config/config.yaml` (the
`.yaml` extension, not `.yml`) on the first start, with an example camera
(`name_of_your_camera`, pointing at a fake IP `10.0.10.10`) — tested in
practice, that camera keeps trying to connect and failing in a loop in the
logs (`Connection timed out` every 10-20s or so) until it is removed or
disabled. Step 6 below already replaces that file with a clean one
(`cameras: {}`) before configuring the first real camera.

## Prerequisites

- Rootless Podman with systemd `--user` working

## Installation

```bash
python3 install.py frigate            # dry-run: shows what it will do
python3 install.py frigate --apply
```

For the local network only, `--access local`; on the tailnet and the LAN,
`--access both`. Adding `--href-local` points the dashboard link at the LAN.
The script creates the directories, writes the `.env`, generates the secrets,
fixes the volumes' ownership, starts the service and prints the address at the
end — see [Installing and operating](../../docs/installing.md).

Open `https://<host-ip>:8971` (accepting the self-signed certificate in the
browser) or, through [tsdproxy](../tsdproxy/), at
`https://frigate.<your-tailnet>.ts.net` (there with a valid certificate —
tsdproxy swaps the self-signed one for its own at the tailnet's edge).

<details>
<summary><b>Manual installation</b> (advanced) — the same steps, one at a time</summary>


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

Open `https://<host-ip>:8971` (accepting the self-signed certificate in the
browser) or, through [tsdproxy](../tsdproxy/), at
`https://frigate.<your-tailnet>.ts.net` (there with a valid certificate —
tsdproxy swaps the self-signed one for its own at the tailnet's edge).

</details>

## Login (an automatically generated user)

**There is no fixed default account** — the image creates an `admin` user with
a random password on the first start, visible only in the log (already
captured in step 6 of the installation, if you followed the order):

```bash
podman logs frigate 2>&1 | grep -A3 "Created a default user"
```

Change the password after logging in, under Settings → Users.

**Lost the password** (restarted before capturing it, or it no longer appears
in the log — it is only printed once, the first time the user database is
empty)? Deleting the user from the database forces the image to create a new
one with a new password on the next start, the same mechanism as the first
boot — tested in practice:

```bash
systemctl --user stop frigate
podman unshare sqlite3 ~/.config/containers/volumes/frigate/config/frigate.db \
  "DELETE FROM user WHERE username='admin';"
systemctl --user start frigate
until podman inspect frigate --format '{{.State.Health.Status}}' 2>/dev/null | grep -qE 'healthy|unhealthy'; do sleep 3; done
podman logs frigate 2>&1 | grep -A3 "Created a default user"
```

## Adding the first camera

Edit `~/.config/containers/volumes/frigate/config/config.yaml` (created in
step 6 of the installation — note the `.yaml` extension, not `.yml`):

```yaml
mqtt:
  enabled: False

cameras:
  front:
    ffmpeg:
      inputs:
        - path: rtsp://user:password@camera-ip:554/stream
          roles:
            - detect
            - record
    detect:
      width: 1280
      height: 720
    record:
      enabled: True
```

```bash
systemctl --user restart frigate
```

**Recalculate `--shm-size`** — this deploy's default `128m` covers only
Frigate's overhead with no cameras. The official per-camera formula (the
detection resolution, not the recording one):
`(width × height × 1.5 × 20 + 270480) / 1048576` MB, plus about 40MB of
headroom for logs. A 1280×720 camera, for example, comes to about 67MB —
adjust `PodmanArgs=--shm-size=` in the `.container`, adding that to whatever
is already there, then `systemctl --user daemon-reload && systemctl --user
restart frigate`.

**The restream ports** (`8554` RTSP, `8555` WebRTC) are not published by
default — they only matter if you use the embedded go2rtc's restream feature
(watching a camera directly without going through the UI). Add
`PublishPort=8554:8554` / `PublishPort=8555:8555/tcp` /
`PublishPort=8555:8555/udp` to the `.container` if you need them.

## Enabling hardware acceleration

### Coral USB

```ini
AddDevice=/dev/bus/usb:/dev/bus/usb
```

```yaml
detectors:
  coral:
    type: edgetpu
    device: usb
```

### Coral PCIe/M.2

```ini
AddDevice=/dev/apex_0:/dev/apex_0
```

```yaml
detectors:
  coral:
    type: edgetpu
    device: pci
```

### Intel GPU (OpenVINO, `/dev/dri`)

```ini
AddDevice=/dev/dri/renderD128:/dev/dri/renderD128
```

```yaml
detectors:
  ov:
    type: openvino
    device: GPU
```

### NVIDIA GPU (TensorRT) — the same GPU as this host's Ollama

This needs the **NVIDIA Container Toolkit** configured for Podman (it
generates the CDI spec) — the same prerequisite and the same steps already
documented in [Ollama's README](../openwebui/#enabling-an-nvidia-gpu). Then:

1. Change `Image=` to `ghcr.io/blakeblackshear/frigate:0.17.2-tensorrt` (a
   dedicated NVIDIA tag, different from the default image used here).
2. Add `PodmanArgs=--gpus=all` (alongside the existing `--shm-size=`).
3. In `config.yml`:
   ```yaml
   detectors:
     tensorrt:
       type: tensorrt
       device: 0
   ```

```bash
systemctl --user daemon-reload
systemctl --user restart frigate
```

## Auto-update

No `AutoUpdate=` — an explicit tag (`0.17.2`), bumped by hand
(rule 9 of the [conventions](../../docs/conventions.md)). The image has `curl` and a real healthcheck — `AutoUpdate=registry` could be
enabled with working rollback, but recordings and camera configuration are the
user's real data, so review by hand before updating.

## Backup & recovery

```bash
systemctl --user stop frigate
tar -czf frigate-config-backup-$(date +%Y%m%d-%H%M%S).tar.gz \
  -C ~/.config/containers/volumes frigate
systemctl --user start frigate
```

`config/` only — recordings (`$FRIGATE_MEDIA_DIR`) tend to be far too large
for a routine backup; do those separately if you need to, or accept that they
are disposable (the real value is usually the real-time detection, not the
historical archive).

## Useful commands

```bash
systemctl --user status frigate
podman logs -f frigate
podman exec frigate curl -fsSk https://127.0.0.1:8971/
```

## Credits

Quadlet deploy based on
[Frigate](https://github.com/blakeblackshear/frigate) (MIT).
