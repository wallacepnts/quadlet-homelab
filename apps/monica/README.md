# Monica — Podman Quadlet (rootless)

**[🇧🇷 Leia em português](./README.pt-BR.md)**

A [Monica](https://www.monicahq.com) (a personal CRM — relationship history,
contacts, reminders) deploy via Podman Quadlet, using the
`ghcr.io/monicahq/monica-next` image (v5, with SQLite).

## Floating tag — a deliberate exception to rule 9

**No pinned tag** — unlike the rest of the repository. v5 (the SQLite version,
simpler to maintain here) only publishes this image as `:main`, with no
versioned tag at all. Tested in practice before deciding: no `monicahq/monica`
tag on Docker Hub pulls from this host — neither v5's
(`5.0.0-beta.5-apache` and so on) nor stable v4's (`4.1.2-apache`); an access
error on all of them, which looks like the whole repository being inaccessible
rather than a version-specific limitation.
`ghcr.io/monicahq/monica-next:main` was the only image that actually worked.

**An accepted, documented risk**: `:main` is the development branch of pre-1.0
software — it can bring a broken database migration or a schema change with no
warning on any restart or pull. The same exception pattern already used for
dispatcharr/gluetun in the [media-stack](../media-stack/). No `wud.watch=true`,
on purpose — with a floating tag, WUD would have nothing to compare.

If and when v5 has a stable release with a pinned tag (or if Docker Hub
becomes accessible again), change `Image=` and revisit this section.

## Architecture

A single container. **SQLite**, not MySQL/MariaDB (only the older v4 requires
an external database) — simpler, and the user's real data does not justify a
separate Postgres/MySQL here in any case.

**`APP_URL` has to be the real domain, not the `.env.example`'s
placeholder** — tested in practice: leaving `<your-tailnet>` literal does not
break the container (it comes up "healthy" as usual), but the UI does not load
in the browser through tsdproxy — every asset URL (JS/CSS) and internal route
is generated as `http://`, even though the page is served over `https://`
(tsdproxy terminates TLS before reaching the container), and the browser
silently blocks that as "mixed content". Editing `APP_URL` to the real domain
before the first start avoids the problem.

**The right variable is `APP_TRUSTED_PROXIES`, not `TRUSTED_PROXIES`** — the
latter looks obvious but does not exist in this image (it is
`config/trustedproxy.php` → `env('APP_TRUSTED_PROXIES')`); without it
configured, Laravel does not trust tsdproxy's `X-Forwarded-Proto` header and
ends up generating the wrong URLs even with `APP_URL` set correctly.

**The database is redirected inside the persisted volume** — by default the
image writes the SQLite file to `database/database.sqlite`, **outside**
`storage/` (the image's own `entrypoint.sh` warns: "make sure it will be saved
in a persistent volume"). `DB_DATABASE` in the `.container` redirects it to
`storage/database.sqlite`, inside the only mounted volume — without that, the
whole CRM is lost every time the container is recreated.

**`APP_KEY` as a secret via `type=env`, not `target=APP_KEY` without
`type=env`** — tested in practice: the image supports reading a secret from a
file, but only through an `APP_KEY_FILE` variable pointing at the path (its
own convention) — mounting the secret as a plain file is not enough, it
ignores that and generates a new key by itself. Injecting it as an env var
directly is simpler and works first time. Without that key being fixed, a new
one is generated on every start (it persists nowhere), invalidating sessions
and every encrypted field in the database.

It runs as root internally (Apache) — with no `UserNS=keep-id`, the
`entrypoint.sh` already does a `chown -R www-data:www-data` on `storage/` by
itself at start.

## Files

```
monica.container       # main unit
```

## Prerequisites

- Rootless Podman with systemd `--user` working

## Installation

```bash
python3 install.py monica            # dry-run: shows what it will do
python3 install.py monica --apply
```

For the local network only, `--access local`; on the tailnet and the LAN,
`--access both`. Adding `--href-local` points the dashboard link at the LAN.
The script creates the directories, writes the `.env`, generates the secrets,
fixes the volumes' ownership, starts the service and prints the address at the
end — see [Installing and operating](../../docs/installing.md).

Open `http://<host-ip>:9092` (or through [tsdproxy](../tsdproxy/) at
`https://monica.<your-tailnet>.ts.net`) and create the account on first access
(`/register`). **There is no default account in this image** (unlike
[gitea](../gitea/)) — signing up is the only way in.

<details>
<summary><b>Manual installation</b> (advanced) — the same steps, one at a time</summary>


```bash
# 1. Download the units (no need to clone the repository)
mkdir -p ~/.config/containers/systemd
wget -P ~/.config/containers/systemd/ \
  https://raw.githubusercontent.com/wallacepnts/quadlet-homelab/main/apps/monica/monica.container

# 2. Data directory — a bind mount requires it to exist before the start
mkdir -p ~/.config/containers/volumes/monica/storage

# 3. Non-secret env — download the example
#    replace "<your-tailnet>" with the real domain, see below) before starting
mkdir -p ~/.config/containers/env
wget -O ~/.config/containers/env/monica.env \
  https://raw.githubusercontent.com/wallacepnts/quadlet-homelab/main/apps/monica/.env.example

# 4. Secret — APP_KEY (the "base64:" prefix plus 32 random bytes in base64,
#    the same as what `artisan key:generate` itself would produce)
mkdir -p ~/.config/containers/secrets/monica
python3 -c "
import base64, os
print(f'base64:{base64.b64encode(os.urandom(32)).decode()}', end='')
" > ~/.config/containers/secrets/monica/app-key.txt
chmod 600 ~/.config/containers/secrets/monica/app-key.txt
podman secret create monica-app-key ~/.config/containers/secrets/monica/app-key.txt

# 5. Start it
systemctl --user daemon-reload
systemctl --user start monica
```

Open `http://<host-ip>:9092` (or through [tsdproxy](../tsdproxy/) at
`https://monica.<your-tailnet>.ts.net`) and create the account on first access
(`/register`). **There is no default account in this image** (unlike
[gitea](../gitea/)) — signing up is the only way in.

**Email confirmation is mandatory** — with `MAIL_MAILER=log` (this
`.env.example`'s default), the confirmation email is not really sent; it is
written into the container's logs:

```bash
podman logs monica 2>&1 | grep -A5 "verify\|reset-password"
```

The confirmation link shows up there (`.../email/verify/<id>/<hash>?...`) —
opening it completes the signup. The same route works for password recovery
later. Configuring real SMTP (the section below) saves hunting for a link in
the log every time.

</details>

## Configuring real SMTP (optional)

Change this in `monica.env`:

```ini
MAIL_MAILER=smtp
MAIL_HOST=smtp.example.com
MAIL_PORT=587
MAIL_ENCRYPTION=tls
MAIL_USERNAME=your-username
MAIL_FROM_ADDRESS=monica@example.com
MAIL_FROM_NAME=Monica
```

The SMTP password does **not** go in the `.env` — it goes in as a secret,
injected through `MAIL_PASSWORD_FILE` (natively supported by the image's
`entrypoint.sh`, the same convention as the `APP_KEY_FILE` documented above,
but here it works because we are not using the `type=env` shortcut — if you
prefer `type=env,target=MAIL_PASSWORD` directly, that works too and is
simpler):

```bash
mkdir -p ~/.config/containers/secrets/monica
echo -n "the-smtp-password" > ~/.config/containers/secrets/monica/mail-password.txt
chmod 600 ~/.config/containers/secrets/monica/mail-password.txt
podman secret create monica-mail-password \
  ~/.config/containers/secrets/monica/mail-password.txt
```

In `monica.container`, add this alongside the existing
`Secret=monica-app-key,...`:

```ini
Secret=monica-mail-password,type=env,target=MAIL_PASSWORD
```

```bash
systemctl --user daemon-reload
systemctl --user restart monica
```

## Auto-update

**Not applicable** — with no pinned tag there is nothing for Podman to
compare against the registry to decide whether to update
(`AutoUpdate=registry` needs a fully qualified image, floating tag included,
but it would make no sense at all to automatically pick up something that is
already a development branch). Updating here is always manual: `podman pull`
plus a restart, aware of the risk described above.

## Backup & recovery

```bash
systemctl --user stop monica
tar -czf monica-backup-$(date +%Y%m%d-%H%M%S).tar.gz \
  -C ~/.config/containers/volumes monica
systemctl --user start monica
```

`~/.config/containers/secrets/monica/app-key.txt` needs a separate backup
too — without it, the restored database has unreadable encrypted fields (the
key used to encrypt them was a different one).

## Useful commands

```bash
systemctl --user status monica
podman logs -f monica
podman exec monica curl -fsS http://127.0.0.1:80/login
```

## Credits

Quadlet deploy based on [Monica](https://github.com/monicahq/monica)
(AGPL-3.0).
