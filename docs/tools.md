# Tools

All three speak Portuguese when the system does, like `qh`. `QH_LANG=en` or
`QH_LANG=pt` forces either, and `NO_COLOR=1` turns the colouring off — which
is also off automatically whenever the output is not a terminal.

## `qh-check`

Reads every unit in `apps/` and fails on what breaks silently. It also runs in
CI on every push, so an error here fails the build.

```bash
qh-check
```

What it catches: a unit whose basename does not match the app, two services
publishing the same host port, a `Secret=` with no recipe in `app.json`, a
service missing from the README's services table, a service README whose
pinned-version line no longer matches its units, a `PodmanArgs=` carrying what
Quadlet has a key for or a space it will not survive, a row in
[`hardening.md`](./hardening.md) that no longer matches its unit, `$` in
`HealthCmd` without the double escape, a backslash in a `Label=` value, an unquoted value with
spaces, `Notify=healthy` without a `HealthCmd`, and a unit out of the standard
layout — the blocks described in [the reference](./reference.md#anatomy-of-a-container).
That one it also fixes:

```bash
qh-check --format      # rewrites every unit into the layout; order and blank lines only
```

It also runs every unit through **Podman's own Quadlet generator** (`quadlet -dryrun -user`,
all the units in one directory as on the host), which knows what the rest of the file does not: an
unsupported key, a `Network=` naming a file that is not there, a section it cannot read. Those
used to show up at install. It runs when the machine has a generator at Podman 5 or newer and is
skipped quietly otherwise; `qh-check --quadlet` makes its absence an error, which is what CI uses
(a separate job, in the official `podman/stable` image, since the runner's Podman is older than
the keys need). The generator does not interpret every value (`Notify=maybe` passes), so this is a
floor under the other checks, not a substitute for them. The store's Customize screen already
validates a drop-in with the same generator before it writes it.

To waive a rule deliberately, the unit says so and the reason is required:

```ini
# check: ignore ports vm-windows and vm-windows-arm never run together
```

## `qh-updates`

Compares every `Image=` tag against the project's latest GitHub release and
prints only what is outdated. `--all` adds what is up to date and what could
not be compared.

```bash
qh-updates
```

The GitHub repository is derived from the image name where that works, and
`app.json` carries an `upstream` override where it does not — the image is
often not named like the repository (`dockurr/windows` against `dockur/windows`).

`--bump` takes what it found: it rewrites `Image=` and every place that mirrors
it — the per-unit page and Version column of a folder that documents its units apart.
The root README's services table carries no version. Without `--apply` it only
shows the plan.

`--host` compares what is installed on this machine instead of what the
repository pins, so you can tell what is behind upstream even before the
repository is bumped. `--json` prints every row as JSON, which is what the
store reads.

```bash
qh-updates --host            # installed here, against each project's release
qh-updates memos --bump      # one service only (folder or unit names)
```

```bash
qh-updates --bump            # what it would take
qh-updates --bump --apply    # take it
```

It refuses a major, listing them for you to take one at a time with `--major`.
Rule 9 of the [conventions](./conventions.md) is that a version is chosen, not
received: wud 9 exits at startup without an administrator that did not exist
before, wger 2.7 converts old data with a setting that has to be right first and
cannot be changed after. The refusal is a filter and not a guarantee — a
calendar version has no major, so 2026.8 to 2026.9 reads as a minor and carried
eight breaking changes. Reading the release notes is still the job.

A sidecar tracked by `compose:` is bumped to what that compose declares,
digest included. When the compose runs two images of the same name — Postiz's has
`postgres:17-alpine` for the app and `postgres:16` for Temporal — the one whose tag
is shaped like the pinned one is the one compared. Taking the first made the
Temporal database read as a major behind.

Before asking whether a newer image exists, it asks whether the pinned one still
does, and reports what does not as gone. Two got there by different roads: the
Chrome image karakeep used was withdrawn from its registry, and the arch-toolbox
digest was collected out from under a rolling image. Both kept running from the
local copy while every fresh install failed.

A GitHub release is not a published image: the release can land hours before the
registry has the tag. That case is reported separately — the tag is checked in
the registry before an update is called available.

A sidecar follows the version the app's own compose validates, not its own
upstream — the Postgres in immich's compose moves when immich moves it:

```ini
`upstream`
immich-postgres = compose:immich-app/immich:docker/docker-compose.yml
authentik-postgres = compose:https://goauthentik.io/docker-compose.yml
```

The compose is read at the version the main unit is pinned at, which is the one
you would be going to. A direct URL works too, for a project that publishes its
compose on its site instead of in the repository.

When both sides pin by digest, the digests are what get compared — a tag like
immich's `valkey:9` reads the same across two releases while the image under it
changes, and comparing tags there would only ever say "up to date". When the
compose does not pin at all, that is reported as such instead of being called
up to date, which would be a comparison that never happened.

An image that does not version by GitHub release — a distro tag, a project
that only publishes git tags, an image versioned apart from its repository —
compares against the registry instead:

```ini
`upstream`
netbootxyz = registry
```

It lists the registry's tags and takes the newest one shaped like ours: with
`1.30.4-alpine` installed the candidates are `\d+.\d+.\d+-alpine`, so `-perl`
and `latest` never win.

A pattern after the colon narrows that list where the shape alone cannot —
nginx keeps stable on even minors and mainline on odd, and publishes `-alpine`
for both:

```ini
`upstream`
nginx = registry:^1\.\d*[02468]\.\d+-alpine$
```

One value is special. `registry:latest` asks which numbered tag `latest`
currently resolves to, and compares against that. It is for a project that
numbers its prereleases too: Fedora publishes the stable release, the branched
one and rawhide side by side, all numbered, so the highest number is always the
wrong answer — `46` is byte-identical to `rawhide`, while `latest` is `44`.

```ini
`upstream`
toolbx-fedora = registry:latest
```

And `-` says there is nothing to compare at all — toolbx's Arch image publishes
only `latest`, so it is pinned by digest and no tag would answer for it.

A floating tag (`latest`, a bare major) has no version to compare, so it is
compared by digest instead: if the tag now points somewhere else than the image
on this host, it says so. That needs podman and the image already pulled.

## `qh-store`

The web panel, and the way this repository is meant to be used: `bootstrap.sh` starts it,
and install, update, back up, restore, customize and remove all happen in it. It is a layer
over `qh`: it shows the catalog (`qh --catalog`), and every action runs a `qh` command (the
dry-run plan first, then `qh <app> --apply`, also `--update` and `--remove`), plus
start/stop/restart and logs for each unit. Nothing in it is a second implementation, so what
the terminal does and what the panel does cannot disagree.

Deleting data is in the panel too, behind the same guard as a restore: the **Remove** form has
"Also delete the data, the secrets and the .env", which asks for the service's name typed, and
`qh` asks it again on its own. **Settings** (the header) holds the access rule (local network,
tailnet or both, `qh --set-access`) and shows which installed services do not follow it, with a
button that applies it to them (an update each). **Update all**, in My apps, takes every service
that has something to take, one after the other: a failure does not stop the rest, and the job
says at the end that one failed.
Each installed unit shows its tag next to the project's latest release
(`qh-updates --host`, cached on disk for a day, and re-asked only for the
service an install, update or remove just touched; **Check now** forces it), so
you can see what is behind without this repository having to be bumped first.
**Update to X** takes the new release. For an app whose version is not in the
repository (see [auto-update](./auto-update.md)) that is `qh <app> --update --latest
--apply`: the new tag is pinned in the host's drop-in and nothing is left to commit. For an
image that still has its tag in the unit (a sidecar, a digest) it is `qh-updates <app>
--bump --apply` for that one service (its `Image=`, in the clone the store
runs from), then `qh <app> --update --apply`, and the change stays in git for you to review
and commit. A major is held back both ways.
There is one update button, and it shows up only when there is something to
update, and clicking it runs the update right away, with no plan and no
confirmation. While it runs, the panel shows every GitHub release between the
installed tag and upstream's (prereleases left out). Remove and restore still
show a plan and ask first, because they touch data. **Login** shows the credential named in `login` of `app.json`, the
same one `qh` prints after an install. **Backups** runs `qh --backup` into
`~/.local/share/quadlet-homelab/backups`, lists the archives, and lets you
download them or upload one back. A restore runs `qh --restore`, and you have to
type the service name first, the same as in the terminal.
A service that keeps data also gets a **Back up first** box next to Update (remembered
in the browser, off by default): the update then runs after a `qh --backup`, chained, so a
backup that fails stops the update before it changes anything. The backup is the cold one
(it stops the service for a moment), so it costs a short outage.
What the terminal would ask during an install, the form asks first: `manual`
secrets and unset `vars`. They are stored with the same functions and the
same `validate` check that `qh` uses.

**Configure** edits the service's `.env`, the file `qh` installed from
`.env.example`. An optional setting ships commented out: ticking it turns it on,
and unticking an active one comments it out again. Only keys the file already
names are accepted, a value is a single line, and the previous file is kept as
`<name>.env.bak` (mode 0600). Saving restarts the units that read the file with
`try-restart`, so a stopped service stays stopped. Keys that look like
credentials are password fields.

A setting can say what it holds with a `# type:` line among the comments right above
it in the `.env.example`: `number`, `bool`, `email`, `url`, `ip` or `password`
(plain text when there is none). The form then shows the right box — a number field, a
checkbox that writes the file's own style (`Y`/`N`, `yes`/`no`, `1`/`0`, `true`/`false`),
a masked field — and the server refuses a value that is not one. An empty value is never
refused: it means unset. `check.py` fails an unknown type, a hint with no setting under
it, and an example value that is not of its type. Only declare `bool` where the app takes
nothing else (`GPU=Y` also takes `intel` or `nvidia`, so it stays text).
```
# How many cores the VM gets.
# type: number
CPU_CORES=2
```

The panel also shows CPU, memory and disk, and the architectures the images are
built for, with a warning when the host's is not among them. CPU and memory are
read from `/proc` and cgroupfs, because `podman stats` answers 0B of memory for
rootless containers here (the memory controller is not delegated to the user's
cgroup); memory is resident size, which counts a page shared between a
container's processes once per process, so it is a size to compare, not an
accounting. Disk is `podman unshare du` over the volumes `qh --backup` would
pack, never a shared media root, and is cached for ten minutes. Architectures
come from the image's registry manifest and are cached for a week.

The page has two screens, as CasaOS does. **My apps** is what is installed, as
tiles with the state, the version badge and CPU and memory: a tile opens the app
in a new tab when it has a single address, and the gear beside it manages the
service. An app with several web UIs (the media stack) or none has no single
place to go, so its tile opens the panel. **Store** is the whole catalog, with
categories and search, and marks what is already installed. The screen is kept
in the URL (`#apps` or `#store`), so a reload or a bookmark lands on the same
one; with nothing installed yet it opens on the Store.

It runs on the host as a systemd `--user` service, not as a Quadlet. Its job is
driving systemd and podman as you, so a container would need your home, your
podman socket and your systemd bus. That is the same access, just less obvious.
For the same reason the unit has no `NoNewPrivileges=`: rootless podman needs
the setuid `newuidmap`.

`bootstrap.sh` installs and starts it: it copies the unit to `~/.config/systemd/user/`, asks once
where the panel will be opened from (writing `QH_STORE_LISTEN` into a drop-in for the local
network or the tailnet), starts it, and prints the address and the login token. A re-run keeps
the answer, restarts the panel on the new code, and prints them again. `NO_PANEL=1` skips all of
it. The unit starts `~/.local/bin/qh-store`, the link `bootstrap.sh` creates. By hand:

```bash
systemctl --user enable --now ~/quadlet-homelab/store/qh-store.service
cat ~/.config/quadlet-homelab/store-token       # the login
```

Each installed service has an **Access** picker: follow the rule, local
network, tailnet, or both. Picking one saves an exception
(`qh --set-access MODE APP`) and applies it with `--update`. Installing a
service whose network belongs to one that is not installed (tsdproxy, for 80 of
the 83) installs that one first, asking its questions in the same form.

It listens on `127.0.0.1:8484`, so only this machine can reach it. Use
`ssh -L 8484:127.0.0.1:8484 <host>` to open it from another computer. To reach
it from the tailnet as well, give it the host's tailnet address too
(comma-separated addresses, each its own listener; `0.0.0.0` would add the LAN)
and publish it through tsdproxy's `lists.yaml`, the same way as Cockpit. The
entry ships commented out in `apps/tsdproxy/config/lists.yaml`:

```bash
systemctl --user edit qh-store      # [Service]  Environment=QH_STORE_LISTEN=127.0.0.1:8484,<tailscale-ip>:8484
```

```yaml
qh-store:
  ports:
    443/https:
      targets:
        - http://<tailscale-ip>:8484
```

**History** (the header button, and one per service) lists every action the
store ran — install, update, remove, backup, restore, access, settings, and
start/stop/restart — with when, how it ended, how long it took and its output.
It is one line of JSON per action in
`~/.local/share/quadlet-homelab/store-history.jsonl` (mode 0600): the output
keeps only its last 20 000 characters, the login credentials `qh` prints after
an install are masked as `***`, and the file is cut to its newest half when it
passes 2 MB. "From" is the address the store saw; behind tsdproxy that is the
proxy's, since there is one token and so one user.

Each panel also links to the project, its documentation and issues, its
releases, the image's page on its registry, and this repository's recipe. The
project's repository is shown only where something says which it is —
`app.json `upstream``, or an image on `ghcr.io`/`lscr.io` — and never guessed
from a Docker Hub name, which would give a link to a 404. Where the image's path
is not the repository's (netbootxyz's image is built from another repository),
`source` (an https URL) (or a full https URL) says which it is; **Issues** and
**Releases** follow from it, for GitHub, GitLab and Codeberg. **Documentation** is
read from the `[Official documentation](...)` link in each service README's
Credits, so it is written down once, by a person, and a link that only points back
to the repository is left out. Every one of these was checked to answer when it was
added; `check.py` does not fetch them, so a link can still go stale.

The logo and the screenshots are files in the app's own folder, `icon.svg` and `screenshots/1.png`,
`2.png`…, and the store serves them itself (`/assets/<app>/...`, behind the login, so the browser never
asks another host and nothing outside sees which apps you look at). `check.py` wants a logo (`.svg`,
`.png`, `.webp` or `.jpg`, up to 512 KB) and holds the screenshots to at most six images of up to 1 MB. A few
services carry screenshots; the rest have none until someone adds an image worth showing.

A service that is discontinued — archived upstream, or with its pinned image gone
from the registry — is marked in the same file:

```json
"deprecated": "Archived upstream on 2026-03-01; no release since 1.4.2."
```

The store shows a "discontinued" badge with the reason and offers no install
for it, and the server refuses one too. A service already installed stays
manageable, since removing it is the likeliest next step. `qh` warns before
installing it, and `qh --all` leaves it out; naming it still installs, because
the warning is not a ban. `deprecated_pt` is optional, and the English reason
stands in without it. `check.py` wants one plain line of at most 300 characters.
It is a decision a person writes down: nothing marks a service by itself.

**Console**: a Console button on a running unit opens a shell inside its container (`podman exec
-it`, bash when the image has it, else sh) over a WebSocket, written with the standard library only
(`wsterm.py`: the handshake, text frames, ping/pong, close, and a pty). Whoever holds the token
already controls every service, so this adds no power, but it is a shell, so: the browser's `Origin`
must be this server's own (a WebSocket cannot carry the `X-QH-Store` header, and the cookie is
`SameSite=Strict`), at most four consoles are open, one idle for 15 minutes is closed, and each
session is a line in the history. The page keeps the screen itself and understands what a shell with
`TERM=dumb` sends (line breaks, backspace, tab; colours are dropped), so full-screen programs (vim,
top) do not work. Closing the tab ends the session politely (Ctrl-C, `exit`) and, if the shell
ignores that, kills everything started in it by an environment marker: closing the local
`podman exec` alone leaves the container's shell running.

**Live logs**: the Logs button on a unit opens its last 200 lines and then follows them as they
arrive (`journalctl -f`, sent as Server-Sent Events), with a box that filters the lines as you type
(case-insensitive, over the last 5000 received) and a "follow" tick that keeps the view at the end.
Closing the panel or opening another log ends the stream, and the server kills the `journalctl`
when the browser goes away (a heartbeat every 15 s notices a closed tab on a quiet journal). At most
eight streams are open at once.

**Filters and summary** in My apps: under the tabs, "All", "With updates" and "With problems" are
buttons that carry their counts, and one line says how many apps are running, stopped or paused. A
service has an update when a newer release exists upstream or the repository changed since it was
installed; a problem is whatever the badge shows in red (a unit that failed, a restart loop, an
unhealthy container, an image that is gone). Clicking the active filter again clears it, and so does
switching tab; the search box works on top of it.

**Failure state** on the card: a unit that systemd restarted, that failed, or that is waiting to
be restarted shows a red "restart loop (7×)" or "failed (exit 125)" badge, or a yellow "restarted
2×" once it recovered, with the details on hover and in the panel: restarts, exit code, result and
the time of the last failure. It comes from one `systemctl show` for all the units (`NRestarts`,
`ExecMainStatus`, `Result`, `ExecMainExitTimestamp`) and is in `qh --catalog` as `failure`. A
service stopped on purpose never shows it.

**Play, pause and stop** (▶ ⏸ ■ on each installed app, in My apps and in its panel) act on the
whole service. Play starts what is not running and thaws what is paused; pause freezes the running
containers with `podman pause` (the units stay `active` for systemd, the app shows "paused" and its
memory stays allocated), and a reboot brings the app back running, since the processes were
never saved; stop stops every unit of the service together (thawing a frozen one first, as it
ignores SIGTERM) and **masks** them (`systemctl --user mask --now`), which is what survives a
reboot: the units are wanted by `default.target`, so a plain stop is undone at the next boot. Play
unmasks, then starts. A masked service shows as "stopped", not as a problem; `qh --update` pulls
the new image and skips the restart (and says so), and `qh --remove` lifts the mask so the name can
be installed again. Masking is not enable/disable (rule 4): the generated unit keeps its own
`[Install]`. Each button is enabled only where it does something. They run
as jobs, so they appear in the history.

**Resources** also shows **Space per app**: what each installed app's data takes on disk, largest first, with a
total (`podman unshare du`, because the files a container wrote belong to a subuid a plain `du` cannot read). Only the
folders under `volumes/` count: a folder of yours, such as the media root, is not the app's. It is computed on opening
and kept five minutes; **Recalculate** forces it.

**Resources** (the header button, and a hint after an update) lists what Podman keeps
that nothing uses: images, networks and volumes, with the space the images take
("up to": layers are shared). Every update leaves the previous image behind. "Unused"
is stricter than `podman image prune -a`: an image is kept if a container uses it
**or an installed unit asks for it in `Image=`**, so a stopped service is not pulled
again at its next start. A network is kept if it is the default, used, or declared by a
`.network` file; a volume only when no container mounts it and no `.volume` file
declares it. Deleting asks twice, and volumes (data) want the word typed. The same from
a terminal: `python3 resources.py` to see, `prune images|networks|volumes --apply` to do.

**Minimum Podman**: a unit with `Notify=healthy` needs Podman 5.0, and `"min_podman": "5.4"`
raises that floor for a service that uses a newer Quadlet key.
`qh` warns before installing on an older host and the store shows it in the panel;
it does not refuse. `QH_PODMAN_VERSION` overrides what the host reports.

**Customize before installing**: an app that is not installed has a Customize button beside Install.
The form is the same, but it works on the unit as `qh` would write it (the repository's, rendered
for the access rule in force); **Keep for the install** checks the choice with the same rules and
the same Quadlet generator, remembers it, and the install carries it: it is validated again when
the install starts (a bad one refuses the install before anything runs) and written into the drop-in
right after the unit exists, with the same rollback if the service does not come up. Only an install
takes one, and only for units of that app; nothing is written to the host until then.

**Customize** changes an installed service without touching the repository's
unit: ports, volumes, extra variables, devices, extra capabilities and the
restart policy, laid out like the form CasaOS has for an app. The change is a
Quadlet drop-in, `<unit>.container.d/50-store.conf`, beside the unit. `qh
--update` leaves it alone and says so (and says it too when the unit changed
under a customization that resets a list, since that hides what is new),
`qh --status` marks the service, and `qh --remove` takes it away with the unit.
**Revert**, or deleting the file, goes back to the unit as published. **Preview**
shows the exact file and the `podman run` line Quadlet makes of it; **Save and
apply** writes it, restarts the service, and, if the service does not come up,
puts the previous state back and prints the last lines of its journal.

Only what is new is checked, and what the unit already carries is always
accepted as it is. A new volume must sit inside `~/.config/containers/volumes`,
a folder the units already ask you for (`${MEDIA_DATA_DIR}`) or one you list in
`~/.config/quadlet-homelab/store-roots` (one path per line), and a **folder picker** (the 📁 beside
the host path) lists exactly those folders and nothing else: by real path, so a symlink does not
lead out of them, with no hidden folders or files, and a new sub-folder can be typed (it is created
when the customization is applied); a port must be at
or above the unprivileged floor and free (not another unit's, not listening); a
capability must be on a short list (Podman's defaults plus `NET_RAW`,
`SYS_NICE`, `MKNOD`, `AUDIT_WRITE`); a device must exist under `/dev`. There is
no image or tag field, because the version belongs to the repository (rule 9),
and no privileged switch: with the store's token, either would make it a shell
on your host. For those, edit the unit by hand. The `.env` file stays under
**Configure**; the form edits the `Environment=` lines.

**Limits** (memory and CPU) are offered only where they can work. Rootless, they need the user's
systemd to delegate those controllers, and where it does not, `--memory` stops the container from
starting (`memory.swap.max: no such file or directory`), which was measured on a host where only
`pids` is delegated. So the form reads the user's `cgroup.controllers` and, when it lists `memory`
and `cpu`, shows two fields: **Memory** (`Memory=512m`, `2g`) and **CPUs** (`PodmanArgs=--cpus=1.5`,
which Quadlet has no key for), written into the same drop-in and checked against the host's memory
and core count. Where the controllers are missing the fields are shown disabled, with the reason, and
the server refuses to save a limit anyway. A limit the unit itself carries is not removed from here.
It takes effect the next time the container starts. Check yours with
`cat /sys/fs/cgroup/user.slice/user-$(id -u).slice/user@$(id -u).service/cgroup.controllers`.
Delegating them is a root change that this repository does not make for you: a drop-in such as
`/etc/systemd/system/user@.service.d/delegate.conf` with `[Service]` and `Delegate=cpu cpuset io
memory pids`, then log out and in. This path was written and tested against a stand-in
`cgroup.controllers`, not on a host that delegates them.

`store/test/ui.js` runs the page in Node against a stand-in DOM, and
`store/test/browser.js` drives a real Chromium through it (`node
store/test/browser.js <url> <token-file> <out-dir> [real|sandbox]`; `real` only
reads and previews, `sandbox` also applies, so point it only at a store started
with `--prefix`). Neither is in the CI, which is Python only.

Anyone holding the token can install and remove services as you. Treat it like
an SSH key. To revoke it, delete the file and restart the service.

`qh-store --prefix /tmp/test` points it at a sandbox, like `qh --prefix`.
`qh-store --selftest` covers login, the request checks, and a full install
against a sandbox.

## `screenshots.py`

Looks for screenshots in the README of each app's `source` and, only with `--apply`, saves them as
`apps/<app>/screenshots/1.png…`. It takes only what the project hosts itself (its own repository, or GitHub's
`user-attachments`), checks each image (200, `image/png|jpeg|webp|gif`, up to 1 MB, not an icon), and by default
leaves alone an app that already has screenshots (`--app <name>` replaces them). Read the dry run before
`--apply`: it prints every address.

## Alerts (`alerts.py`, in `qh-store`)

Off by default. **Settings → Alerts** takes an ntfy server, a topic and an optional token, and the store checks
every five minutes: a unit that failed, a container that is unhealthy, a unit restarting in a loop (three restarts,
the last within the hour), a new upstream release, and a disk past the chosen percentage. A backup the store ran
that failed is told at once. The same alert is not sent again within the cooldown (6 hours by default), and a
release is told once per version. The settings are in `~/.config/quadlet-homelab/alerts.json` (mode 600, it may
hold the token, which the page never receives back); what was sent and when is in
`~/.cache/quadlet-homelab/alerts-state.json`. Backups scheduled by Zerobyte are not watched.

## Server performance

The home (My apps) opens with the server at a glance: processor, memory, the disk the apps' data lives on and the
network (rate; real interfaces only, not the container bridges or the tailnet's copy of the same traffic), each with a
small history, refreshed every five seconds from `/api/host`. There is no widgets sidebar any more.

## Files

**Files** (the navigation, and a button in each app that keeps data) is a file manager for the folders of your apps, the
way CasaOS and ZimaOS have one: apps first, then their volumes and folders (the directories under
`~/.config/containers/volumes/`), plus the folders you chose for what the apps share (`@MEDIA_DATA_DIR`, the
recordings), when they exist.

- **Look:** a window with the places on the left (each app with its logo, then your own folders), breadcrumbs, a list
  with size and date or a grid of icons (the choice is kept in the browser), an icon by kind of file, a text file previewed (first 256 KB), an image shown, any file
  downloaded.
- **Change:** **Upload** (the button, or drop files on the window; a name already there is kept and the new one becomes
  `name (1)`, and a cut upload leaves nothing), **New folder**, **Rename**, **Copy / Cut / Paste** (across folders and
  apps), **Delete** (asked twice) and an editor for a whole text file. Select with the checkboxes; the actions follow
  the selection.
- **The panel warns, it does not stop you:** changing the files of a running app can corrupt its data (a database
  copied while it writes). Stop the app first.
- **Ownership:** what is created takes the owner of the folder it lands in, so the app that owns that folder can read
  it back. The work runs in `podman unshare`, where the files a container wrote, which belong to a subuid, can be
  read and written at all (`hostctl.py fs-*`).

What holds it inside the app's folders:

- **Only the volumes**: a path is `app/volume/folder/...` and the volume must be one the app's units mount (or an
  `@NAME` folder from the variables the installed apps use). The rest of the home is not reachable.
- **No links**: a container can leave a symlink to `/etc/passwd` in its data, and inside `podman unshare` that would
  reach the host's own files. A link anywhere on the path is refused and shown as a link; it is never followed or
  written through. A link can be renamed, copied as a link and deleted (the link goes, its target stays).
- **Regular files only**: a fifo or a device is refused, so a read cannot hang.
- **The units and the `.env` files, read only:** `Units (systemd)` and `Variáveis (.env)` (`@systemd`, `@env`) show
  `~/.config/containers/systemd` and `env` to look at and download, never to change: a unit is code that runs as you, and
  editing one freely would skip what **Customize** checks (to change a unit use Customize; a `.env`, Configure).
- **The secrets are never reachable:** `~/.config/containers/secrets` is one clear file per secret. No root can be or
  hold it, and a link into it is refused like any other.
- **The volume itself** cannot be renamed, moved or deleted from here (that is the app's removal, in the panel).

## Restart or shut down the server

**Settings → Server** has **Restart** and **Shut down**, each asking once more before it acts. The panel runs them as
your user (`systemctl reboot` / `poweroff`; polkit allows it for a logged-in user) and refuses while a job (an install,
an update) is running. After a restart the panel waits for the server to answer again and reloads by itself; after a
shutdown, only the machine's own button turns it back on.

The same section **schedules** one of them: in 15 minutes, 1 or 4 hours, or at a time of day (the next one, by the
server's clock), between a minute and a week ahead. It is a transient systemd user timer (`qh-power.timer`), one at a
time: a new schedule replaces the old, and **Cancel schedule** stops it. The state is `~/.config/quadlet-homelab/power.json`.
Unlike the immediate action, a scheduled one does not wait for a running job.

## Quick Launch, appearance and service widgets

- **Quick Launch:** type any letter on the page (or `/`) and a search opens over it: the installed apps first, then the
  store's. Enter takes the highlighted one (opens the app, or its page in the store), and the last line searches the
  web. It does not open while you are typing in a field or with a window open.
- **Appearance** (Settings): theme (system, light, dark), accent colour (eight, all AA), card style (shadow or thin
  border), density, and a background image (PNG, JPEG or WebP up to 8 MB, with blur and a veil). It is kept on the
  server (`~/.config/quadlet-homelab/store-ui.json` and `store-bg.*`), so every browser sees the same.
- **Site monitor:** a running container whose app does not answer gets a red dot; one that answers says how fast in
  the dot's tooltip. The server asks each app's address once a minute (`/api/monitor`).
- **Service widgets** (`widgets` in `app.json`, see [manifest](./manifest.md)): numbers from inside an app on its tile
  and in its panel. The key is typed in the panel (Set up the widget) and kept in
  `~/.config/quadlet-homelab/widgets.json` (mode 600); the server calls the app, so the key never reaches the
  browser. Numbers that call for attention are coloured (inbox waiting, downloads wanted, monitors down).

## The Clean theme

The panel is a navigation on the left (My apps, Store, History, Resources, Settings), and the page in the middle. The navigation starts open and folds to
icons (⇤), and the choice is kept. The font is Plus Jakarta Sans (OFL, served by the panel itself).

- **My apps** is a home: a greeting, four cards with the server (processor, memory, disk, network, each with its last
  readings), what you used recently, and then all your apps. An app is its icon and its name: **right-click it** (or
  press and hold on a phone) for its state, the update, Open, Manage, Customize,
  restart, pause, stop, logs and remove. A failure still shows on the tile, in words.
- **Icons** sit on a squircle plate, Samsung One UI style, soft. The panel reads each logo once (its hue, whether it is a
  full square, mostly white, vivid or grey, and how much of its box it fills) and picks the plate and the size, so every
  logo weighs the same. `icon` in the app's `app.json` overrides it: `bg` (the plate's colour), `fit` and `tone`
  (`light`, `color`, `dark`, `full`), see [manifest](./manifest.md).
- **Appearance** (Settings): theme (system, light, dark), accent, card style, density, **icon size** (small, medium,
  large), **background** (flat, or with depth and colour), and a background image.
