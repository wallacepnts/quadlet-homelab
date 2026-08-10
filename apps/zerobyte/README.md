# Zerobyte

<img src="https://cdn.jsdelivr.net/gh/homarr-labs/dashboard-icons/png/zerobyte.png" width="64" height="64" alt="">

**[🇧🇷 Leia em português](./README.pt-BR.md)**

Automates backups (via Restic) of every other service's data in this repository.

## Install

```bash
qh zerobyte            # shows the plan
qh zerobyte --apply
```

Open `http://<host-ip>:4096` or `https://zerobyte.<your-tailnet>.ts.net`.

<details>
<summary><b>Manual install</b></summary>

```bash
# 1. Download the unit (no need to clone the repository)
mkdir -p ~/.config/containers/systemd
wget -P ~/.config/containers/systemd/ \
  https://raw.githubusercontent.com/wallacepnts/quadlet-homelab/main/apps/zerobyte/zerobyte.container

# 2. Directories — a bind mount requires them to exist before the start
mkdir -p ~/.config/containers/volumes/zerobyte/data
mkdir -p ~/backups/zerobyte-local
mkdir -p ~/.config/rclone

# 3. Configure the rclone destination — interactive, and it runs on the
#    HOST (not in the container). Choose the provider (S3, Google Drive,
#    Backblaze B2 and so on) when the wizard asks.
rclone config

# 4. APP_SECRET — a 32+ byte key Zerobyte uses to encrypt what it stores in
#    its own database (this is not the Restic repository's passphrase — that
#    one is set when each repository is created, through the interface)
mkdir -p ~/.config/containers/secrets/zerobyte
openssl rand -hex 32 | tr -d '\n' > ~/.config/containers/secrets/zerobyte/app-secret.txt
chmod 600 ~/.config/containers/secrets/zerobyte/app-secret.txt
podman secret create zerobyte-app-secret ~/.config/containers/secrets/zerobyte/app-secret.txt

# 5. Non-secret env
mkdir -p ~/.config/containers/env
wget -O ~/.config/containers/env/zerobyte.env \
  https://raw.githubusercontent.com/wallacepnts/quadlet-homelab/main/apps/zerobyte/.env.example
# edit ~/.config/containers/env/zerobyte.env: BASE_URL and RESTIC_HOSTNAME

# 6. Start it
systemctl --user daemon-reload
systemctl --user start zerobyte
```

</details>

## Files

```
zerobyte.container   unit
backup-hook/         the hook, into ~/.local/bin and systemd/user
install.ini
.env.example
install.ini
```

## Backup hook

Restic copying a database while it is being written to produces an archive
that only reveals itself as broken when you restore it. The hook is what makes
the scheduled copy cold: Zerobyte calls it before Restic runs and again
afterwards, and it stops and starts the unit around the copy.

It runs on the host's python, not in a container, because a unit cannot stop
itself from inside the container being stopped. Stdlib only, so there is
nothing to install for it.

`qh zerobyte --apply` puts both files in place. Three steps are left:

```bash
# 1. Which units it may stop. Anything not listed gets a 404 — an endpoint
#    that stops services by name is a denial of service with a nice API.
systemctl --user edit --full zerobyte-backup-hook.service
#    Environment=ZEROBYTE_HOOK_UNITS=any-sync-bundle,vaultwarden,karakeep

# 2. The token Zerobyte sends in the X-Zerobyte-Hook-Secret header
mkdir -p ~/.config/zerobyte-backup-hook
openssl rand -hex 32 > ~/.config/zerobyte-backup-hook/token
chmod 600 ~/.config/zerobyte-backup-hook/token

# 3. Start it
systemctl --user enable --now zerobyte-backup-hook.service
curl -s http://127.0.0.1:8765/healthz     # {"ok": true}
```

Then, per backup job, point Zerobyte at the two URLs for that unit and paste
the same token as the secret:

```
http://host.containers.internal:8765/hooks/<unit>/pre-backup
http://host.containers.internal:8765/hooks/<unit>/post-backup
```

`WEBHOOK_ALLOWED_ORIGINS` in this service's `.env` already names that address
— without it Zerobyte refuses to save the URL.

**Which units need it**: the ones holding a database. On a running host, this
finds them:

```bash
podman unshare find ~/.config/containers/volumes -maxdepth 4 \
  \( -name "*.db" -o -name "*.sqlite*" -o -name "PG_VERSION" \) \
  | cut -d/ -f7 | sort -u
```

The pre-backup hook only answers 2xx once the unit has really stopped, which
is what makes Zerobyte wait instead of copying a live database. The post-backup
one answers immediately and starts the unit in the background: a service with
`Notify=healthy` can take longer to come up than Zerobyte's timeout allows, and
a slow start would be reported as a failed backup that in fact succeeded.

## Update

```bash
qh zerobyte --update --apply
```

Pinned to `v0.41.0`. Nothing updates on its own — a new version is applied
when you run the command above.

## Backup

```bash
qh zerobyte --backup --apply --out ~/backups
```

It stops the service, packs the data, the `.env` and the secrets, and starts
it again. Cold on purpose: copying a live database gives an archive that only
fails when you restore it.

To restore, over the current data:

```bash
qh zerobyte --restore ~/backups/zerobyte-20260809-1200.tar.gz --apply
```

It asks you to type `zerobyte` to confirm, because the current data is deleted
before the archive is unpacked.

## Remove

```bash
qh zerobyte --remove --apply           # stops it, keeps the data
qh zerobyte --remove --purge --apply   # and deletes volumes, secrets and .env
```

`--purge` asks for the typed name too. The tailnet node is not deregistered by
this — that is done in the Tailscale admin.

## Commands

```bash
systemctl --user status zerobyte
podman logs -f zerobyte
```

## Credits

[nicotsx/zerobyte](https://github.com/nicotsx/zerobyte) — AGPL-3.0.

[Official documentation](https://zerobyte.app)
