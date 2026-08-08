# Actual Budget — Podman Quadlet (rootless)

**[🇧🇷 Leia em português](./README.pt-BR.md)**

An [Actual Budget](https://actualbudget.org) (sync server) deploy via Podman
Quadlet — self-hosted, local-first personal budgeting.

## Files

```
actual.container   # main unit
```

## Prerequisites

- Rootless Podman with systemd `--user` working

## Installation

```bash
python3 install.py actual-budget            # dry-run: shows what it will do
python3 install.py actual-budget --apply
```

For the local network only, `--access local`; on the tailnet and the LAN,
`--access both`. Adding `--href-local` points the dashboard link at the LAN.
The script creates the directories, writes the `.env`, generates the secrets,
fixes the volumes' ownership, starts the service and prints the address at the
end — see [Installing and operating](../../docs/installing.md).

Open it at `http://localhost:5006` or, through
[tsdproxy](../tsdproxy/) (tailnet), `https://actual.<your-tailnet>.ts.net` —
change that in `homepage.href` in the `.container` and, if you use
`HOMEPAGE_ALLOWED_HOSTS` or a domain of your own, adjust it there too.

<details>
<summary><b>Manual installation</b> (advanced) — the same steps, one at a time</summary>


```bash
# 1. Download the unit (no need to clone the repository)
mkdir -p ~/.config/containers/systemd
wget -P ~/.config/containers/systemd/ \
  https://raw.githubusercontent.com/wallacepnts/quadlet-homelab/main/apps/actual-budget/actual.container

# 2. Data directory — a bind mount requires it to exist before the start.
#    Actual creates server-files/ and user-files/ inside it by itself.
mkdir -p ~/.config/containers/volumes/actual/data

# 3. Env — download the example (TZ is mandatory, the rest is optional — see
#    https://actualbudget.org/docs/config/)
mkdir -p ~/.config/containers/env
wget -O ~/.config/containers/env/actual.env \
  https://raw.githubusercontent.com/wallacepnts/quadlet-homelab/main/apps/actual-budget/.env.example

# 4. Start it
systemctl --user daemon-reload
systemctl --user start actual
```

Open it at `http://localhost:5006` or, through
[tsdproxy](../tsdproxy/) (tailnet), `https://actual.<your-tailnet>.ts.net` —
change that in `homepage.href` in the `.container` and, if you use
`HOMEPAGE_ALLOWED_HOSTS` or a domain of your own, adjust it there too.

</details>

## Where the project lives (the old repo is archived)

`actualbudget/actual-server` was **archived in February 2025** and the code
migrou pro monorepo `actualbudget/actual`, em `packages/sync-server` —
which is why this README's links point there. **The Docker image kept
com o nome antigo**: `docker.io/actualbudget/actual-server` continua
sendo a publicada e ativa (conferido: `latest` e `26.8.0` batem com a
the new repo's `v26.8.0` release). There is no `actualbudget/actual` image —
an archived repo here does not mean an abandoned image.

## Health check

The `HealthCmd` uses the project's own official health check script
(`node /app/src/scripts/health-check.js`, mesmo comando do
[`docker-compose.yml` oficial](https://github.com/actualbudget/actual/blob/master/packages/sync-server/docker-compose.yml)).
The image is Debian, not minimal — it has a shell and Node.js available, so
the
health check funciona de verdade (diferente do any-sync-bundle).

## Auto-update

**On**, unlike the default policy for the rest of the repo
([rule 9](../../docs/conventions.md)) — a deliberate exception, because here
rule 9's two conditions genuinely hold: a real `HealthCmd` (the official
script) gives genuine automatic rollback, and there is no third-party data at
stake.

```ini
Image=docker.io/actualbudget/actual-server:latest
AutoUpdate=registry
```

There is no "patch only" tag for `actual-server` (only exact tags like
`26.7.0`, whose digest never changes, or `latest`/`edge`/`nightly`, which
float across any version) — using `:latest` is the project's own official
recommendation for most users, so that is the one chosen.

```bash
podman auto-update --dry-run              # a preview, applying nothing
podman auto-update --rollback actual      # roll back by hand if needed
```

`podman-auto-update.timer` has to be active for that to run on its own once
a day — `systemctl --user enable --now podman-auto-update.timer` (it is shared
across every service in this repo, so it only needs enabling once).

**Take a backup before any meaningful update** (see the section below) —
automatic rollback covers "it did not become `healthy`", not "it became
healthy but with a silent bug in the data".

## Backup & recovery

All the state (the budget, `server-files`, `user-files`) lives in
`volumes/actual/data/`. Stop the service before copying:

```bash
systemctl --user stop actual
tar -czf actual-backup-$(date +%Y%m%d-%H%M%S).tar.gz \
  -C ~/.config/containers/volumes actual
systemctl --user start actual
```

## Useful commands

```bash
systemctl --user status actual
podman logs -f actual
podman exec actual node /app/src/scripts/health-check.js
```

## Credits

Quadlet deploy based on [Actual Budget](https://github.com/actualbudget/actual).
Original licence: MIT.
