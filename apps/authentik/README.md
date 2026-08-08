# Authentik — Podman Quadlet (rootless)

**[🇧🇷 Leia em português](./README.pt-BR.md)**

Deploy do [Authentik](https://goauthentik.io) (servidor de identidade —
SSO, MFA, OIDC/SAML) via Podman Quadlet, seguindo o
[`compose.yml`](https://docs.goauthentik.io/compose.yml) oficial.

**Deployed for testing and exploration only** — see "An important
limitation" below before expecting it to protect other apps here
sozinho.

## An important limitation: no automatic forward-auth here

Authentik's most common use is in front of other apps, requiring a login
before granting access (SSO — a single login protecting everything behind the
proxy). Isso normalmente depende do proxy da frente saber conversar com
o Authentik (**forward-auth**, mesmo mecanismo do Authelia) — o
[tsdproxy](../tsdproxy/) (the proxy used in this repository) **does not
support
isso**, testado/pesquisado antes de decidir implantar.

Authentik has a way out that Authelia does not: **outposts in "Proxy
Mode"** — um container extra por app protegido, que funciona como
a full reverse proxy (it receives the request, checks the login, and only
then forwards it to the real app) — in that mode, tsdproxy can be pointed at
the
outpost em vez de apontar direto pro app, sem precisar de forward-auth
anywhere. **Not deployed yet** — it is documented here as the next step, app
by app, if and when it makes sense to use it for real
(cada app protegido = mais um outpost container).

For now, this deploy is the **core** alone (the portal plus admin) — you can
explore the interface, create users and groups and configure OIDC/SAML
providers, with no other service here depending on it.

## Architecture

Three containers on the `authentik-net.network` network:

- `authentik-postgres` — the database (plain Postgres, **with no SQLite
  option** — unlike most apps here, this is Authentik's own requirement).
- `authentik` — the server (port `9000` HTTP / `9443` HTTPS, only `9000`
  published — TLS is already handled by tsdproxy at the tailnet's edge).
- `authentik-worker` — tarefas em segundo plano (envio de e-mail,
  outposts, other asynchronous tasks) — it runs as **root inside the
  container** (`User=0`, igual ao compose oficial) e tem acesso ao
  the Podman socket, needed only once outposts come into use.

`authentik`/`authentik-worker` only start once Postgres reports `healthy`
(`Requires=`/`After=`, the same pattern as
[karakeep](../karakeep/)/[immich](../immich/)).

**No `AUTHENTIK_REDIS__*`** — recent Authentik versions no longer require
Redis (confirmed in the current official `compose.yml`, which only has
`postgresql`+`server`+`worker`) — arquitetura mais enxuta do que guias
antigos sugerem.

## Files

```
authentik-net.network         # rede dedicada
authentik-postgres.container  # banco
authentik.container            # server (portal + admin)
authentik-worker.container     # tarefas em segundo plano
```

## Prerequisites

- Rootless Podman with systemd `--user` working
- `podman.socket` enabled (for the worker only — `systemctl --user enable
  --now podman.socket` if it is not already, the same prerequisite as
  [tsdproxy](../tsdproxy/)/[Beszel](../beszel/))

## Installation

```bash
python3 install.py authentik            # dry-run: shows what it will do
python3 install.py authentik --apply
```

For the local network only, `--access local`; on the tailnet and the LAN,
`--access both`. Adding `--href-local` points the dashboard link at the LAN.
The script creates the directories, writes the `.env`, generates the secrets,
fixes the volumes' ownership, starts the service and prints the address at the
end — see [Installing and operating](../../docs/installing.md).

Open `http://<host-ip>:9000` (or through [tsdproxy](../tsdproxy/) at
`https://authentik.<your-tailnet>.ts.net`) — it redirects to `/setup` on first
access; create the admin account there (called `akadmin` by default).

<details>
<summary><b>Manual installation</b> (advanced) — the same steps, one at a time</summary>


```bash
# 1. Download the units (no need to clone the repository)
mkdir -p ~/.config/containers/systemd/authentik
wget -P ~/.config/containers/systemd/authentik/ \
  https://raw.githubusercontent.com/wallacepnts/quadlet-homelab/main/apps/authentik/authentik-net.network \
  https://raw.githubusercontent.com/wallacepnts/quadlet-homelab/main/apps/authentik/authentik-postgres.container \
  https://raw.githubusercontent.com/wallacepnts/quadlet-homelab/main/apps/authentik/authentik.container \
  https://raw.githubusercontent.com/wallacepnts/quadlet-homelab/main/apps/authentik/authentik-worker.container

# 2. Data directories — a bind mount requires them to exist before the start
mkdir -p ~/.config/containers/volumes/authentik/{postgres,data,certs}

# 3. Secrets — the Postgres password plus Authentik's signing key.
#    IMPORTANT: no newline in the file (`print(..., end='')`, not a plain
#    `print(...)`) — tested in practice, Postgres tolerates the trailing
#    newline in the password (its init script discards it), but Authentik
#    does not: authentication fails in a loop ("password authentication
#    failed") with the SAME password, purely because one side compares the
#    string with a trailing \n and the other without.
mkdir -p ~/.config/containers/secrets/authentik
python3 -c "import secrets; print(secrets.token_urlsafe(32), end='')" \
  > ~/.config/containers/secrets/authentik/postgres-password.txt
python3 -c "import secrets; print(secrets.token_urlsafe(48), end='')" \
  > ~/.config/containers/secrets/authentik/secret-key.txt
chmod 600 ~/.config/containers/secrets/authentik/*.txt
podman secret create authentik-postgres-password \
  ~/.config/containers/secrets/authentik/postgres-password.txt
podman secret create authentik-secret-key \
  ~/.config/containers/secrets/authentik/secret-key.txt

# 4. Start it (the server brings Postgres up by itself, via Requires=)
systemctl --user daemon-reload
systemctl --user start authentik
systemctl --user start authentik-worker
```

Open `http://<host-ip>:9000` (or through [tsdproxy](../tsdproxy/) at
`https://authentik.<your-tailnet>.ts.net`) — it redirects to `/setup` on first
access; create the admin account there (called `akadmin` by default).

</details>

## Auto-update

No `AutoUpdate=` on any of the three — explicit tags (`2026.5.6`), bumped by
hand ([rule 9](../../docs/conventions.md)). No `HealthCmd` on Postgres or the
worker, following the internal-dependency pattern used across the rest of the
repository; `authentik`
(server) tem `HealthCmd` real (`/-/health/live/`) — daria pra habilitar
working rollback on it, but users, groups and configuration are real data —
review by hand before updating.

## Backup & recovery

```bash
systemctl --user stop authentik authentik-worker authentik-postgres
tar -czf authentik-backup-$(date +%Y%m%d-%H%M%S).tar.gz \
  -C ~/.config/containers/volumes authentik
systemctl --user start authentik-postgres authentik authentik-worker
```

`~/.config/containers/secrets/authentik/` (the Postgres password plus the
signing key) needs a separate backup too — without the `secret-key`, existing
sessions and tokens become invalid even after restoring the database.

## Useful commands

```bash
systemctl --user status authentik-postgres authentik authentik-worker
podman logs -f authentik
podman logs -f authentik-worker
podman exec authentik curl -fsS http://127.0.0.1:9000/-/health/live/
```

## Credits

Quadlet deploy based on [Authentik](https://github.com/goauthentik/authentik)
(MIT, with enterprise modules under their own licence).
