# The repository's tools

Two dependency-free scripts, which run in CI on every push
([`check.yml`](../.github/workflows/check.yml)).

## Checking the repository (`check.py`)

[![check](https://github.com/wallacepnts/quadlet-homelab/actions/workflows/check.yml/badge.svg)](https://github.com/wallacepnts/quadlet-homelab/actions/workflows/check.yml)

It runs by itself on every push and pull request
([`.github/workflows/check.yml`](../.github/workflows/check.yml)) — on a bare
runner, with no podman and no systemd, because `check.py` is file reading and
`install.py --prefix` executes nothing on the host.

The job does three things beyond the check itself:

- **builds the install plan for all 48 services**, which catches what static
  analysis cannot see: a `Secret=` with no recipe in `install.ini`, and an
  `.example` with no destination;
- **runs `test_install.py`**, which exercises the whole lifecycle in a sandbox
  — install, edit a user file, back up, restore, refuse an invalid restore,
  remove and purge, with 23 asserts about what actually happened on disk;
- **runs both scripts' `--selftest`** before anything else, because a broken
  parser makes the rest worthless.

`test_install.py` was written after a code review found four defects in
`--restore` that manual verification had let through. Reintroducing each of
them on purpose, the test catches all four.

The rules in this repository that break most often are the ones that **give
no visible error**: Quadlet generates the unit, `podman inspect` does not
complain, and the defect only shows up months later. `check.py` checks those,
with no dependency beyond the distro's Python:

```bash
python3 check.py            # 0 if it passes, 1 if there is an error
python3 check.py --selftest # tests the script's own parser
```

| What it checks | Rule |
| --- | --- |
| a unit basename repeated across folders | 1 |
| a bare `$` in `HealthCmd` | 7 |
| a `Label=` with an unquoted space | 12 |
| `localhost` in `HealthCmd` | 13 |
| `Notify=healthy` without `HealthCmd=` | 14 |
| a `Label=` with a backslash | 18 |
| a real tailnet name anywhere in the repo | — |
| **published port collision** | — |
| the version table vs. the tag in `Image=` | — |
| a folder in `apps/` with no table row, and vice versa | — |

The last two blocks are what human discipline was not keeping up with. On its
first run it found **four port collisions that had been in the repository
since July** — adguardhome×gitea, nginx×owntracks, freshrss×owntracks and
beszel×calibre-web-automated. None had shown up because the pairs never came
up at the same time; the second unit would simply have failed to start. In
each pair, whoever arrived later gave up the port.

**Waiving a rule**: when the violation is deliberate, the unit itself says
why — the reason lives next to what it justifies, like the rest of the
comments here:

```ini
# check: ignore ports — this is the EXCLUSIVE alternative to deluge publishing
# directly: either gluetun runs, or deluge runs alone. Never both.
```

The tailnet check is the one exception that is exempted **per line**, not per
file — a test fixture has to contain a name that looks real for the check to
have anything to test:

```python
assert lab("https://traccar.some-real-name.ts.net") == ["some-real-name"]  # check: ignore tailnet
```

Warnings (which do not fail the run) cover what is convention rather than
invariant: a `.network` on a single-container service, and a main container
with neither `wud.watch` nor `AutoUpdate=`.

## Checking versions (`updates.py`)

It automates the rule that is hardest to keep up by hand: **the source is the
project's official GitHub page, not the registry's tag list**. There are 74
`Image=` tags in this repository.

```bash
python3 updates.py            # only what is behind
python3 updates.py --all      # include what is up to date
```

It follows the redirect of `github.com/<org>/<repo>/releases/latest`, which
returns the tag without spending API rate limit. It runs weekly in CI
([`updates.yml`](../.github/workflows/updates.yml)) and puts the result in the
job summary.

**The GitHub repository is derived from the image where possible**:
`ghcr.io/<org>/<x>` mirrors the owner, and `lscr.io/linuxserver/<x>` becomes
`linuxserver/docker-<x>`. Where it cannot be derived, it is declared in
`apps/<app>/install.ini`:

```ini
[upstream]
vaultwarden = dani-garcia/vaultwarden
immich-postgres = -          # `-` = do not compare
```

The `-` matters as much as the rest, and it is where the knowledge the tool
does not have on its own lives:

- **an infra base image** (Postgres, Redis, Mosquitto, nginx) follows the
  app's compose, not its own upstream;
- **a component pinned by the app**: karakeep's Meilisearch and
  paperless-ngx's Gotenberg are the version *that app's* official compose
  validates — their upstream being ahead is not being behind;
- **versioning that is not the project's**: the netboot.xyz image versions as
  `0.7.6-nbxyzNN` (a LinuxServer build) while the repository's releases are
  for the menu (`3.0.2`). Comparing the two is exactly the false positive
  rule 9 warns about.

The comparison uses only the common version prefix, otherwise LinuxServer's
`4.0.19.2979-ls320` release would say an image pinned at `4.0.19` is behind.

**A GitHub release is not a published image.** ghost announced `v6.57.0` while
Docker Hub still only had `6.56.0-alpine` — check that the tag exists in the
variant the unit uses before changing `Image=`, otherwise the service will not
start:

```bash
podman manifest inspect docker.io/library/ghost:6.57.0-alpine
```
