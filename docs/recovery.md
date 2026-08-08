# Recovery and migration

Two different scenarios: the machine died and all you have are the
`.tar.gz` files, or the old server is still up and you want to move house.

## The machine died: recovery from scratch

Different from ["Migrating from another server"](#migrating-from-another-server),
which is a planned move with the old server still up. Here you have the
`.tar.gz` files from `--backup` and nothing else.

**The order is install first, restore only afterwards.** `--restore` does not
install: without the unit in place there is nowhere to extract to and nothing
to start. It refuses, with the command that fixes it, instead of blowing up
halfway through:

```
homebox: nothing to do for `RESTORE (overwrites)`.
  !  homebox is not installed — run this first: python3 install.py homebox --apply
```

### 1. Host

["Step zero"](../README.md#step-zero-preparing-the-host): rootless Podman and
the four folders. Tailscale and `TAILNET` **if** you use the tailnet —
otherwise, `--local` on each installation.

### 2. tsdproxy first, if you use a tailnet

```bash
python3 install.py tsdproxy --apply
```

Before the rest, because it is what makes the others reachable by name. The
authkey is new: the old nodes are left orphaned in the Tailscale admin and
have to be removed by hand.

### 3. Service by service

```bash
python3 install.py <app> --apply
python3 install.py <app> --restore ~/backups/<app>-YYYYMMDD-HHMMSS.tar.gz --apply
```

`--apply` recreates the unit, the folders, the `.env` and the secret;
`--restore` swaps all of that for the backup's content — including recreating
the `podman secret`, which would not exist on a new machine. On a stack, start
only the main unit: `Requires=` pulls the chain (immich, karakeep,
paperless-ngx, authentik, owntracks, zigbee2mqtt).

### 4. Check

```bash
systemctl --user list-units 'podman-*' --failed
python3 updates.py            # the backup may be a version behind
```

### What the backup does not carry

- **The images** — the first `start` pulls them again, and that is the slow
  step.
- **The tailnet identity** — a new node, the same name, a different address.
- **What the migration section already lists**: any-sync-bundle's
  cryptographic identity, and addresses recorded inside the data
  (vaultwarden's `DOMAIN`, wger's `ALLOWED_HOSTS`, any-sync-bundle's
  `externalAddr`) — if the host's name changed, these need reviewing.
- **A service that never had a backup.** `--backup` is ad-hoc; the scheduled
  one is [zerobyte](../apps/zerobyte/).

This ordering is tested: `test_install.py` runs the whole scenario in a
sandbox — install, write data, back up, delete the home, and recover — so
that the runbook does not go stale on its own.

## Migrating from another server

Bringing a backup from a different server (not a fresh installation from
scratch — for that, see each service's "Deploying on another server") onto
this host.

### 1. On the old server

Stop the service and produce the backup as already documented in each
README's Backup section — a `tar` of `volumes/<app>/` — including
`~/.config/containers/secrets/<app>/` too if the service uses secrets: without
them the restored data will not authenticate or decrypt.

### 2. Transfer

Both hosts are already on the same tailnet — `scp`/`rsync` straight between
them over the tailnet is the simplest route: it is already encrypted, with no
intermediate storage and no extra configuration.

### 3. On this server

Install the Quadlet as usual, but **without giving it the first `start`** —
extract the backup into `volumes/<app>/` before that, recreate the secrets
from the copied files (`podman secret create` with the same content), and only
then `systemctl --user start`.

### What to check before calling it migrated

- **Cryptographic identity**: any-sync-bundle and tsdproxy generate their own
  identity on the first run (`peerId`/`peerKey`; the `tsnet` state);
  [Beszel](../apps/beszel/) is the same case (`hub-data/id_ed25519`, the key
  that authenticates every agent registered with that hub). Bringing that data
  over makes the new server *be* the continuation of the old one (the same
  node; existing clients and agents recognise it). Not bringing it produces a
  new, independent instance — the opposite of what each service's "Deploying
  on another server" recommends for a fresh installation.
- **Addresses recorded in the data**: `externalAddr` (any-sync-bundle),
  `DOMAIN` (vaultwarden), `NEXTAUTH_URL`/cookies (karakeep) all reference the
  old server's hostname — adjust them to this host's tailnet address after
  restoring.
- **Version compatibility**: if the old server was on a version well behind
  the tag pinned here, check the changelog first — above all immich (Postgres
  migrations) and vaultwarden (the SQLite schema).
- **Do not delete the old server until you have confirmed** the new one is
  healthy and reachable — if something goes wrong in the migration, you can
  still go back.
