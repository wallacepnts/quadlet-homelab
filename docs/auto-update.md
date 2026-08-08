# Auto-update

Why most services here update by hand, and what has to be true before turning
the automatic path on for one of them.

Off by default across the whole repository (rule 9) — enabling it is opt-in,
service by service, and only when rule 9's conditions hold (a real `HealthCmd`
in the image + no critical third-party data at stake, or a deliberate
willingness to accept the risk). [`actual-budget`](../apps/actual-budget/) and
[`homepage`](../apps/homepage/) are the ones enabled today — use their READMEs
as a reference.

### 1. Enable the timer (once, for the whole host)

```bash
systemctl --user enable --now podman-auto-update.timer
```

It runs once a day, checking every container with the
`io.containers.autoupdate` label — there is no need to re-enable it per
service, just this once.

### 2. Check whether the service is a candidate (rule 9)

- Does it have a `HealthCmd` configured in the `.container`? Without one there
  is no automatic rollback — Podman applies the update blind.
- Is there a floating tag that makes sense? On an exact tag (`1.2.3`) the
  digest never changes and `AutoUpdate=` has no effect at all. Check whether
  the project offers something like a pinned major.minor (`8.0`, say) before
  jumping straight to `:latest` — and be suspicious even then (see the real
  case of the MongoDB embedded in
  [any-sync-bundle](../apps/any-sync-bundle/#variants): the version is fixed
  inside the image itself, with no way to pin it separately, and a new tag
  brought a MongoDB that dies with "illegal instruction" on kernel 6.19+ with
  no warning whatsoever).
- Is the data there sensitive or critical enough that you would rather review
  before every bump? (A password vault, or a backend with real state —
  probably not worth it.)

### 3. Enable it in the `.container`

```ini
Image=<registry>/<image>:<floating-tag>
AutoUpdate=registry
```

```bash
systemctl --user daemon-reload
systemctl --user restart <app>
```

### 4. Check, and roll back if you need to

```bash
podman auto-update --dry-run              # a preview, applying nothing
podman auto-update --rollback <container> # roll back by hand
```

Take a backup before any meaningful version bump — automatic rollback only
covers "it did not become `healthy`", not "it became healthy but with a silent
bug in the data" (see each service's Backup section).

### What AutoUpdate needs to work properly

Three pieces, all three mandatory:

1. **A floating tag** (`:latest`, `:2`, and so on) — `AutoUpdate=registry`
   compares the tag's digest against the registry; on a pinned tag (`:v1.4.5`)
   the digest never changes, so there is never anything to update.
2. **`AutoUpdate=registry`** in the `.container` — without that line Podman
   never checks, even with a floating tag.
3. **An active `podman-auto-update.timer`** (`systemctl --user enable --now
   podman-auto-update.timer`) — it is what triggers the check periodically
   (daily, by systemd's default). A single timer, shared by every container of
   this user that has `AutoUpdate=`.

**The part that makes this safe, not merely automatic: a real `HealthCmd`.**
Automatic rollback (going back to the previous image if the update breaks)
only exists if the container has a genuine healthcheck — which in turn
requires a shell or an HTTP client inside the image (`wget`/`curl`, or a raw
TCP check like lubelogger's). Without one, `AutoUpdate=registry` still swaps
the image and restarts by itself, only **with no safety net**: if the new
build is broken, it stays broken until somebody notices and fixes it by hand.
See rule 9, in [Conventions](./conventions.md).

Check the candidates before trusting it blindly: `podman auto-update
--dry-run`.

### Why most of it is off

This repository's default: an explicit tag plus a manual bump, with
auto-update as opt-in. The specific reasons, documented in each service's
README ("Auto-update" or "Updating the images"):

- **any-sync-bundle** — AIO mode with real data (the Anytype identity);
  `HealthCmd` covers "the process answered", not "the update did not silently
  break anything" (the same reasoning as gitea/immich). Every bump is tested
  separately with disposable data before touching the real thing, which
  automatic auto-update does not do on its own (see the service's README).
- **Karakeep** — the Meilisearch version is the one the official
  `docker-compose.yml` recommends; changing it without checking compatibility
  can break search. Chrome follows the same rule, and the embedded SQLite is
  the user's real data (bookmarks, archived pages).
- **Immich** — photos, videos and the face recognition index are the user's
  real and irreplaceable data; database migrations between major versions are
  not rare, and a healthcheck saying "ok" does not cover that.
- **Radicale** — calendars and contacts are the user's real data, and the
  embedded database means a healthcheck does not cover a schema migration.
- **Syncthing** — the same reasoning as ownCloud: synced files are the user's
  real data.
- **vaultwarden** — the image has `wget`/`curl` (so it could be enabled with
  real rollback), but it is a password vault: manual review before updating is
  the default here on purpose, not a technical limitation.
- **zerobyte** — the same reasoning as vaultwarden: it holds the passphrase to
  every other backup, so manual review is preferred even with a real
  `HealthCmd`.
- **lubelogger** — an Ubuntu image with no `curl`/`wget`; the `HealthCmd` uses
  a raw TCP check (rule 13), so it does not even enter the conversation about
  auto-update with real rollback without changing the healthcheck strategy
  first.
- **Calibre-Web-Automated** — the same reasoning as vaultwarden: the database
  (`metadata.db`) plus the library are the user's real data, so review by hand
  before changing version.
- **netboot.xyz** — it has `curl` and a real healthcheck, but checking the
  webapp's changelog before changing tag is preferred (a menu/boot loader is
  sensitive to a version change).
- **Paperless-ngx** — the same reasoning as vaultwarden: the embedded SQLite
  (documents plus the index) is the user's real data, and an HTTP healthcheck
  does not cover a broken schema migration.
- **n8n** — the same reasoning as vaultwarden: saved workflows and credentials
  are the user's real data, and an HTTP healthcheck does not cover an update
  that silently breaks existing workflows.
- **ownCloud** — the same reasoning as karakeep: synced files are the user's
  real data; running on SQLite (a mode the project itself does not support in
  production) is one more reason for manual review.
- **tsdproxy** — no specific technical reason, it simply has not been
  evaluated or enabled yet (it already uses a floating major tag, `:2`, but
  without `AutoUpdate=` that does not trigger anything on its own).
- **AdGuard Home** — the same reasoning as ownCloud/Radicale: DNS is critical
  infrastructure for the whole network, and if it goes down nobody resolves
  any name; manual review before changing version, despite having a real
  `HealthCmd`.
- **Audiobookshelf** — the same reasoning as vaultwarden: reading progress and
  the library are the user's real data.
- **Beszel**, **nginx**, **Ollama/Open WebUI** — all with a real `HealthCmd`
  (so `AutoUpdate=registry` could be enabled with working rollback), but not
  evaluated or enabled by default yet, the same reasoning as tsdproxy.
- **FreshRSS** — the same reasoning as vaultwarden: read articles and saved
  feeds are the user's real data.
- **Authentik** — users, groups and the SSO configuration are real data;
  `server` has a `HealthCmd`, but manual review before updating, all the more
  so because it is authentication infrastructure.
- **Monica** — a case of its own: **there is no pinned tag for auto-update to
  compare against** (only `:main`), see the dedicated section in the
  [service's README](../apps/monica/#floating-tag--a-deliberate-exception-to-rule-9).
