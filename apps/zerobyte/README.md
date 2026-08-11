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
jobs/                the job generator, behind `qh --zerobyte`
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

The allowlist lives in a systemd drop-in (`systemctl --user edit
zerobyte-backup-hook`), not in the shipped unit — and `qh --zerobyte` asks the
running hook which units it knows, then names the ones missing. A unit missing
there is a backup that fails at 03:00 with a 404 nobody is watching.

Each job then carries two URLs, which `qh --zerobyte` writes for you:

```
http://<host-ip>:8766/hooks/<unit>/pre-backup
http://<host-ip>:8766/hooks/<unit>/post-backup
```

The hook runs on the host, because stopping a unit is `systemctl --user`, which
a container cannot reach. But do **not** use `host.containers.internal`: it
only answers from Podman's default network, and every service here is on
`tsdproxy-net`, where it times out and the job fails with `pre webhook failed`.
Pass the host's own address, the tailscale one for preference since it does not
move with DHCP: `qh --zerobyte --hook-host 100.x.y.z`. The same origin has to
be in `WEBHOOK_ALLOWED_ORIGINS`.

`<unit>` says who to act on. The token goes in the `X-Zerobyte-Hook-Secret`
header — without it the hook answers 401, and that is what keeps anything
reaching port 8766 from stopping your services.

### Creating the jobs

One job per folder under `volumes/`, each with the hook mode its data needs.
`qh --zerobyte` works that out and creates them through the API. It reads the
address from `BASE_URL` in the service's own `.env`; `--url` overrides it:

```bash
# An API key from Settings -> API keys, saved where the script looks
mkdir -p ~/.config/zerobyte
printf '%s' 'THE_KEY' > ~/.config/zerobyte/api-key && chmod 600 ~/.config/zerobyte/api-key

qh --zerobyte            # shows the plan
qh --zerobyte --apply
```

The mode comes from the data: SQLite means `sqlite`, a Postgres or Mongo
fingerprint means `stop`, anything else needs no hook. A folder it cannot read
counts as `stop` too — that is a container's data owned by a mapped uid.

`stop` on a folder with no unit of its own stops the stack instead: rule 1
prefixes every unit of a stack with the app's name, so `media-stack` means the
twelve `media-stack-*` units. Twelve stops take longer than Zerobyte's default
60-second webhook timeout, which is why `WEBHOOK_TIMEOUT=180` is in the `.env`.

It reports instead of acting when no unit answers to that name at all, and for
`ZEROBYTE_HOOK_UNITS`, which it prints but does not edit — a job missing from
that list gets a 404 and fails. A folder that is not one of this repository's
services is listed and left alone. Running it again changes nothing: jobs are
matched by name.

Every job excludes `*.tmp`, `*.partial`, `lost+found`, `.Trash-*` and any
directory carrying a `CACHEDIR.TAG`. The list is short because the disposable
files measured across the real volumes add up to single-digit megabytes — a
longer guessed list would only add ways to drop something that mattered. What
an app knows about its own data goes in its `install.ini`:

```ini
[backup]
exclude =
    repositories
```

That is zerobyte's own, and it is worth 15 MB a night: a repository created
through the interface lands inside the volume this job backs up.

Every job also keeps the same window: 7 daily, 4 weekly, 6 monthly, and the
last 3 runs. Zerobyte applies it as `restic forget --prune` right after each
backup, so the space comes back rather than only the snapshot disappearing.
There is no `keepHourly` — the schedule is daily and it would never match.

The container keeps one capability, `DAC_READ_SEARCH`. A service that runs its
database under its own user leaves files owned by a mapped uid, mode 600 — with
every capability dropped, restic reads a directory listing and then fails on
each file (`permission denied` on any-sync-bundle's Mongo). This one bypasses
the read check and nothing else; writing would be `DAC_OVERRIDE`, which it does
not have, and the volumes are mounted read-only anyway.

A `secrets` job covers `~/.config/containers/secrets` — a volume restored
without them gives a service that starts and does not work.

**Keep the repository's own password somewhere else.** It is a file under
`secrets/`, which now lives *inside* the thing it unlocks: a password manager,
or paper.

### Alerts

Its origin has to be in `WEBHOOK_ALLOWED_ORIGINS` in the `.env`, next to the
hook's — Zerobyte refuses to call a URL it was not told about, and says so.
With [ntfy](../ntfy) that is `http://ntfy:2586`, reached by container name over
`tsdproxy-net`, and it needs a token: ntfy here denies by default.

```bash
podman exec ntfy ntfy user add zerobyte          # a publisher, not an admin
podman exec ntfy ntfy access zerobyte backups write-only
podman exec ntfy ntfy token add zerobyte         # goes in the destination
```

A destination created once in **Settings → Notifications** (ntfy, e-mail,
Telegram, Gotify, Discord, Slack) is wired to every job by the same command, on
failure and on warning. Not on success: twelve "it worked" messages a night is
noise you learn to skip, and the one that failed goes with it — which is how a
Mongo can spend a month reporting `warning` with nobody reading it.

### More than one repository

With two or more registered, say which one runs the backup; the others become
mirrors of every job:

```bash
qh --zerobyte --repository <shortId> --apply
qh --zerobyte --repository <shortId> --no-mirror --apply   # turn mirroring off
```

A mirror copies the finished snapshot instead of repeating the backup: the
service stops once, and what lands remotely is what was verified here.
It also triggers the first copy, so the new repository fills up now instead of
at the next run. `--no-mirror` clears the mirrors on every job, which is
otherwise one by one through the interface.

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
