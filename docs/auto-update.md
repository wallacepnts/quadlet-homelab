# Auto-update

Nothing in this repository updates on its own. Every image is pinned — to a
version tag, or to a digest where upstream publishes no version (monica-next,
the Arch and Fedora toolboxes, mdrop, two of immich's) — and `check.py` refuses
a unit with `AutoUpdate=` or a floating tag (`latest`, `main`, a bare major like
`16` or `17-alpine`). Rule 9 of the [conventions](./conventions.md).

## Where the version lives

An app's own image that follows a GitHub release has **no tag in the repository**:

```
# apps/memos/memos.container
Image=docker.io/neosmemo/memos
# apps/memos/app.json, under "units"
"memos": { "image": "{version}" }              # or v{version}, {version}-alpine, {version:2} ...
```

`qh` fills the template with the latest release when it installs, and writes the result where
only that host sees it — a Quadlet drop-in, `memos.container.d/10-image.conf`, with an
`Image=repo:tag` and a `# was:` line for the one it replaced. The host still runs a pinned,
known tag, and `systemctl cat memos` shows it; the repository never needs a bump for it.

```bash
qh <app> --update --apply            # re-copies the unit; keeps the version pinned on the host
qh <app> --update --latest --apply   # also moves each image to its latest release
qh <app> --update --latest --major --apply   # ...including a jump to a new major
qh-updates --host                    # what runs here, against what upstream released
```

A major jump is held back unless you say so: the release notes are read first (see below). A
host installed before versions left the repository keeps running what it ran: the first
`--update` writes the tag it finds on the installed unit into the drop-in. To go back, put
the tag you want in `Image=` of the drop-in and restart.

What keeps its tag in the unit — and is moved by a commit — is an image that is NOT the app's
own release: a database or cache pinned to what the app's compose validates (`upstream`
`compose:` or `-`), a distro image tracked on the registry (`registry:`), and anything pinned
by digest.

```bash
qh-updates                     # what is behind, against each project's own release page
qh-updates --bump --apply      # for those: rewrites Image=
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
