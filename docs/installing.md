# Installing and operating

Everything through `qh`. Every mode is **dry-run by default**; `--apply`
executes.

```bash
qh                                    # the services
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
filebrowser: already installed — 1/1 unit(s) in ~/.config/containers/systemd
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

## What was done

With `--apply`, the run ends with what actually ran:

```
feito: 3 instalações
  7 diretórios, 6 units e arquivos copiados, 3 volumes com dono ajustado,
  3 imagens baixadas, 3 serviços reiniciados, 1 secret criado
```

With one service the step list above already is the summary; with `--all` it is
three hundred lines and the question left is what changed.

## Status

```bash
qh --status
```

```
service                    unit       container  repo
adguardhome                failed     —          changed
filebrowser                active     healthy    changed
memos                      active     healthy    —
```

`unit` is what systemd says, `container` is what podman says — a unit can be
`active` with the app inside it dead, so the two are not the same question.
`repo` says the file here differs from the one installed, which is what
`--update` would fix. Versions are not here: that needs the network, and it is
what `qh-updates` is for. It exits non-zero when anything needs attention.

## The access rule

Chosen once, followed by every install and update:

```bash
qh --set-access tailnet     # local | tailnet | both | headscale
qh                          # shows the rule in force
```

| rule | reachable at | tsdproxy | LAN port |
| --- | --- | --- | --- |
| `local` | `http://<host-ip>:<port>` | labels commented out | open |
| `tailnet` | `https://<app>.<tailnet>.ts.net` | on | **closed** |
| `both` | either | on | open |
| `headscale` | `https://<app>.qh` | labels commented out | **closed** |

`headscale` is for a tailnet of your own: no tsdproxy, no port on the LAN, and
[Caddy](../apps/caddy) in front answering a name you chose, signed by its own
authority. Each install prints the Caddyfile block to paste. The suffix is
`qh` unless you say otherwise:

```bash
qh --set-domain casa
```

The whole setup is in [A tailnet of your own](./self-hosted-tailnet.md).

`qh` reports how many installed services do not follow it, and the command
that brings them in line — a rule that only applied to the next install would
be half a rule.

The bootstrap asks for it on the first run. Until it is set, `tailnet` is the
default. Naming `--access` on a single command wins over the rule for that
command only, and changes nothing saved.

## Access

```bash
qh traccar --apply --access local     # no tsdproxy, dashboard link to the LAN
qh traccar --apply --access tailnet   # default
qh traccar --apply --access both
qh traccar --apply --href-local       # on the tailnet, dashboard link to the LAN
```

`--local` is shorthand for `--access local`. The `tsdproxy.*` labels are
commented out rather than deleted, so changing your mind later is an `--update`
with another mode — not a `--reinstall`, which would overwrite env, config and
secrets to change a label.

`--access tailnet` also **closes the LAN port**. The service joins the
`tsdproxy-net` network and tsdproxy reaches it at the container's own address,
so nothing of it is open on the host. Only the port tsdproxy proxies is closed:
a unit that also publishes DNS, MQTT or a torrent port keeps those in every
mode, because devices reach them directly.

An update keeps the mode the host already has, so a service installed with
`--local` does not silently rejoin the tailnet on the next version bump. Naming
`--access` on an update changes it:

```bash
qh memos --update --apply --access tailnet    # and close its LAN port
```

## Credentials

When a service has a login, the install ends with it:

```
  user:     admin
  password: 7x63tlKq...
```

Not on `--update`: it changes no credential, and `qh --all --update` would
spill every password into the terminal at once. Install and `--reinstall` do
print it, and so does a plain `qh <app>` on something already installed — which
is the deliberate way to look one up. It lands in your scrollback.

Which secret that is comes from `install.ini`. Only the one that is a typed
password is printed — the JWT keys and API tokens next to it are secrets too:

```ini
[login]
user = admin
password = filebrowser-admin-password
```

A stack whose units have different logins names one per unit:

```ini
[login.vm-windows]
user = Docker
password = vm-windows-password

[login.vm-chromeos]
user = admin
password = vm-chromeos-password
```

When one secret holds both halves, in the `user:password` form the app reads,
name it once and the install splits it at the first `:`:

```ini
[login]
credentials = vaultzap-basic-auth
```

`check.py` fails the build if any of those names is not a `Secret=` some unit
declares.

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
