# n8n

<img src="https://cdn.jsdelivr.net/gh/homarr-labs/dashboard-icons/svg/n8n.svg" width="64" height="64" alt="">

**[🇧🇷 Leia em português](./README.pt-BR.md)**

Workflow automation through a visual node editor.

## Install

```bash
qh n8n            # shows the plan
qh n8n --apply
```

Open `http://<host-ip>:5678` or `https://n8n.<your-tailnet>.ts.net`.

<details>
<summary><b>Manual install</b></summary>

```bash
# 1. Download the unit (no need to clone the repository)
mkdir -p ~/.config/containers/systemd
wget -P ~/.config/containers/systemd/ \
  https://raw.githubusercontent.com/wallacepnts/quadlet-homelab/main/apps/n8n/n8n.container

# 2. Data directory — a bind mount requires it to exist before the start
mkdir -p ~/.config/containers/volumes/n8n/data

# 3. Secret — the encryption key for the credentials saved in workflows
#    (API tokens, passwords and so on). Generate it explicitly rather than
#    letting n8n generate one on the first start, so the value is documented.
mkdir -p ~/.config/containers/secrets/n8n
openssl rand -hex 32 | tr -d '\n' > ~/.config/containers/secrets/n8n/encryption-key.txt
chmod 600 ~/.config/containers/secrets/n8n/encryption-key.txt
podman secret create n8n-encryption-key ~/.config/containers/secrets/n8n/encryption-key.txt

# 4. Non-secret env — download the example
mkdir -p ~/.config/containers/env
wget -O ~/.config/containers/env/n8n.env \
  https://raw.githubusercontent.com/wallacepnts/quadlet-homelab/main/apps/n8n/.env.example

# 5. Start it
systemctl --user daemon-reload
systemctl --user start n8n
```

</details>

## Files

```
n8n.container
.env.example
install.ini
```

## Update

```bash
qh n8n --update --apply
```

Pinned to `2.33.7`. Nothing updates on its own — a new version is applied
when you run the command above.

## Backup

```bash
qh n8n --backup --apply --out ~/backups
```

It stops the service, packs the data, the `.env` and the secrets, and starts
it again. Cold on purpose: copying a live database gives an archive that only
fails when you restore it.

To restore, over the current data:

```bash
qh n8n --restore ~/backups/n8n-20260809-1200.tar.gz --apply
```

It asks you to type `n8n` to confirm, because the current data is deleted
before the archive is unpacked.

## Remove

```bash
qh n8n --remove --apply           # stops it, keeps the data
qh n8n --remove --purge --apply   # and deletes volumes, secrets and .env
```

`--purge` asks for the typed name too. The tailnet node is not deregistered by
this — that is done in the Tailscale admin.

## Commands

```bash
systemctl --user status n8n
podman logs -f n8n
```

## Credits

[n8n-io/n8n](https://github.com/n8n-io/n8n)

[Official documentation](https://n8n.io)
