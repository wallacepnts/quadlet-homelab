# Zerobyte — Podman Quadlet (rootless)

**[🇧🇷 Leia em português](./README.pt-BR.md)**

A [Zerobyte](https://github.com/nicotsx/zerobyte) (backup automation built
on [Restic](https://restic.net)) deploy via Podman Quadlet — it schedules,
monitors and manages encrypted backups of every other service in this
repository, with a web interface.

## Architecture

A single container. It mounts as **sources** (read-only) everything this
repository manages — `~/.config/containers/volumes/` and
`~/.config/containers/secrets/` — and two **destinations**: a local directory
on this host and a remote repository via rclone (any of the 40+ supported
providers).

### Why `SecurityLabelDisable=true`

Every service in this repo already uses `:Z` (a **private** SELinux label,
exclusive to that container) on its own volumes. A third container — zerobyte
— trying to read across several directories with different private labels gets
`Permission denied`, even mounting them `:ro`. The way out is turning SELinux
confinement off for zerobyte alone (`--security-opt label=disable`). A
deliberate trade-off: it only mounts those sources read-only, but it loses
SELinux's extra barrier — acceptable here because that is precisely a backup
tool's role (it has to see everything), and the container is not exposed
outside the tailnet.

### rclone is a destination only, not a source

Zerobyte uses rclone in two possible ways: as a **repository** (where the
encrypted backups are stored) or as a **source volume** (mounting cloud
storage as though it were a local disk, via FUSE). Only the first mode is used
here — which is why we do **not** need `SYS_ADMIN` or `--device /dev/fuse`
(required only for the second).

## Files

```
zerobyte.container            # main unit

../any-sync-bundle/backup-webhook/
├── any-sync-bundle-webhook.py       # receives Zerobyte's pre/post-backup webhooks
└── any-sync-bundle-webhook.service  # runs the script above (ordinary systemd, not Quadlet)
```

## Prerequisites

- Rootless Podman with systemd `--user` working
- `rclone` installed on the **host** (only to run the interactive config
  wizard once — the binary does not go into the container)

## Installation

```bash
python3 install.py zerobyte            # dry-run: shows what it will do
python3 install.py zerobyte --apply
```

For the local network only, `--access local`; on the tailnet and the LAN,
`--access both`. Adding `--href-local` points the dashboard link at the LAN.
The script creates the directories, writes the `.env`, generates the secrets,
fixes the volumes' ownership, starts the service and prints the address at the
end — see [Installing and operating](../../docs/installing.md).

Reach it through [tsdproxy](../tsdproxy/) (tailnet) at
`https://zerobyte.<your-tailnet>.ts.net`, or locally at
`http://localhost:4096`.

<details>
<summary><b>Manual installation</b> (advanced) — the same steps, one at a time</summary>


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

Reach it through [tsdproxy](../tsdproxy/) (tailnet) at
`https://zerobyte.<your-tailnet>.ts.net`, or locally at
`http://localhost:4096`.

</details>

## Configuring the two destinations (repositories) through the interface

After the first access, create two repositories in the UI:

- **Local**: the path `/repositories/local` (where `~/backups/zerobyte-local`
  is mounted inside the container)
- **rclone**: choose the remote configured in step 3 of the installation

Each repository asks for its own Restic encryption passphrase — **that
passphrase is in no file in this repository; keep it somewhere safe** (in this
repo's own [vaultwarden](../vaultwarden/), irony aside). Without it, the
snapshots exist but nothing can be restored.

## Creating the backup jobs

The sources available inside the container: `/sources/volumes` (mirroring
`~/.config/containers/volumes/`) and `/sources/secrets` (mirroring
`~/.config/containers/secrets/`). One job per service, or a single job
covering everything — the granularity is yours.

**Careful with anything running Postgres**: Zerobyte has no pre-backup hook
(it runs no command before archiving) — it simply copies whatever it finds at
the configured path. Copying a Postgres's raw files **while the database is
running** is a classic way to produce a corrupt, unrestorable backup. Today
that applies to [immich](../immich/) (`/sources/volumes/immich/postgres`), the
only service with Postgres in this repository.

Two ways out, neither automatic:

- **A cold backup** — stop the stack before the job runs. That is what
  [immich's README](../immich/README.md#backup--recovery) describes, and what
  the any-sync-bundle section below automates through a webhook.
- **A logical dump** — a `pg_dump` on a systemd timer, excluding
  `immich/postgres` from the job and including the dump file instead. The two
  schedules are not synchronised automatically: the timer has to run first,
  and keeping that order is your responsibility.

  ```bash
  podman exec immich-postgres pg_dump -U immich immich \
    | gzip > ~/.config/containers/volumes/immich/pg-dump/immich.dump.gz
  ```

This repository does not version a ready-made timer for the dump — the route
recommended here is the cold backup, which has no guessed window.

**any-sync-bundle** (AIO mode — the bundle's badger storage plus Mongo and
Redis embedded in a single container) carries the same kind of risk, but with
no `pg_dump`/`BGSAVE` way out: copying Mongo's and badger's raw files while
the process is writing is the classic recipe for a corrupt, unrestorable
backup. The solution here was different — stopping the whole container before
Restic runs and bringing it back afterwards, rather than producing dumps. A
complete cold backup, with no risk of corruption (see the *Backup & recovery*
section of [any-sync-bundle's README](../any-sync-bundle/README.md)).

Unlike the timer-based dump (a fixed schedule, with no guarantee of
synchronisation with the job), here
[Zerobyte's pre/post-backup webhook](https://zerobyte.app/docs/guides/backup-webhooks)
can genuinely be used: the pre-backup hook is blocking (Restic only runs after
a 2xx, and aborts if the webhook fails or times out), so there is no guessed
window — the stack is only down while the backup is actually running.

```bash
# 1. A shared token (the same header on both of the job's hooks)
mkdir -p ~/.config/any-sync-bundle-webhook
openssl rand -hex 32 | tr -d '\n' > ~/.config/any-sync-bundle-webhook/token
chmod 600 ~/.config/any-sync-bundle-webhook/token

# 2. The script plus the unit (stdlib only, with no dependency to install;
#    no need to clone the repository)
mkdir -p ~/.local/bin
wget -O ~/.local/bin/any-sync-bundle-webhook.py \
  https://raw.githubusercontent.com/wallacepnts/quadlet-homelab/main/apps/any-sync-bundle/backup-webhook/any-sync-bundle-webhook.py
chmod 700 ~/.local/bin/any-sync-bundle-webhook.py
wget -P ~/.config/systemd/user/ \
  https://raw.githubusercontent.com/wallacepnts/quadlet-homelab/main/apps/any-sync-bundle/backup-webhook/any-sync-bundle-webhook.service
systemctl --user daemon-reload
systemctl --user enable --now any-sync-bundle-webhook.service

# 3. WEBHOOK_ALLOWED_ORIGINS=http://host.containers.internal:8765 has to be
#    in zerobyte.env already (step 5 of the installation above) before
#    restarting zerobyte
systemctl --user restart zerobyte
```

In Zerobyte's UI, the **Advanced** section of the any-sync-bundle job:

| Hook | URL | Header |
| --- | --- | --- |
| Pre-backup | `http://host.containers.internal:8765/hooks/any-sync-bundle/pre-backup` | `X-Zerobyte-Hook-Secret: <the token's contents>` |
| Post-backup | `http://host.containers.internal:8765/hooks/any-sync-bundle/post-backup` | `X-Zerobyte-Hook-Secret: <the token's contents>` |

`host.containers.internal` is rootless Podman's special hostname (via pasta)
for reaching the host from inside a container — it does not need to be on
zerobyte's network and needs no published port.

**A deliberate trade-off:** for `host.containers.internal` to reach the
service, it has to listen on `0.0.0.0` (it cannot be restricted to a single
interface — tested in practice, that special Podman address does not exist as
a real IP on the host's side, only through the network's NAT). That leaves
port 8765 technically reachable from the LAN/tailnet too, not only from the
container — the only barrier is the token in the header
(`hmac.compare_digest`, a constant-time comparison). Without that token,
anyone who reaches the port can stop the container. For one more layer,
restrict port 8765 in the host's firewall to accept only from Podman's subnet.

The post-backup hook fires `systemctl --user start` in the background and
answers immediately — the container uses `Notify=healthy` (so `start` only
returns once the healthcheck passes), which can exceed `WEBHOOK_TIMEOUT`'s
60s default; since a post-backup failure only becomes a warning in Zerobyte
(it does not undo the backup that already ran), answering straight away beats
risking a timeout with the container still stopped.

## Auto-update

No `AutoUpdate=` — an explicit tag (`v0.41.0`), bumped by hand
(rule 9 of the [conventions](../../docs/conventions.md)). An Alpine image with `wget` and a real `HealthCmd` configured — genuine
auto-update could be enabled if you wanted, but for a tool that holds the
passphrase to all your backups, manual review is preferred.

## Useful commands

```bash
systemctl --user status zerobyte
podman logs -f zerobyte
podman exec zerobyte sh -c "ls /sources/volumes"   # check what is visible
```

## Credits

Quadlet deploy based on [Zerobyte](https://github.com/nicotsx/zerobyte),
by [nicotsx](https://github.com/nicotsx). Original licence: AGPL-3.0.
