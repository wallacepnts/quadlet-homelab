# Hermes Agent — Podman Quadlet (rootless)

**[🇧🇷 Leia em português](./README.pt-BR.md)**

A [Hermes Agent](https://github.com/NousResearch/hermes-agent) (Nous Research)
deploy via Podman Quadlet, using the official
`docker.io/nousresearch/hermes-agent` image.

A personal AI agent that keeps skills and memories across sessions, and exposes
an **OpenAI-compatible API** — so [n8n](../n8n/), [Open WebUI](../openwebui/)
or [Home Assistant](../home-assistant/) can point at it the same way they point
at any other model endpoint.

**Read the security section before exposing this one.** It is not a web app
with an agent bolted on: the container ships `docker-cli`, `git`, `ssh`,
`ripgrep` and a Playwright/Chromium browser, and the dashboard can drive them.
Whoever reaches the dashboard runs commands inside this container.

## Architecture

A single container running `gateway run`, with **s6-overlay as PID 1**
supervising the processes inside it. One volume, `/opt/data`, holding
everything: config, provider keys, sessions, skills and memories. The install
at `/opt/hermes` is read-only at runtime and carries no state — the image is
disposable, the volume is not.

Two ports:

| Port | What |
| --- | --- |
| `8642` | the OpenAI-compatible gateway (`/v1/...`, plus an unauthenticated `/health`) |
| `9119` | the web dashboard |

Only **9119 goes on the tailnet** through [tsdproxy](../tsdproxy/). The gateway
stays on the host port, where the other containers reach it — an agent holding
your provider keys does not need a second public door.

## Files

```
hermes-agent.container    # main unit
.env.example              # dashboard user, CORS
install.ini               # secret recipes
```

## Installation

```bash
python3 install.py hermes-agent            # dry-run: shows what it will do
python3 install.py hermes-agent --apply
```

For the local network only, `--access local`; on the tailnet and the LAN,
`--access both`. Adding `--href-local` points the dashboard link at the LAN.
The script creates the directories, writes the `.env`, generates the secrets,
fixes the volumes' ownership, starts the service and prints the address at the
end — see [Installing and operating](../../docs/installing.md).

### Then run the setup wizard, once

The agent has no provider key yet, so it cannot answer anything. The wizard is
interactive and writes into the volume:

```bash
podman exec -it hermes-agent hermes setup
```

It asks for the provider (Anthropic, OpenAI, …) and the key, and stores them
under `/opt/data`. That is why those keys are **not** `podman secret`s here:
they are yours, they are not generated, and upstream's own flow already puts
them in the volume that the backup covers.

Open the dashboard at `https://hermes.<your-tailnet>.ts.net` and log in with
`admin` plus the generated password:

```bash
podman secret inspect --showsecret hermes-agent-dashboard-password
```

<details>
<summary><b>Manual installation</b> (advanced) — the same steps, one at a time</summary>


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

## Security

The dashboard is the agent's console. Three things stand between it and the
tailnet, and all three are on by default here:

1. **Basic auth** — `HERMES_DASHBOARD_BASIC_AUTH_USERNAME` in the `.env`,
   password and cookie secret as `podman secret`s. Upstream leaves all three
   unset, which publishes the dashboard with no login.
2. **`API_SERVER_KEY`** on the gateway, so 8642 is not an open model proxy
   billing your provider account.
3. **The gateway is not on the tailnet** — only the dashboard is proxied.

A tailnet is not authentication: it narrows who can knock, not who gets in.
Every device on your tailnet, and anything running on those devices, can reach
port 9119.

`/health` on 8642 is deliberately unauthenticated — that is what `HealthCmd`
calls, and it answers before the gateway has any key configured.

## Hardening — measured, and what is still open

The image starts as **root on purpose**: s6-overlay's stage-2 hook runs
`usermod`/`groupmod` to remap the UID, chowns `/opt/data`, seeds the config,
and only then drops to the `hermes` user (UID 10000) through `s6-setuidgid`.
That single fact rules out most of [rule 20](../../docs/conventions.md)'s
ladder:

| Setting | Status |
| --- | --- |
| `NoNewPrivileges=true` | on — dropping root to 10000 does not need new privileges |
| `PidsLimit=2048` | on — s6 supervision plus Playwright/Chromium, not the repository's usual 256 |
| `ShmSize=1g` | on — upstream requires it for the browser tools (`--shm-size=1g`) |
| `Memory=4G` | on — upstream recommends 2–4 GB |
| `ReadOnly=true` | **not attempted** — s6-overlay as PID 1, the case rule 20 names |
| `User=` | **not attempted** — the image drops privileges itself; forcing a uid breaks the chown before `s6-setuidgid` runs |
| `DropCapability=ALL` | **not attempted yet** — see below |

`DropCapability=ALL` is the one worth testing. The start-up needs at least
`CHOWN`, `DAC_OVERRIDE`, `FOWNER`, `SETGID` and `SETUID`, and probably `KILL`
(s6 supervises processes owned by another uid). Nobody has measured it here, so
the unit ships without the line rather than with a guessed one. To find out —
and remember `systemctl --user reset-failed hermes-agent` between attempts, or
the rate limit will make a good config look broken:

```bash
podman run --rm -d --name t --cap-drop=ALL \
  --cap-add=CHOWN --cap-add=DAC_OVERRIDE --cap-add=FOWNER \
  --cap-add=SETGID --cap-add=SETUID --cap-add=KILL \
  --shm-size=1g -v /tmp/hermes-test:/opt/data:Z \
  docker.io/nousresearch/hermes-agent:v2026.8.3 gateway run
sleep 60
podman exec t curl -sf -o /dev/null -w "%{http_code}\n" http://127.0.0.1:8642/health
podman logs t | tail -30
podman rm -f t
```

A `200` means the app is alive, not just the container. Record the result here
either way — a capability that was tested and refused is worth as much as one
that worked.

## Auto-update

No `AutoUpdate=` — an explicit tag (`v2026.8.3`), bumped by hand
([rule 9](../../docs/conventions.md)). The tags are calendar versions and
upstream also publishes `latest` and `main`, hence the
`wud.tag.include=^v[0-9]+.[0-9]+.[0-9]+$` in the unit. Some releases carry a
fourth component (`v2026.7.7.2`) and will not match — check
[the releases page](https://github.com/NousResearch/hermes-agent/releases) when
`updates.py` goes quiet for a while.

Config schema migrations run on start (`HERMES_SKIP_CONFIG_MIGRATION` opts
out), so take the backup below before any bump.

## Backup & recovery

```bash
systemctl --user stop hermes-agent
tar -czf hermes-agent-backup-$(date +%Y%m%d-%H%M%S).tar.gz \
  -C ~/.config/containers/volumes hermes-agent
systemctl --user start hermes-agent
```

**The archive contains your provider API keys in clear text** — `hermes setup`
writes them into `/opt/data`. Treat the tarball like the keys themselves; it
does not belong in the same place as the other services' backups unless that
place is encrypted (see [zerobyte](../zerobyte/), which uses Restic).

## Useful commands

```bash
systemctl --user status hermes-agent
podman logs -f hermes-agent
podman exec -it hermes-agent hermes setup      # wizard, first run
podman exec hermes-agent hermes --version
curl -H "Authorization: Bearer $KEY" http://127.0.0.1:8642/v1/models
```

## Credits

Quadlet deploy based on [Hermes Agent](https://github.com/NousResearch/hermes-agent)
by [Nous Research](https://nousresearch.com) (MIT).
