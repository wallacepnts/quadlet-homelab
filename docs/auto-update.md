# Auto-update

Three services update on their own: Actual Budget, homepage and VaultZap.
Everything else is pinned to a tag and bumped by hand.

## Turning it on for a service

```bash
systemctl --user enable --now podman-auto-update.timer   # once, for the host
```

Then in the `.container`:

```ini
Image=<registry>/<image>:<floating-tag>
AutoUpdate=registry
```

```bash
qh <app> --update --apply
```

## What it needs to be safe

- **A real `HealthCmd`.** Without one there is no rollback — Podman applies the
  update blind. With one, a container that fails its healthcheck is rolled back
  to the previous image.
- **A floating tag.** On an exact tag (`1.2.3`) the digest never changes and
  `AutoUpdate=` does nothing at all.
- **Data you do not mind seeing change without warning.** A password vault or a
  sync backend is worth reviewing before every bump.

Rolling back by hand:

```bash
podman auto-update --rollback
```

## Why most of it is off

A pinned tag means the version on the host is the version in the repository,
and an update happens when you decide it does. The three that are on have a
working healthcheck, a floating tag that upstream actually maintains, and data
whose loss would be an inconvenience rather than a disaster.
