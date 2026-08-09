# Authentik

<img src="https://cdn.jsdelivr.net/gh/homarr-labs/dashboard-icons/svg/authentik.svg" width="64" height="64" alt="">

**[🇧🇷 Leia em português](./README.pt-BR.md)**

An identity server.

## Install

```bash
qh authentik            # shows the plan
qh authentik --apply
```

Open `http://<host-ip>:9000` or `https://authentik.<your-tailnet>.ts.net`.

<details>
<summary><b>Manual install</b></summary>

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

</details>

## Files

```
authentik-postgres.container
authentik-worker.container
authentik.container
authentik-net.network
install.ini
```

Units in this stack:

- `authentik-postgres`
- `authentik-worker`
- `authentik`
- `authentik-n`

## Update

```bash
qh authentik --update --apply
```

Pinned to `16-alpine`, `2026.5.6`. Nothing updates on its own — a new version is applied
when you run the command above.

## Backup

```bash
qh authentik --backup --apply --out ~/backups
```

It stops the service, packs the data, the `.env` and the secrets, and starts
it again. Cold on purpose: copying a live database gives an archive that only
fails when you restore it.

To restore, over the current data:

```bash
qh authentik --restore ~/backups/authentik-20260809-1200.tar.gz --apply
```

It asks you to type `authentik` to confirm, because the current data is deleted
before the archive is unpacked.

## Remove

```bash
qh authentik --remove --apply           # stops it, keeps the data
qh authentik --remove --purge --apply   # and deletes volumes, secrets and .env
```

`--purge` asks for the typed name too. The tailnet node is not deregistered by
this — that is done in the Tailscale admin.

## Commands

```bash
systemctl --user status authentik
podman logs -f authentik
```

## Credits

[goauthentik/authentik](https://github.com/goauthentik/authentik) — MIT

[Official documentation](https://goauthentik.io)
