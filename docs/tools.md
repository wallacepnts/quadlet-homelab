# Tools

Both speak Portuguese when the system does, like `qh`. `QH_LANG=en` or
`QH_LANG=pt` forces either.

## `qh-check`

Reads every unit in `apps/` and fails on what breaks silently. It also runs in
CI on every push, so an error here fails the build.

```bash
qh-check
```

What it catches: a unit whose basename does not match the app, two services
publishing the same host port, a `Secret=` with no recipe in `install.ini`, a
service missing from the README's version table, `$` in `HealthCmd` without the
double escape, a backslash in a `Label=` value, an unquoted value with spaces,
and `Notify=healthy` without a `HealthCmd`.

To waive a rule deliberately, the unit says so and the reason is required:

```ini
# check: ignore ports vm-windows and vm-windows-arm never run together
```

## `qh-updates`

Compares every `Image=` tag against the project's latest GitHub release and
prints only what is behind.

```bash
qh-updates
```

The GitHub repository is derived from the image name where that works, and
`install.ini` carries an `[upstream]` override where it does not — the image is
often not named like the repository (`dockurr/windows` against `dockur/windows`).

A GitHub release is not a published image: the release can land hours before the
registry has the tag. If it reports a version you cannot pull yet, wait.
