# Tools

Both speak Portuguese when the system does, like `qh`. `QH_LANG=en` or
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
service missing from the README's version table, a service README whose
pinned-version line no longer matches its units, a `PodmanArgs=` carrying what
Quadlet has a key for or a space it will not survive, a row in
[`hardening.md`](./hardening.md) that no longer matches its unit, `$` in
`HealthCmd` without the double escape, a backslash in a `Label=` value, an unquoted value with
spaces, and `Notify=healthy` without a `HealthCmd`.

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
it — the two version tables, the `Pinned to` line of each service README in both
languages, and the per-unit page and Version column of a folder that documents
its units apart. Without `--apply` it only shows the plan.

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
digest included.

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
