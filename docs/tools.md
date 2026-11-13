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
(`qh-updates --host`, checked in the background and cached for six hours), so
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
What the terminal would ask during an install, the form asks first: `manual`
secrets and unset `[vars]`. They are stored with the same functions and the
same `[validate]` check that `qh` uses.

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

It listens on `127.0.0.1:8484`, so only this machine can reach it. Use
`ssh -L 8484:127.0.0.1:8484 <host>` to open it from another computer. To reach
it from the tailnet, have it listen on the host's tailnet address and publish it
through tsdproxy's `lists.yaml`, the same way as Cockpit:

```bash
systemctl --user edit qh-store      # [Service]  Environment=QH_STORE_LISTEN=<tailscale-ip>:8484
```

```yaml
qh-store:
  ports:
    443/https:
      targets:
        - http://<tailscale-ip>:8484
```

Anyone holding the token can install and remove services as you. Treat it like
an SSH key. To revoke it, delete the file and restart the service.

`qh-store --prefix /tmp/test` points it at a sandbox, like `qh --prefix`.
`qh-store --selftest` covers login, the request checks, and a full install
against a sandbox.
