# Beszel

<img src="https://cdn.jsdelivr.net/gh/homarr-labs/dashboard-icons/svg/beszel.svg" width="64" height="64" alt="">

**[🇧🇷 Leia em português](./README.pt-BR.md)**

A light dashboard for monitoring this host's resources (CPU/RAM/disk/network/containers).

## Install

```bash
qh beszel            # shows the plan
qh beszel --apply
```

Open `http://<host-ip>:8090` or `https://beszel.<your-tailnet>.ts.net`.

<details>
<summary><b>Manual install</b></summary>

```bash
# 1. Download the units (no need to clone the repository)
mkdir -p ~/.config/containers/systemd/beszel
wget -P ~/.config/containers/systemd/beszel/ \
  https://raw.githubusercontent.com/wallacepnts/quadlet-homelab/main/apps/beszel/beszel-net.network \
  https://raw.githubusercontent.com/wallacepnts/quadlet-homelab/main/apps/beszel/beszel.container \
  https://raw.githubusercontent.com/wallacepnts/quadlet-homelab/main/apps/beszel/beszel-agent.container

# 2. Data directories — a bind mount requires them to exist before the start
mkdir -p ~/.config/containers/volumes/beszel/{hub-data,socket,agent-data}

# 3. Env — download the example, set APP_URL to the real access URL
mkdir -p ~/.config/containers/env
wget -O ~/.config/containers/env/beszel.env \
  https://raw.githubusercontent.com/wallacepnts/quadlet-homelab/main/apps/beszel/.env.example
# edit APP_URL in the downloaded file — the example value with a literal
# "<your-tailnet>" does not start (the hub refuses with "appURL: must be a
# valid URL"), tested in practice; use the real URL (tsdproxy) or
# http://localhost:8090

# 4. Start the hub only, first
systemctl --user start beszel
```

```bash
# 5. KEY — the hub's public key, the same for any agent of this hub;
#    read straight from the file (no need to copy it through the UI)
mkdir -p ~/.config/containers/secrets/beszel
ssh-keygen -y -f ~/.config/containers/volumes/beszel/hub-data/id_ed25519 \
  > ~/.config/containers/secrets/beszel/key.txt
chmod 600 ~/.config/containers/secrets/beszel/key.txt
podman secret create beszel-agent-key ~/.config/containers/secrets/beszel/key.txt

# 6. TOKEN — this one does have to come from the UI: the hub's panel →
#    "Add System" (or Settings → Tokens) → copy the token shown
read -s -p "Beszel token: " BESZEL_TOKEN; echo
echo -n "$BESZEL_TOKEN" > ~/.config/containers/secrets/beszel/token.txt
unset BESZEL_TOKEN
chmod 600 ~/.config/containers/secrets/beszel/token.txt
podman secret create beszel-agent-token ~/.config/containers/secrets/beszel/token.txt

# 7. Start the agent
systemctl --user daemon-reload
systemctl --user start beszel-agent
```

</details>

## Files

```
beszel-agent.container
beszel.container
beszel-net.network
.env.example
install.ini
```

Units in this stack:

- `beszel-agent`
- `beszel`
- `beszel-n`

## Update

```bash
qh beszel --update --apply
```

Pinned to `0.18.7`. Nothing updates on its own — a new version is applied
when you run the command above.

## Backup

```bash
qh beszel --backup --apply --out ~/backups
```

It stops the service, packs the data, the `.env` and the secrets, and starts
it again. Cold on purpose: copying a live database gives an archive that only
fails when you restore it.

To restore, over the current data:

```bash
qh beszel --restore ~/backups/beszel-20260809-1200.tar.gz --apply
```

It asks you to type `beszel` to confirm, because the current data is deleted
before the archive is unpacked.

## Remove

```bash
qh beszel --remove --apply           # stops it, keeps the data
qh beszel --remove --purge --apply   # and deletes volumes, secrets and .env
```

`--purge` asks for the typed name too. The tailnet node is not deregistered by
this — that is done in the Tailscale admin.

## Commands

```bash
systemctl --user status beszel
podman logs -f beszel
```

## Credits

[henrygd/beszel](https://github.com/henrygd/beszel) — MIT

[Official documentation](https://beszel.dev)
