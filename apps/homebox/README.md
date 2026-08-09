# HomeBox

<img src="https://cdn.jsdelivr.net/gh/homarr-labs/dashboard-icons/svg/homebox.svg" width="64" height="64" alt="">

**[🇧🇷 Leia em português](./README.pt-BR.md)**

A home inventory — what you own, where it is, the receipt, the manual and the warranty, with search and labels.

## Install

```bash
qh homebox            # shows the plan
qh homebox --apply
```

Open `http://<host-ip>:7745` or `https://homebox.<your-tailnet>.ts.net`.

<details>
<summary><b>Manual install</b></summary>

```bash
# 1. Download the unit (no need to clone the repository)
mkdir -p ~/.config/containers/systemd
wget -P ~/.config/containers/systemd/ \
  https://raw.githubusercontent.com/wallacepnts/quadlet-homelab/main/apps/homebox/homebox.container

# 2. Directory, with the owner matching the unit's User=1000.
#    `podman unshare` runs the chown INSIDE the user namespace, which is
#    where the container's 1000 exists (on the host that becomes 100999).
mkdir -p ~/.config/containers/volumes/homebox/data
podman unshare chown -R 1000:1000 ~/.config/containers/volumes/homebox/data

# 3. The mandatory secret (see above)
mkdir -p ~/.config/containers/secrets/homebox
openssl rand -base64 48 | tr -d '\n' \
  > ~/.config/containers/secrets/homebox/api-key-pepper.txt
chmod 600 ~/.config/containers/secrets/homebox/api-key-pepper.txt
podman secret create homebox-api-key-pepper \
  ~/.config/containers/secrets/homebox/api-key-pepper.txt

# 4. Variables. Start with signup OPEN so you can create your account —
#    step 6 closes it afterwards.
mkdir -p ~/.config/containers/env
wget -O ~/.config/containers/env/homebox.env \
  https://raw.githubusercontent.com/wallacepnts/quadlet-homelab/main/apps/homebox/.env.example
sed -i 's/^HBOX_OPTIONS_ALLOW_REGISTRATION=false/HBOX_OPTIONS_ALLOW_REGISTRATION=true/' \
  ~/.config/containers/env/homebox.env

# 5. Start it
systemctl --user daemon-reload
systemctl --user start homebox
```

```bash
# 6. Fechar o cadastro depois de criar a sua conta
sed -i 's/^HBOX_OPTIONS_ALLOW_REGISTRATION=true/HBOX_OPTIONS_ALLOW_REGISTRATION=false/' \
  ~/.config/containers/env/homebox.env
systemctl --user restart homebox
# conferir: allowRegistration deve virar false
curl -s http://127.0.0.1:7745/api/v1/status | grep -o '"allowRegistration":[a-z]*'
```

</details>

## Files

```
homebox.container
.env.example
install.ini
```

## Update

```bash
qh homebox --update --apply
```

Pinned to `0.26.2`. Nothing updates on its own — a new version is applied
when you run the command above.

## Backup

```bash
qh homebox --backup --apply --out ~/backups
```

It stops the service, packs the data, the `.env` and the secrets, and starts
it again. Cold on purpose: copying a live database gives an archive that only
fails when you restore it.

To restore, over the current data:

```bash
qh homebox --restore ~/backups/homebox-20260809-1200.tar.gz --apply
```

It asks you to type `homebox` to confirm, because the current data is deleted
before the archive is unpacked.

## Remove

```bash
qh homebox --remove --apply           # stops it, keeps the data
qh homebox --remove --purge --apply   # and deletes volumes, secrets and .env
```

`--purge` asks for the typed name too. The tailnet node is not deregistered by
this — that is done in the Tailscale admin.

## Commands

```bash
systemctl --user status homebox
podman logs -f homebox
```

## Credits

[sysadminsmedia/homebox](https://github.com/sysadminsmedia/homebox) — AGPL-3.0

[Official documentation](https://homebox.software)
