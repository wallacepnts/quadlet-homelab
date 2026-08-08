# Beszel — Podman Quadlet (rootless)

**[🇧🇷 Leia em português](./README.pt-BR.md)**

Deploy do [Beszel](https://beszel.dev) (dashboard leve de monitoramento
monitoring — CPU, RAM, disk, network, containers — with history and
alertas) via Podman Quadlet, seguindo o
[guia oficial](https://www.beszel.dev/guide/getting-started) e a
variante ["same-system"](https://github.com/henrygd/beszel/tree/main/supplemental/docker/same-system)
(hub e agent monitorando o mesmo host).

## Architecture

Arquitetura hub + agent, dois containers:

- **`beszel`** (hub) — painel web + banco de dados (SQLite/PocketBase),
  port `8090`, on its own bridge network (`beszel-net`).
- **`beszel-agent`** — it collects this host's metrics and reports them to
  the hub. **On the `host` network, not a bridge** (deliberately breaking this
  repository's default): the agent reports the host interfaces' real traffic;
  on an isolated bridge network it would only see its own container's internal
  veth — numbers of no use for network monitoring.

**Hub e agent no mesmo host conectam via socket Unix compartilhado**
(`beszel_socket`, a bind mount shared by both), not over TCP with a token
exposto na rede — mais simples e mais seguro que a variante
standard multi-host route (used when the agent runs on *another* machine,
outside this repository's scope).

**Container monitoring**: the agent reads the Podman socket
(`%t/podman/podman.sock`, exposto como `/var/run/docker.sock` — API
(Docker-compatible) to list and monitor the other containers on this
host, mesmo mecanismo do [tsdproxy](../tsdproxy/).

**Images with no shell** (a single static binary, `/beszel`/`/agent`) — the
`HealthCmd` uses `CMD`, not `CMD-SHELL` (tested in practice: `CMD-SHELL` fails
because there is no `/bin/sh`); the binaries themselves have a subcommand
`health` feito pra isso.

## Files

```
beszel-net.network       # rede do hub
beszel.container          # hub — painel + banco
beszel-agent.container    # the agent — collects this host's metrics
```

## Prerequisites

- Rootless Podman with systemd `--user` working
- `podman.socket` enabled (the same prerequisite as
  [tsdproxy](../tsdproxy/) — `systemctl --user enable --now podman.socket`
  if it is not already)
- `ssh-keygen` on the host (only for step 5 below, to read the public key
  of the
  hub direto do arquivo, sem precisar copiar pela UI)

## Installation

```bash
python3 install.py beszel            # dry-run: shows what it will do
python3 install.py beszel --apply
```

For the local network only, `--access local`; on the tailnet and the LAN,
`--access both`. Adding `--href-local` points the dashboard link at the LAN.
The script creates the directories, writes the `.env`, generates the secrets,
fixes the volumes' ownership, starts the service and prints the address at the
end — see [Installing and operating](../../docs/installing.md).

Open `http://<host-ip>:8090` (or through [tsdproxy](../tsdproxy/) at
`https://beszel.<your-tailnet>.ts.net`) and create the admin account on first
access.

<details>
<summary><b>Manual installation</b> (advanced) — the same steps, one at a time</summary>


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

Open `http://<host-ip>:8090` (ou via [tsdproxy](../tsdproxy/) em
`https://beszel.<your-tailnet>.ts.net`) e criar a conta de admin no
primeiro acesso.

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

The system shows up as "online" in the hub's panel as soon as the agent
connects over the shared socket.

</details>

## Monitoring extra disks and partitions

An additional bind mount at `/extra-filesystems/<name>` in
`beszel-agent.container`:

```ini
Volume=/mnt/disco1:/extra-filesystems/disco1:ro
```

## Auto-update

No `AutoUpdate=` on either — explicit tags (`0.18.7`), bumped by hand
([rule 9](../../docs/conventions.md)). Both images have a real healthcheck
(`/beszel health`/`/agent health`, tested in practice) — it would be possible
to
habilitar `AutoUpdate=registry` com rollback funcional, mas mantido
manual as this repository's default.

## Backup & recovery

```bash
systemctl --user stop beszel-agent beszel
tar -czf beszel-backup-$(date +%Y%m%d-%H%M%S).tar.gz \
  -C ~/.config/containers/volumes beszel
systemctl --user start beszel beszel-agent
```

`hub-data/id_ed25519` is included in the backup — restoring preserves the
same KEY, and the agents keep authenticating without reconfiguration.

## Useful commands

```bash
systemctl --user status beszel beszel-agent
podman logs -f beszel
podman logs -f beszel-agent
podman exec beszel /beszel health --url http://localhost:8090
podman exec beszel-agent /agent health
```

## Credits

Quadlet deploy based on [Beszel](https://github.com/henrygd/beszel)
(MIT).
