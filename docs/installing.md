# Installing and operating services

Everything through [`install.py`](../install.py): install, update, back up,
restore and remove. It derives the steps from the unit itself — see
["The unit already is the manifest"](#installing-a-service) below.

## Installing a service

Each service's README carries the `wget`/`mkdir`/`podman secret` commands by
hand, and that still holds. `install.py` does the same thing by reading the
unit:

```bash
python3 install.py --list
python3 install.py traccar                 # dry-run: only shows what it would do
python3 install.py traccar --apply
python3 install.py traccar --update        # re-copies the units and restarts
python3 install.py traccar --reinstall     # overwrites env, config and secrets
python3 install.py traccar --remove        # stops and removes the units, keeps data
python3 install.py traccar --remove --purge   # + deletes volumes, secrets and env
python3 install.py traccar --backup --out ~/backups   # data, cold
python3 install.py traccar --restore ~/backups/traccar-....tar.gz
python3 install.py traccar --apply --access both     # local + tailnet
python3 install.py traccar --apply --prefix /tmp/test   # sandbox
```

Every mode is **dry-run by default**; `--apply` executes.

**Several at once**, and `--all` to act on all 48:

```bash
python3 install.py memos ntfy homebox --apply
python3 install.py --all --update --apply     # after a round of bumps
python3 install.py memos ntfy --backup --apply --out ~/backups
```

**One unit out of a stack** — name the unit instead of the folder. Useful when
a folder holds many services and you only want one of them:

```bash
python3 install.py media-stack-jellyfin --apply   # just Jellyfin, not the other 11
python3 install.py toolbx-ubuntu --apply          # just the Ubuntu box
python3 install.py immich-postgres --update       # one piece of a stack
```

The basename is unambiguous by [rule 1](./conventions.md) — one basename, one
unit, across the whole repository — so there is nothing to disambiguate, and
`check.py` fails the build if that ever stops being true. What the filter keeps:
that unit's volumes, env file and secrets, and **every `.network` in the folder**,
because `Network=` names the file and Quadlet cannot generate the unit without
it. The destination stays the stack's subfolder.

This works for install, `--reinstall` and `--update` only. `--backup`,
`--restore` and `--remove` act on the service's volume root, which the units of
a stack share — `--remove --purge` on one unit would delete all of the stack's
data — so those refuse a unit name and ask for the folder.

Each service is separated by a rule, and the tally comes at the end (`3/3 ok`,
or the list of what failed). The names are checked **before** it starts —
finding out halfway through that the third one does not exist would leave the
job half done. `--restore` is the exception and accepts a single service,
because a `.tar.gz` belongs to one service. With `--purge`, each one asks for
its own typed confirmation, on purpose.

**`--update` is the only one you use every week.** It is the `wget -O` over
the top described in the lifecycle, turned into a script: a version bump in
the repository does not change the file already installed on the host, and
that is what it fixes. It touches no volume, no `.env` and no secret.

**Installing over the top does not delete what you edited.** An existing
`.env`, config file or secret is kept, with a warning — they hold passwords,
tokens and the already-closed signup. To overwrite deliberately, `--reinstall`.

**`--remove` keeps the data** and says how much was kept; `--purge` deletes
volumes, secrets and the `.env`, and requires you to **type the service's
name** to confirm. In both cases it reminds you that tsdproxy does not
deregister the tailnet node — that is done in the Tailscale admin.

**`--backup` stops the service before packing**, and brings it back
afterwards. Cold on purpose: copying SQLite or Postgres while the process is
writing is the classic recipe for an archive that only reveals itself as
corrupt when you try to restore it — the same warning
[zerobyte](../apps/zerobyte/) makes. The volumes, the secrets and the `.env`
go into the `.tar.gz`; the last two are tiny and they are what makes the
backup restorable, because without them the data comes back but the service
does not start. The restore line is printed at the end:

```
tar xzf homebox-20260807-184209.tar.gz -C ~/.config/containers
```

It does **not replace** [zerobyte](../apps/zerobyte/), which is the scheduled,
encrypted, off-machine backup. This one is the "before bumping the version"
backup, which is exactly when this repository's lifecycle says to have one.

**`--restore` is a swap, not a merge.** It deletes the volume root before
extracting — without that, `tar x` would overwrite what is in the archive and
leave the rest, and a `-wal` from the current state on top of an old `.db` is
precisely how a SQLite database gets corrupted. It only deletes the roots the
archive actually carries, so a partial backup does not take away what it
cannot put back.

Before anything else it checks that the `.tar.gz` belongs to **that service**
(restoring homebox's backup over traccar would wipe out both at once) and asks
for the typed name to confirm, like `--purge`. After extracting, it reapplies
ownership on services with `User=` — a file coming from another machine
carries a subuid that may not be this one's.

### Local, tailnet, or both

Local access **works in all three modes**, because every unit publishes a port
on the host — and [tsdproxy](../apps/tsdproxy/) depends on exactly that port
to reach the service. What `--access` decides is whether the service registers
a node on the tailnet:

```bash
python3 install.py memos --apply --access local     # LAN only
python3 install.py memos --apply --access tailnet   # default
python3 install.py memos --apply --access both
```

| | registers a tailnet node? | `homepage.href` |
| --- | --- | --- |
| `local` | no — the `tsdproxy.*` labels are commented out | `http://<lan-ip>:<port>` |
| `tailnet` *(default)* | yes | `https://<app>.<tailnet>.ts.net` |
| `both` | yes | `https://<app>.<tailnet>.ts.net` |

The dashboard link follows what makes sense for each mode: in `local` only the
LAN address exists; in `tailnet` and `both` the link is the tailnet name,
**which works from anywhere** — the right address to click both at home and
away.

Whoever prefers the short link, straight to the LAN without the proxy hop,
adds `--href-local`:

```bash
python3 install.py memos --apply --access both --href-local
# on the tailnet, but the dashboard points at http://192.168.1.12:5230
```

**One flag, one meaning**: `--access` decides the tailnet node, `--href-local`
decides the dashboard link. `--local` is just shorthand for `--access local` —
and combining the two is an error rather than a guess.

Under `--access local` the tsdproxy labels are **commented out, not deleted**:
the unit still says what would exist, and changing your mind is a matter of
running `--update` with another mode.

**`--prefix` is a real sandbox**: besides redirecting the paths, it does *not*
run `systemctl` or `podman`, it only announces them. Without that, a
`--remove --prefix /tmp/test` would take down the real service, because the
prefix does not change the unit's name.

**The unit already is the manifest.** Almost everything a README tells you to
do is already declared in the `.container` itself, just in running text:

| Directive | Becomes |
| --- | --- |
| `Volume=` | a `mkdir -p` of the host path |
| `EnvironmentFile=` | the `.env.example`'s destination |
| `Secret=` | the `podman secret create` calls |
| `User=` | the volume's `podman unshare chown -R` |
| the number of Quadlet files | loose vs. subfolder in `systemd/` |

What is left over is small, and lives in `apps/<app>/install.ini`: **each
secret's recipe** (the right random value for it, or the instruction when it
cannot be generated) and the **destination of a config file that lands inside
a directory volume** — two cases today, donetick and copyparty.

```ini
[secrets]
homebox-api-key-pepper = rand-base64 48
monica-app-key = shell printf 'base64:%s' "$(openssl rand -base64 32)"
tsdproxy-authkey = manual an auth key generated in the Tailscale admin
```

The forms are `rand-hex N`, `rand-base64 N`, `rand-urlsafe N`, `rand-alnum N`,
`shell <command>` and `manual <instruction>`. The `manual` ones are **not**
invented — a Tailscale auth key, vaultwarden's argon2 hash and vaultzap's
password all come from outside.

In a terminal, `--apply` **asks for the `manual` values right there**, with
the input hidden:

```
  vaultzap-basic-auth
  choose `user:password` and create the secret by hand (see the README)
  value (not echoed):
```

Leaving it blank skips it, and the value stays pending as before. Outside a
terminal (a pipe, cron, `--prefix`) it never hangs waiting: it goes back to
just warning. The file is written **without a trailing `\n`** on purpose —
several apps read the raw value, and the newline becomes part of the password.

`check.py` verifies that every `Secret=` has a recipe, so a service does not
stop halfway through installation for the want of one.

At the end (and in the dry-run) it prints **where to reach it**, also derived
from the unit: `tsdproxy.port.web` says which internal port is the web one —
which matters on a service that publishes more than one, like traccar with the
OsmAnd protocol port — the matching `PublishPort` gives the host one, and
`homepage.href` already carries the tailnet URL, with only `${TAILNET}` left
to resolve.

```
http://192.168.1.12:8099
https://traccar.your-tailnet.ts.net
```

A multi-container stack lists one per unit. Without a tailnet, only the first
line.

**Validated against the real installation**: running `install.py --prefix`
into an empty directory and comparing with what is on the host reproduces it
file by file across the 10 services that were checked. The two differences
that turned up were host drift, not script bugs — one of them a stale comment
left over from a manual edit.

## Lifecycle

[`install.py`](#installing-a-service) covers the whole cycle, always dry-run
by default — `--apply` is what executes:

```bash
python3 install.py <app> --update              # re-copies the unit and restarts
python3 install.py <app> --reinstall           # overwrites .env, config and secrets
python3 install.py <app> --backup --out ~/backups
python3 install.py <app> --restore ~/backups/<app>-....tar.gz
python3 install.py <app> --remove              # keeps the data
python3 install.py <app> --remove --purge      # deletes volumes, secrets and .env
```

Underneath it is ordinary systemd, and that still applies for inspecting:

```bash
systemctl --user status <app>
journalctl --user -u <app> -f
podman exec -it <container> sh   # if the image has a shell
systemctl --user daemon-reload   # after editing a unit by hand
```

On a real server: `loginctl enable-linger <user>` — without it, the services
disappear when the login session ends.

### A standalone service (most of them)

Straightforward: `systemctl --user restart <app>`.

### A service with dependencies (immich, owntracks, paperless-ngx)

- **Starting**: the main unit only — `systemctl --user start <app>` already
  brings the dependencies up first, via `Requires=`.
- **Restarting everything**: likewise, a `restart` on the main unit recreates
  the right chain.
- **Restarting a single dependency** (the database alone, say, to apply
  config): it also **stops** whoever requires it (rule 8) — if the dependency
  falls into a crash loop in that window, whatever depended on it does not
  come back on its own afterwards. In that case: wait for the dependency to go
  `healthy` and only then run `systemctl --user start <app>` by hand.
- **Taking everything down deliberately**: stop them all at once, not just the
  main unit —
  ```bash
  systemctl --user stop <app> <app>-dependency-1 <app>-dependency-2
  ```
  (this is the pattern used in each service README's backup steps, for exactly
  this reason — stopping only the main unit leaves the dependencies alive and
  writing while the backup runs.)

### Checking afterwards

```bash
systemctl --user is-active <app>          # quick, status only
journalctl --user -u <app> -f              # live logs
podman ps --filter "name=<app>"            # confirms it is really healthy
```

### Removing the unit (keeps the data)

```bash
systemctl --user stop <app> [<dependencies>]
# A loose service (1 file):
rm ~/.config/containers/systemd/<app>.container
# A service in a subfolder (2+ files — see "The standard layout"):
rm -r ~/.config/containers/systemd/<app>/
systemctl --user daemon-reload
systemctl --user reset-failed   # clears any residual failure state
```

After the `daemon-reload` the unit disappears from `systemctl --user status`.
The data stays in `volumes/<app>/` — it can be reinstalled later without
losing anything.

### Deleting everything (destructive — data, secrets, config)

```bash
# 1. Confirm the unit is already removed (the step above)

# 2. Data — IRREVERSIBLE without a backup
rm -rf ~/.config/containers/volumes/<app>/

# 3. Env
rm -f ~/.config/containers/env/<app>.env

# 4. Secrets, if the service used any (most of them today: beszel, gitea,
#    immich, karakeep, n8n, openwebui, owncloud, owntracks, paperless-ngx,
#    tsdproxy, vaultwarden, zerobyte — check the service's README if you are
#    not sure)
podman secret rm <app>-secret-name
rm -rf ~/.config/containers/secrets/<app>/
```

Two traps specific to this repository:

- **tsdproxy does not deregister the tailnet node by itself** — deleting the
  container does not remove the device from the Tailscale admin (this is how
  the duplicate `dash`/`dash-1` entries mentioned earlier came about). To get
  rid of it for good, remove it by hand at
  https://login.tailscale.com/admin/machines.
- **Homepage needs no cleanup** — it only reads labels from live containers
  over the socket; an entry disappears from the list by itself as soon as the
  container stops existing.
