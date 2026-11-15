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
publishing the same host port, a `Secret=` with no recipe in `install.ini`, a
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
`install.ini` carries an `[upstream]` override where it does not — the image is
often not named like the repository (`dockurr/windows` against `dockur/windows`).

`--bump` takes what it found: it rewrites `Image=` and every place that mirrors
it — the `Pinned to` line of each service README in both languages, and the
per-unit page and Version column of a folder that documents its units apart.
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
[upstream]
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
[upstream]
netbootxyz = registry
```

It lists the registry's tags and takes the newest one shaped like ours: with
`1.30.4-alpine` installed the candidates are `\d+.\d+.\d+-alpine`, so `-perl`
and `latest` never win.

A pattern after the colon narrows that list where the shape alone cannot —
nginx keeps stable on even minors and mainline on odd, and publishes `-alpine`
for both:

```ini
[upstream]
nginx = registry:^1\.\d*[02468]\.\d+-alpine$
```

One value is special. `registry:latest` asks which numbered tag `latest`
currently resolves to, and compares against that. It is for a project that
numbers its prereleases too: Fedora publishes the stable release, the branched
one and rawhide side by side, all numbered, so the highest number is always the
wrong answer — `46` is byte-identical to `rawhide`, while `latest` is `44`.

```ini
[upstream]
toolbx-fedora = registry:latest
```

And `-` says there is nothing to compare at all — toolbx's Arch image publishes
only `latest`, so it is pinned by digest and no tag would answer for it.

A floating tag (`latest`, a bare major) has no version to compare, so it is
compared by digest instead: if the tag now points somewhere else than the image
on this host, it says so. That needs podman and the image already pulled.

## `qh-store`

A web app store over `qh`. It shows the catalog (`qh --catalog`), and every
action runs a `qh` command: the dry-run plan first, then `qh <app> --apply`
(also `--update` and `--remove`), plus start/stop/restart and logs for each
unit. It never runs `--purge`: data is still deleted only in the terminal.
Each installed unit shows its tag next to the project's latest release
(`qh-updates --host`, cached on disk for a day, and re-asked only for the
service an install, update or remove just touched; **Check now** forces it), so
you can see what is behind without this repository having to be bumped first.
When the repository still pins the installed version, **Update to X** takes
it: `qh-updates <app> --bump --apply` for that one service (its `Image=` and
Pinned lines, in the clone the store runs from), then `qh <app> --update
--apply`. The change stays in git for you to review and commit. A major is held
back exactly as `--bump` holds it.
There is one update button, and it shows up only when there is something to
update, and clicking it runs the update right away, with no plan and no
confirmation. While it runs, the panel shows every GitHub release between the
installed tag and upstream's (prereleases left out). Remove and restore still
show a plan and ask first, because they touch data. **Login** shows the credential named in `[login]` of `install.ini`, the
same one `qh` prints after an install. **Backups** runs `qh --backup` into
`~/.local/share/quadlet-homelab/backups`, lists the archives, and lets you
download them or upload one back. A restore runs `qh --restore`, and you have to
type the service name first, the same as in the terminal.
A service that keeps data also gets a **Back up first** box next to Update (remembered
in the browser, off by default): the update then runs after a `qh --backup`, chained, so a
backup that fails stops the update before it changes anything. The backup is the cold one
(it stops the service for a moment), so it costs a short outage.
What the terminal would ask during an install, the form asks first: `manual`
secrets and unset `[vars]`. They are stored with the same functions and the
same `[validate]` check that `qh` uses.

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

The unit starts `~/.local/bin/qh-store`, the link `bootstrap.sh` creates; a clone from
before the store needs `bootstrap.sh` again, or the `ln -s` by hand.

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
`install.ini [upstream]`, or an image on `ghcr.io`/`lscr.io` — and never guessed
from a Docker Hub name, which would give a link to a 404. Where the image's path
is not the repository's (netbootxyz's image is built from another repository),
`[store] repo = owner/repo` (or a full https URL) says which it is; **Issues** and
**Releases** follow from it, for GitHub, GitLab and Codeberg. **Documentation** is
read from the `[Official documentation](...)` link in each service README's
Credits, so it is written down once, by a person, and a link that only points back
to the repository is left out. Every one of these was checked to answer when it was
added; `check.py` does not fetch them, so a link can still go stale.

Screenshots come from `install.ini`, as images the project itself hosts:

```ini
[store]
screenshots =
    https://example.org/shot-1.png
    https://example.org/shot-2.png
```

`check.py` holds the list to https URLs, at most six, with no repeats. The
browser loads them from there, so the project's host sees the request, as it
already does for the icons. A few services carry them as examples; the rest
have none until someone adds an image worth showing.

A service that is discontinued — archived upstream, or with its pinned image gone
from the registry — is marked in the same section:

```ini
[store]
deprecated = Archived upstream on 2026-03-01; no release since 1.4.2.
deprecated_pt = Arquivado no upstream em 01/03/2026; sem release desde a 1.4.2.
```

The store shows a "discontinued" badge with the reason and offers no install
for it, and the server refuses one too. A service already installed stays
manageable, since removing it is the likeliest next step. `qh` warns before
installing it, and `qh --all` leaves it out; naming it still installs, because
the warning is not a ban. `deprecated_pt` is optional, and the English reason
stands in without it. `check.py` wants one plain line of at most 300 characters.
It is a decision a person writes down: nothing marks a service by itself.

**Play, pause and stop** (▶ ⏸ ■ on each installed app, in My apps and in its panel) act on the
whole service. Play starts what is not running and thaws what is paused; pause freezes the running
containers with `podman pause` (the units stay `active` for systemd, the app shows "paused" and its
memory stays allocated); stop stops every unit of the service together, thawing a frozen one first,
as a frozen container ignores SIGTERM. Each button is enabled only where it does something. They run
as jobs, so they appear in the history.

**Resources** (the header button, and a hint after an update) lists what Podman keeps
that nothing uses: images, networks and volumes, with the space the images take
("up to": layers are shared). Every update leaves the previous image behind. "Unused"
is stricter than `podman image prune -a`: an image is kept if a container uses it
**or an installed unit asks for it in `Image=`**, so a stopped service is not pulled
again at its next start. A network is kept if it is the default, used, or declared by a
`.network` file; a volume only when no container mounts it and no `.volume` file
declares it. Deleting asks twice, and volumes (data) want the word typed. The same from
a terminal: `python3 resources.py` to see, `prune images|networks|volumes --apply` to do.

**Works with** is a suggestion in the panel: `works_with = grafana, ntfy` under
`[store]` lists other service folders worth running beside this one, each a link
to its panel, ticked when installed. It is never a requirement (that is a network's
owner, which `qh` already enforces); `check.py` fails a name that is not a folder.

**Minimum Podman**: a unit with `Notify=healthy` needs Podman 5.0, and `[store]
min_podman = 5.4` raises that floor for a service that uses a newer Quadlet key.
`qh` warns before installing on an older host and the store shows it in the panel;
it does not refuse. `QH_PODMAN_VERSION` overrides what the host reports.

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
`~/.config/quadlet-homelab/store-roots` (one path per line); a port must be at
or above the unprivileged floor and free (not another unit's, not listening); a
capability must be on a short list (Podman's defaults plus `NET_RAW`,
`SYS_NICE`, `MKNOD`, `AUDIT_WRITE`); a device must exist under `/dev`. There is
no image or tag field, because the version belongs to the repository (rule 9),
and no privileged switch: with the store's token, either would make it a shell
on your host. For those, edit the unit by hand. The `.env` file stays under
**Configure**; the form edits the `Environment=` lines.

Memory and CPU limits are not offered, on purpose. Rootless, they need the user's
systemd to delegate those controllers, and where it does not, `--memory` stops
the container from starting (`memory.swap.max: no such file or directory`),
which was measured here, where only `pids` is delegated. Check yours with
`cat /sys/fs/cgroup/user.slice/user-$(id -u).slice/user@$(id -u).service/cgroup.controllers`.
Delegating them is a root change to `user@.service` (`Delegate=cpu cpuset io
memory pids`) that this repository does not make for you.

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
