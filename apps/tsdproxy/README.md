# tsdproxy

<img src="https://cdn.jsdelivr.net/gh/selfhst/icons/svg/tsdproxy.svg" width="64" height="64" alt="">

**[🇧🇷 Leia em português](./README.pt-BR.md)**

Publishes containers on the tailnet automatically, from labels alone — no per-service proxy configuration.

## Install

```bash
qh tsdproxy            # shows the plan
qh tsdproxy --apply
```

Open `http://<host-ip>:8080` or `https://dash.<your-tailnet>.ts.net`.

<details>
<summary><b>Manual install</b></summary>

```bash
# 1. Download the unit (no need to clone the repository)
mkdir -p ~/.config/containers/systemd
wget -P ~/.config/containers/systemd/ \
  https://raw.githubusercontent.com/wallacepnts/quadlet-homelab/main/apps/tsdproxy/tsdproxy.container

# 2. Data directories — a bind mount requires them to exist before the start.
#    tsdproxy does not generate a default config by itself, so
#    config/tsdproxy.yaml also has to come from somewhere before the first
#    start.
mkdir -p ~/.config/containers/volumes/tsdproxy/{data,config}
wget -O ~/.config/containers/volumes/tsdproxy/config/tsdproxy.yaml \
  https://raw.githubusercontent.com/wallacepnts/quadlet-homelab/main/apps/tsdproxy/config/tsdproxy.yaml

# 3. A secret with the Tailscale authkey
mkdir -p ~/.config/containers/secrets/tsdproxy
echo -n "YOUR_AUTHKEY" > ~/.config/containers/secrets/tsdproxy/authkey.txt
chmod 600 ~/.config/containers/secrets/tsdproxy/authkey.txt
podman secret create authkey ~/.config/containers/secrets/tsdproxy/authkey.txt

# 4. The Podman socket
systemctl --user enable --now podman.socket

# 5. Start it
systemctl --user daemon-reload
systemctl --user start tsdproxy
```

</details>

## Files

```
tsdproxy.container
install.ini
```

## Update

```bash
qh tsdproxy --update --apply
```

Pinned to `2`. Nothing updates on its own — a new version is applied
when you run the command above.

## Backup

```bash
qh tsdproxy --backup --apply --out ~/backups
```

It stops the service, packs the data, the `.env` and the secrets, and starts
it again. Cold on purpose: copying a live database gives an archive that only
fails when you restore it.

To restore, over the current data:

```bash
qh tsdproxy --restore ~/backups/tsdproxy-20260809-1200.tar.gz --apply
```

It asks you to type `tsdproxy` to confirm, because the current data is deleted
before the archive is unpacked.

## Remove

```bash
qh tsdproxy --remove --apply           # stops it, keeps the data
qh tsdproxy --remove --purge --apply   # and deletes volumes, secrets and .env
```

`--purge` asks for the typed name too. The tailnet node is not deregistered by
this — that is done in the Tailscale admin.

## Commands

```bash
systemctl --user status tsdproxy
podman logs -f tsdproxy
```

## Credits

[almeidapaulopt/tsdproxy](https://github.com/almeidapaulopt/tsdproxy) — MIT

[Official documentation](https://almeidapaulopt.github.io/tsdproxy/)
