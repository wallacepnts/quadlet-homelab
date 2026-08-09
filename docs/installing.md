# Installing and operating

Everything through `qh`. Every mode is **dry-run by default**; `--apply`
executes.

```bash
qh --list
qh traccar                            # shows what it would do
qh traccar --apply
qh traccar --update --apply           # re-copies the units, restarts, keeps data
qh traccar --reinstall --apply        # overwrites env, config and secrets
qh traccar --remove --apply           # stops it, keeps the data
qh traccar --remove --purge --apply   # + deletes volumes, secrets and env
qh traccar --backup --apply --out ~/backups
qh traccar --restore ~/backups/traccar-....tar.gz --apply
```

Several at once, or `--all` for every service:

```bash
qh memos ntfy homebox --apply
qh --all --update --apply
```

One unit out of a stack — name the unit instead of the folder:

```bash
qh media-stack-jellyfin --apply
qh immich-postgres --update --apply
```

This works for install, `--reinstall` and `--update`. `--backup`, `--restore`
and `--remove` act on the whole folder's data, so they take the folder name.

## What each mode does

**`--update`** is the one you use weekly: a version bump in the repository does
not change the file already on the host, and this is what fixes it. It touches
no volume, no `.env` and no secret. A moving tag (`latest`) is always pulled; a
pinned one only when the host does not have it.

**A plain install over an installed service refuses** and names the two ways
forward:

```
filebrowser: already installed — 1 of 1 unit(s) in ~/.config/containers/systemd
  --update     re-copies the units and restarts, keeping data, env and secrets
  --reinstall  installs again, OVERWRITING env, config and secrets
```

**After a `--remove`**, installing again finds the `.env`, config and secrets
still in place and keeps them, with a warning. `--reinstall` overwrites them.

**`--backup` stops the service** before packing and starts it again. The
`.tar.gz` carries the volumes, the secrets and the `.env` — the last two are
tiny and are what makes it restorable.

**`--restore` is a swap, not a merge.** It deletes the volume root before
extracting, checks the archive belongs to that service, and asks for the typed
name to confirm.

## Access

```bash
qh traccar --apply --access local     # no tsdproxy, dashboard link to the LAN
qh traccar --apply --access tailnet   # default
qh traccar --apply --access both
qh traccar --apply --href-local       # on the tailnet, dashboard link to the LAN
```

`--local` is shorthand for `--access local`. The `tsdproxy.*` labels are
commented out rather than deleted, so changing your mind later is another
install with a different mode.

## Credentials

When a service has a login, the install ends with it:

```
  user:     admin
  password: 7x63tlKq...
```

This shows in the dry-run too, so `qh <app>` on something already installed is
also the answer to "what was my password". It lands in your scrollback.

To type the secrets instead of generating them:

```bash
qh filebrowser --reinstall --ask-secrets --apply
```

Enter takes the generated value, so you can type the one password you log in
with and leave the rest random. Needs a terminal and `--apply`.

## Questions during the install

Some `.env` values are a choice from a known list and only apply on the first
start — the Windows edition is downloaded once and never revisited. Those are
asked, with the default first:

```
VERSION — which Windows to install
  1) 11   Windows 11 Pro — 7.9 GB   [default]
  2) 10   Windows 10 Pro — 5.8 GB
```

Enter takes the default. Without a terminal the defaults are kept and the
install says so.

## Sandbox

```bash
qh traccar --apply --prefix /tmp/test
```

Redirects every path, and does not touch systemd or podman — the steps that
would are printed instead of run.

## Lifecycle

```bash
qh <app> --apply                      # install
qh <app> --update --apply             # after a version bump in the repository
qh <app> --backup --apply --out ~/backups
qh <app> --remove --apply             # stop and remove, keep the data
qh <app> --remove --purge --apply     # delete everything
```

Checking afterwards:

```bash
systemctl --user is-active <app>
podman ps --filter "name=<app>"       # confirms healthy, not just started
journalctl --user -u <app> -f
```

A service with dependencies (immich, owntracks, paperless-ngx) comes up from
the main unit alone — `Requires=` pulls the chain. To stop it for a backup,
stop them all together, or the dependencies keep writing.

Removing the unit does not deregister the tailnet node; that is done in the
Tailscale admin.
