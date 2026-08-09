# ntfy

<img src="https://cdn.jsdelivr.net/gh/homarr-labs/dashboard-icons/svg/ntfy.svg" width="64" height="64" alt="">

**[🇧🇷 Leia em português](./README.pt-BR.md)**

A push notification server — where the uptime-kuma, wud and zerobyte alerts go, with a phone app.

## Install

```bash
qh ntfy            # shows the plan
qh ntfy --apply
```

Open `http://<host-ip>:2586` or `https://ntfy.<your-tailnet>.ts.net`.

<details>
<summary><b>Manual install</b></summary>

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

</details>

## Files

```
ntfy.container
.env.example
```

## Update

```bash
qh ntfy --update --apply
```

Pinned to `v2.27.0`. Nothing updates on its own — a new version is applied
when you run the command above.

## Backup

```bash
qh ntfy --backup --apply --out ~/backups
```

It stops the service, packs the data, the `.env` and the secrets, and starts
it again. Cold on purpose: copying a live database gives an archive that only
fails when you restore it.

To restore, over the current data:

```bash
qh ntfy --restore ~/backups/ntfy-20260809-1200.tar.gz --apply
```

It asks you to type `ntfy` to confirm, because the current data is deleted
before the archive is unpacked.

## Remove

```bash
qh ntfy --remove --apply           # stops it, keeps the data
qh ntfy --remove --purge --apply   # and deletes volumes, secrets and .env
```

`--purge` asks for the typed name too. The tailnet node is not deregistered by
this — that is done in the Tailscale admin.

## Commands

```bash
systemctl --user status ntfy
podman logs -f ntfy
```

## Credits

[binwiederhier/ntfy](https://github.com/binwiederhier/ntfy) — Apache-2.0

[Official documentation](https://ntfy.sh)
