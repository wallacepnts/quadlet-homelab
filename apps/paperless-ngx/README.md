# Paperless-ngx — Podman Quadlet (rootless)

**[🇧🇷 Leia em português](./README.pt-BR.md)**

A [Paperless-ngx](https://docs.paperless-ngx.com) (a self-hosted document
manager — OCR, indexing, full-text search) deploy via Podman Quadlet, migrated
from the
[official](https://github.com/paperless-ngx/paperless-ngx/blob/dev/docker/compose/docker-compose.sqlite-tika.yml)
`docker-compose.sqlite-tika.yml` (SQLite as the database, with Office document
support through Tika + Gotenberg).

## Architecture

Four containers on the `paperless-ngx-net.network` network:

- `paperless-ngx-broker` — Valkey (the asynchronous task queue — OCR,
  indexing — Redis-compatible)
- `paperless-ngx-gotenberg` — converts Office documents and `.eml` files to
  PDF before OCR
- `paperless-ngx-tika` — extracts text and metadata from Office documents
- `paperless-ngx` — the application, exposing `8000` (mapped to `8091` on the
  host — `8000` is already in use by [Downtify](../media-stack/) here)

`paperless-ngx` only starts once the broker and gotenberg report `healthy`
(`Requires=`/`After=` in `[Unit]`, the same pattern as
[karakeep](../karakeep/)/[any-sync-bundle](../any-sync-bundle/)).
**Tika is the exception**: the official image has no `curl`, no `wget` and no
network tool at all
([TIKA-3333](https://issues.apache.org/jira/browse/TIKA-3333), still open
upstream), so no `HealthCmd=` can be declared on it — `Requires=`/`After=`
still guarantees the start *order*, it just does not wait for it to actually
be ready to accept connections. In practice that is rarely a problem:
Paperless only talks to Tika while processing an Office document
(asynchronously, through the queue), not during its own startup.

SQLite (an embedded database in `data/`) was chosen deliberately — it saves
one more Postgres just for this service; see the Auto-update section for the
trade-off.

## Files

```
paperless-ngx-net.network          # the dedicated network
paperless-ngx-broker.container     # Valkey (the queue)
paperless-ngx-gotenberg.container  # Office → PDF conversion
paperless-ngx-tika.container       # text/metadata extraction
paperless-ngx.container            # the application
```

## Prerequisites

- Rootless Podman with systemd `--user` working
- `openssl` (to generate the secret)

## Installation

```bash
python3 install.py paperless-ngx            # dry-run: shows what it will do
python3 install.py paperless-ngx --apply
```

For the local network only, `--access local`; on the tailnet and the LAN,
`--access both`. Adding `--href-local` points the dashboard link at the LAN.
The script creates the directories, writes the `.env`, generates the secrets,
fixes the volumes' ownership, starts the service and prints the address at the
end — see [Installing and operating](../../docs/installing.md).

Reach it through [tsdproxy](../tsdproxy/) (tailnet) at
`https://paperless.<your-tailnet>.ts.net`, or locally at
`http://localhost:8091`.

<details>
<summary><b>Manual installation</b> (advanced) — the same steps, one at a time</summary>


```bash
# 1. Download the units into a dedicated subfolder (no need to clone the
#    repository)
mkdir -p ~/.config/containers/systemd/paperless-ngx
for f in paperless-ngx-net.network paperless-ngx-broker.container \
         paperless-ngx-gotenberg.container paperless-ngx-tika.container \
         paperless-ngx.container; do
  wget -P ~/.config/containers/systemd/paperless-ngx/ \
    "https://raw.githubusercontent.com/wallacepnts/quadlet-homelab/main/apps/paperless-ngx/$f"
done

# 2. Data directories — a bind mount requires them to exist before the start
mkdir -p ~/.config/containers/volumes/paperless-ngx/{broker,data,media,export,consume}
podman unshare chown -R 999:999 ~/.config/containers/volumes/paperless-ngx/redis   # the broker runs with User=999

# 3. Secret — the key used to sign sessions and tokens
mkdir -p ~/.config/containers/secrets/paperless-ngx
openssl rand -base64 64 | tr -d '\n' > ~/.config/containers/secrets/paperless-ngx/secret-key.txt
chmod 600 ~/.config/containers/secrets/paperless-ngx/secret-key.txt
podman secret create paperless-ngx-secret-key ~/.config/containers/secrets/paperless-ngx/secret-key.txt

# 4. Non-secret env — download the example
#    the user running Podman (the same owner as the volumes above)
mkdir -p ~/.config/containers/env
wget -O ~/.config/containers/env/paperless-ngx.env \
  https://raw.githubusercontent.com/wallacepnts/quadlet-homelab/main/apps/paperless-ngx/.env.example
sed -i "s/^USERMAP_UID=.*/USERMAP_UID=$(id -u)/;s/^USERMAP_GID=.*/USERMAP_GID=$(id -g)/" \
  ~/.config/containers/env/paperless-ngx.env

# 5. Start it (broker/gotenberg/tika come up first, via Requires=)
systemctl --user daemon-reload
systemctl --user start paperless-ngx
```

Create the first admin user (there is no default password, unlike some other
services here):

```bash
podman exec -it paperless-ngx python3 manage.py createsuperuser
```

Reach it through [tsdproxy](../tsdproxy/) (tailnet) at
`https://paperless.<your-tailnet>.ts.net`, or locally at
`http://localhost:8091`.

**Automatic document consumption**: any file dropped into
`volumes/paperless-ngx/consume/` is processed and imported by itself — the
"inbox" folder, like [Calibre-Web-Automated](../calibre-web-automated/)'s
`/cwa-book-ingest`, except that here the processed file is removed from the
folder afterwards (it is not permanent storage).

</details>

## OCR in another language

The image only installs the English, German, Italian, Spanish and French
Tesseract packages by default. The `.env.example` ships
`PAPERLESS_OCR_LANGUAGE=por` **and** `PAPERLESS_OCR_LANGUAGES=por` (Portuguese
here) — both are required: the second installs the `tesseract-ocr-por` package
on the first start, the first sets the language actually used for recognition.
Setting only one of the two does not work (tested — without
`PAPERLESS_OCR_LANGUAGES` the language never becomes available to Tesseract,
even with `PAPERLESS_OCR_LANGUAGE` pointing at it).

`por` is the only Portuguese code Tesseract has — there is no separate
Brazil/Portugal variant in OCR, so `por` is the right option regardless of
variant. **That is OCR only**, distinct from the Paperless-ngx interface's own
language: the UI has a specific `pt-BR` option, but it is chosen **per user**
inside the app (Settings → Language, after logging in) — there is no
environment variable for it; each account sets its own.

## `Notify=healthy` with an image that already has a built-in HEALTHCHECK

The same trap as karakeep: the official Paperless-ngx image already ships a
`HEALTHCHECK` in its Dockerfile (`curl ... http://localhost:8000`), but that
is not enough for Quadlet — `Notify=healthy` requires a `HealthCmd=` declared
explicitly in the `.container` too, repeating the same command
([rule 14](../../docs/conventions.md)).

## Auto-update

None of the four containers has `AutoUpdate=` — explicit tags, bumped by
hand ([rule 9](../../docs/conventions.md)). `wud.watch=true` only on the main
container (broker/gotenberg/tika are internal dependencies, the same criterion
already used for Postgres/Meilisearch/Redis here). The reason for manual: the
embedded SQLite (documents plus the search index) is the user's real data — an
HTTP healthcheck does not cover a broken schema migration during a version
change, the same reasoning as vaultwarden.

## Backup & recovery

What actually matters is `data/` (the SQLite database plus the index) and
`media/` (the documents themselves — the largest in size). `export/` and
`consume/` are transit folders and need no backup. `broker/` is only a
transient queue, recreatable from scratch with no loss. Stop everything
first:

```bash
systemctl --user stop paperless-ngx paperless-ngx-broker paperless-ngx-gotenberg paperless-ngx-tika
tar -czf paperless-ngx-backup-$(date +%Y%m%d-%H%M%S).tar.gz \
  -C ~/.config/containers/volumes paperless-ngx
systemctl --user start paperless-ngx
```

The secret (`~/.config/containers/secrets/paperless-ngx/`) needs a separate
backup too — without it, existing sessions are invalidated when restoring onto
a new host (it does not block access to the documents, it only drops active
logins).

## Useful commands

```bash
systemctl --user status paperless-ngx paperless-ngx-broker paperless-ngx-gotenberg paperless-ngx-tika
podman logs -f paperless-ngx
podman exec paperless-ngx-broker valkey-cli ping
```

## Credits

Quadlet deploy based on
[Paperless-ngx](https://github.com/paperless-ngx/paperless-ngx).
Original licence: GPL-3.0.
