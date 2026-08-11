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
jobs/                the job generator, into ~/.local/bin
install.ini
.env.example
```

## Backup hook

Zerobyte calls it before and after each job, so Restic never copies a database
mid-write.

| Mode | What it does | Downtime |
| --- | --- | --- |
| `sqlite` | Copies the databases with SQLite's online backup API into `<volume>/.dbbackup/` | **none** |
| `stop` | Stops the unit before the copy, starts it after. The default | the whole copy |

```bash
# Which units it may act on, and how. Anything unlisted gets a 404.
systemctl --user edit --full zerobyte-backup-hook.service
#    Environment=ZEROBYTE_HOOK_UNITS=vaultwarden:sqlite,any-sync-bundle:stop

mkdir -p ~/.config/zerobyte-backup-hook
openssl rand -hex 32 > ~/.config/zerobyte-backup-hook/token
chmod 600 ~/.config/zerobyte-backup-hook/token

systemctl --user enable --now zerobyte-backup-hook.service
curl -s http://127.0.0.1:8766/healthz     # {"ok": true}
# Port taken? ZEROBYTE_HOOK_PORT moves it; WEBHOOK_ALLOWED_ORIGINS must agree.
```

Point each job at these, with that token as the secret:

```
http://host.containers.internal:8766/hooks/<unit>/pre-backup
http://host.containers.internal:8766/hooks/<unit>/post-backup
```

### Creating the jobs

One job per folder under `volumes/`, each with the hook mode its data needs.
`zerobyte-jobs.py` works that out and creates them through the API:

```bash
# An API key from Settings -> API keys, saved where the script looks
mkdir -p ~/.config/zerobyte
printf '%s' 'THE_KEY' > ~/.config/zerobyte/api-key && chmod 600 ~/.config/zerobyte/api-key

zerobyte-jobs.py --url https://zerobyte.<your-tailnet>.ts.net            # shows the plan
zerobyte-jobs.py --url https://zerobyte.<your-tailnet>.ts.net --apply
```

The mode comes from the data: SQLite files mean `sqlite`, a Postgres or Mongo
fingerprint means `stop`, anything else needs no hook. A directory it cannot
read also counts as `stop` — that is a container's data owned by a mapped uid,
and guessing `none` there would back up a live database.

Two things it reports instead of doing: `stop` with no unit of that name
(`media-stack` is the case — twelve units share one directory, and one of them
carries a Postgres), and your allowlist, which it prints but does not edit. A
job whose hook is missing from `ZEROBYTE_HOOK_UNITS` gets a 404 and fails.

It only looks at folders belonging to this repository's services. Anything else
under `volumes/` is listed and left alone — with no `install.ini` and no unit,
the mode would be a guess.

A `secrets` job covers `~/.config/containers/secrets`. Restoring a data volume
without them gives a service that starts and does not work: vaultwarden's admin
token no longer matches, excalidash's `JWT_SECRET` logs everyone out. It is one
job because a Zerobyte job covers a single directory — `includePaths` and
`customResticParams` are joined to the volume's path, and cannot reach outside
it.

**Keep the repository's own password somewhere else.** Restic encrypts the
repository with it, and that password is itself a file under `secrets/` — which
now lives *inside* the thing it unlocks. In a total loss that copy is
unreachable: put it in a password manager, or on paper.

Running it again changes nothing — jobs are matched by name.

### More than one repository

With two or more registered, say which one runs the backup; the others become
mirrors of every job:

```bash
zerobyte-jobs.py --url ... --repository <shortId> --apply
zerobyte-jobs.py --url ... --repository <shortId> --no-mirror --apply   # no mirroring
```

A mirror copies the finished snapshot instead of repeating the backup: the
service stops once, and what lands remotely is what was verified here.

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
