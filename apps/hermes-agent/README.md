# Hermes Agent

<img src="https://cdn.jsdelivr.net/gh/NousResearch/hermes-agent@main/website/static/img/logo.png" width="64" height="64" alt="">

**[🇧🇷 Leia em português](./README.pt-BR.md)**

A personal AI agent with skills and memory, exposing an OpenAI-compatible API for the other services to call.

## Install

```bash
qh hermes-agent            # shows the plan
qh hermes-agent --apply
```

Open `http://<host-ip>:8642` or `https://hermes.<your-tailnet>.ts.net`.

<details>
<summary><b>Manual install</b></summary>

```bash
# 1. Download the unit (no need to clone the repository)
mkdir -p ~/.config/containers/systemd
wget -P ~/.config/containers/systemd/ \
  https://raw.githubusercontent.com/wallacepnts/quadlet-homelab/main/apps/hermes-agent/hermes-agent.container

# 2. Directories
mkdir -p ~/.config/containers/volumes/hermes-agent/data
mkdir -p ~/.config/containers/env

# 3. Environment
wget -O ~/.config/containers/env/hermes-agent.env \
  https://raw.githubusercontent.com/wallacepnts/quadlet-homelab/main/apps/hermes-agent/.env.example

# 4. Secrets
podman secret create hermes-agent-api-key - <<< "$(python3 -c 'import secrets;print(secrets.token_urlsafe(32))')"
podman secret create hermes-agent-dashboard-password - <<< "$(python3 -c 'import secrets;print(secrets.token_urlsafe(24))')"
podman secret create hermes-agent-dashboard-secret - <<< "$(openssl rand -hex 32)"

# 5. Start it, then run the wizard
systemctl --user daemon-reload
systemctl --user start hermes-agent
podman exec -it hermes-agent hermes setup
```

</details>

## Files

```
hermes-agent.container
.env.example
install.ini
```

## Update

```bash
qh hermes-agent --update --apply
```

Pinned to `v2026.8.3`. Nothing updates on its own — a new version is applied
when you run the command above.

## Backup

```bash
qh hermes-agent --backup --apply --out ~/backups
```

It stops the service, packs the data, the `.env` and the secrets, and starts
it again. Cold on purpose: copying a live database gives an archive that only
fails when you restore it.

To restore, over the current data:

```bash
qh hermes-agent --restore ~/backups/hermes-agent-20260809-1200.tar.gz --apply
```

It asks you to type `hermes-agent` to confirm, because the current data is deleted
before the archive is unpacked.

## Remove

```bash
qh hermes-agent --remove --apply           # stops it, keeps the data
qh hermes-agent --remove --purge --apply   # and deletes volumes, secrets and .env
```

`--purge` asks for the typed name too. The tailnet node is not deregistered by
this — that is done in the Tailscale admin.

## Commands

```bash
systemctl --user status hermes-agent
podman logs -f hermes-agent
```

## Credits

[NousResearch/hermes-agent](https://github.com/NousResearch/hermes-agent) — MIT

[Official documentation](https://hermes-agent.nousresearch.com)
