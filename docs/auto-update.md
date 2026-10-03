# Auto-update

Nothing in this repository updates on its own. Every image is pinned — to a
version tag, or to a digest where upstream publishes no version (monica-next,
the Arch and Fedora toolboxes, mdrop, two of immich's) — and `check.py` refuses
a unit with `AutoUpdate=` or a floating tag (`latest`, `main`, a bare major like
`16` or `17-alpine`). Rule 9 of the [conventions](./conventions.md).

An update is a commit, then a command on the host:

```bash
qh-updates                     # what is behind, against each project's own release page
qh-updates --bump --apply      # rewrites Image= and the README tables
qh <app> --update --apply      # puts it on the host
```

## Why nothing updates on its own

- **The version on the host is the version in the repository.** With a pinned
  tag, the unit and the README say what is running. With `latest` the answer is
  whatever was pushed last, on a schedule nobody chose.
- **Upstream decides what a floating tag means.** gluetun's `latest` is built
  from its main branch, not from its releases: moving it to `v3.41.3` changed the
  build, not just the name. Postgres's `16` moves with every minor release.
- **Some updates have to be read first.** A schema migration with no way back, a
  renamed variable, a default that deletes data — Gitea 28 removes Actions runs
  older than 400 days unless told otherwise. The release notes are read before
  the bump, not after the container restarted into it.
- **Rollback was never a safety net.** `AutoUpdate=registry` only rolls back a
  container whose healthcheck fails; an app that starts and is quietly wrong
  stays on the new version.

## On one host only

The repository does not carry it. A host that wants it for one service edits
its own copy of the unit — a floating tag plus `AutoUpdate=registry`, and
`systemctl --user enable --now podman-auto-update.timer` once — and
`qh <app> --update` lists that edit before it would overwrite it.
