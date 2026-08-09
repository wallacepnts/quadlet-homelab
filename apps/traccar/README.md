# Traccar

<img src="https://cdn.jsdelivr.net/gh/homarr-labs/dashboard-icons/svg/traccar.svg" width="64" height="64" alt="">

**[🇧🇷 Leia em português](./README.pt-BR.md)**

GPS tracking — live map, history, geofences and reports, with a phone app.

## Install

```bash
qh traccar            # shows the plan
qh traccar --apply
```

Open `http://<host-ip>:5056` or `https://traccar.<your-tailnet>.ts.net`.

<details>
<summary><b>Manual install</b></summary>

```bash
# 1. Download the unit (no need to clone the repository)
mkdir -p ~/.config/containers/systemd
wget -P ~/.config/containers/systemd/ \
  https://raw.githubusercontent.com/wallacepnts/quadlet-homelab/main/apps/traccar/traccar.container

# 2. Directories, with the owner matching the unit's User=1000
mkdir -p ~/.config/containers/volumes/traccar/{data,logs,conf}

# 3. Config — it has to EXIST before the start (it is a file bind mount; if
#    it does not, Podman creates a directory instead and Traccar breaks)
wget -O ~/.config/containers/volumes/traccar/conf/traccar.xml \
  https://raw.githubusercontent.com/wallacepnts/quadlet-homelab/main/apps/traccar/traccar.xml.example

podman unshare chown -R 1000:1000 ~/.config/containers/volumes/traccar

# 4. Start it
systemctl --user daemon-reload
systemctl --user start traccar
```

</details>

## Files

```
traccar.container
traccar.xml.example
```

## Update

```bash
qh traccar --update --apply
```

Pinned to `6.14.5`. Nothing updates on its own — a new version is applied
when you run the command above.

## Backup

```bash
qh traccar --backup --apply --out ~/backups
```

It stops the service, packs the data, the `.env` and the secrets, and starts
it again. Cold on purpose: copying a live database gives an archive that only
fails when you restore it.

To restore, over the current data:

```bash
qh traccar --restore ~/backups/traccar-20260809-1200.tar.gz --apply
```

It asks you to type `traccar` to confirm, because the current data is deleted
before the archive is unpacked.

## Remove

```bash
qh traccar --remove --apply           # stops it, keeps the data
qh traccar --remove --purge --apply   # and deletes volumes, secrets and .env
```

`--purge` asks for the typed name too. The tailnet node is not deregistered by
this — that is done in the Tailscale admin.

## Commands

```bash
systemctl --user status traccar
podman logs -f traccar
```

## Credits

[traccar/traccar](https://github.com/traccar/traccar) — Apache-2.0

[Official documentation](https://www.traccar.org)
