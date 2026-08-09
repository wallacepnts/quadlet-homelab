# Donetick

<img src="https://cdn.jsdelivr.net/gh/homarr-labs/dashboard-icons/svg/donetick.svg" width="64" height="64" alt="">

**[🇧🇷 Leia em português](./README.pt-BR.md)**

Recurring household chores — who does them, how often, and when they are due.

## Install

```bash
qh donetick            # shows the plan
qh donetick --apply
```

Open `http://<host-ip>:2021` or `https://donetick.<your-tailnet>.ts.net`.

<details>
<summary><b>Manual install</b></summary>

```bash
# 1. Download the unit (no need to clone the repository)
mkdir -p ~/.config/containers/systemd
wget -P ~/.config/containers/systemd/ \
  https://raw.githubusercontent.com/wallacepnts/quadlet-homelab/main/apps/donetick/donetick.container

# 2. Directories
mkdir -p ~/.config/containers/volumes/donetick/{config,data}

# 3. Config — replace the JWT secret and the domain
wget -O ~/.config/containers/volumes/donetick/config/selfhosted.yaml \
  https://raw.githubusercontent.com/wallacepnts/quadlet-homelab/main/apps/donetick/selfhosted.yaml.example
sed -i "s|CHANGEME_openssl_rand_hex_24|$(openssl rand -hex 24)|" \
  ~/.config/containers/volumes/donetick/config/selfhosted.yaml
sed -i "s|<your-tailnet>|YOUR-TAILNET-HERE|g" \
  ~/.config/containers/volumes/donetick/config/selfhosted.yaml

# 4. Dono correspondente ao User=1000 da unit
podman unshare chown -R 1000:1000 ~/.config/containers/volumes/donetick

# 5. Start it
systemctl --user daemon-reload
systemctl --user start donetick
```

```bash
sed -i 's/^is_user_creation_disabled: false/is_user_creation_disabled: true/' \
  ~/.config/containers/volumes/donetick/config/selfhosted.yaml
systemctl --user restart donetick
```

</details>

## Files

```
donetick.container
selfhosted.yaml.example
install.ini
```

## Update

```bash
qh donetick --update --apply
```

Pinned to `v0.1.76`. Nothing updates on its own — a new version is applied
when you run the command above.

## Backup

```bash
qh donetick --backup --apply --out ~/backups
```

It stops the service, packs the data, the `.env` and the secrets, and starts
it again. Cold on purpose: copying a live database gives an archive that only
fails when you restore it.

To restore, over the current data:

```bash
qh donetick --restore ~/backups/donetick-20260809-1200.tar.gz --apply
```

It asks you to type `donetick` to confirm, because the current data is deleted
before the archive is unpacked.

## Remove

```bash
qh donetick --remove --apply           # stops it, keeps the data
qh donetick --remove --purge --apply   # and deletes volumes, secrets and .env
```

`--purge` asks for the typed name too. The tailnet node is not deregistered by
this — that is done in the Tailscale admin.

## Commands

```bash
systemctl --user status donetick
podman logs -f donetick
```

## Credits

[donetick/donetick](https://github.com/donetick/donetick) — AGPL-3.0

[Official documentation](https://donetick.com)
