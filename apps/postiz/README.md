# Postiz

<img src="https://cdn.jsdelivr.net/gh/homarr-labs/dashboard-icons/svg/postiz.svg" width="64" height="64" alt="">

**[🇧🇷 Leia em português](./README.pt-BR.md)**

A social media scheduler: write a post once, pick the channels and the hour, and
it publishes for you. Instagram comes two ways — through a Facebook Business
page, or standalone, straight to a professional Instagram account — alongside
X, LinkedIn, Threads, TikTok, YouTube and others.

**Read [Instagram needs a public media URL](#instagram-needs-a-public-media-url)
before you set up a channel.** It decides whether posting works at all from a
tailnet-only install.

## Install

```bash
qh postiz            # shows the plan
qh postiz --apply
```

Then open `https://postiz.<your-tailnet>.ts.net` and create your account. The
first sign-up works and then the page closes: `DISABLE_REGISTRATION=true` is in
the `.env` the install writes. Measured: the first account is accepted, a second
attempt is refused with `400`, and `can-register` turns `false`. To add someone
later, set it to `false`, restart, create the account, and set it back.

The address has to be the tailnet one. Postiz builds its sign-in and OAuth links
from it, and Meta only accepts an HTTPS redirect. Installing with
`--access local` leaves the link in the unit pointing at the tailnet anyway.

<details>
<summary><b>Manual install (advanced)</b></summary>

```bash
# 1. Download the units (no need to clone the repository)
mkdir -p ~/.config/containers/systemd/postiz ~/.config/containers/env
for f in postiz postiz-postgres postiz-redis postiz-temporal postiz-temporal-postgres; do
  wget -P ~/.config/containers/systemd/postiz/ \
    https://raw.githubusercontent.com/wallacepnts/quadlet-homelab/main/apps/postiz/$f.container
done
wget -P ~/.config/containers/systemd/postiz/ \
  https://raw.githubusercontent.com/wallacepnts/quadlet-homelab/main/apps/postiz/postiz-net.network
wget -O ~/.config/containers/env/postiz.env \
  https://raw.githubusercontent.com/wallacepnts/quadlet-homelab/main/apps/postiz/.env.example
chmod 600 ~/.config/containers/env/postiz.env

# 2. The data directories, each owned by the user its image runs as, and the
#    nginx.conf (see "Signing in")
V=~/.config/containers/volumes/postiz
mkdir -p $V/postgres $V/redis $V/temporal-postgres $V/uploads $V/config
wget -O $V/config/nginx.conf \
  https://raw.githubusercontent.com/wallacepnts/quadlet-homelab/main/apps/postiz/nginx.conf
podman unshare chown -R 70:70   $V/postgres
podman unshare chown -R 999:999 $V/redis $V/temporal-postgres
podman unshare chown -R 33:33   $V/uploads $V/config/nginx.conf

# 3. The secrets. The database URL is built from the password, so it comes second.
mkdir -p ~/.config/containers/secrets/postiz
openssl rand -hex 24 | tr -d '\n' | podman secret create postiz-db-password -
openssl rand -hex 24 | tr -d '\n' | podman secret create postiz-temporal-db-password -
printf 'postgresql://postiz-user:%s@postiz-postgres:5432/postiz' \
  "$(podman secret inspect --showsecret --format '{{.SecretData}}' postiz-db-password)" \
  | podman secret create postiz-database-url -
openssl rand -hex 32 | tr -d '\n' | podman secret create postiz-jwt-secret -

systemctl --user daemon-reload
systemctl --user start postiz
```

</details>

## Files

```
postiz.container                    the app: nginx, backend, frontend, workers
postiz-postgres.container           its database (Postgres 17)
postiz-redis.container              queues and cache (Valkey)
postiz-temporal.container           runs the scheduled publishing
postiz-temporal-postgres.container  Temporal's own database (Postgres 16)
postiz-net.network
nginx.conf                          the image's own, with the session cookie fixed
.env.example                        sign-up switch, Meta keys, media storage
install.ini                         the secrets' recipes
```

Data in `~/.config/containers/volumes/postiz/`: `postgres/`, `temporal-postgres/`,
`redis/` and `uploads/`.

## Signing in

**Postiz does not work behind a `*.ts.net` address as it ships.** It sets the session
cookie with `Domain=.ts.net`, the registrable domain it computes from `FRONTEND_URL`.
`ts.net` is on the Public Suffix List, so every browser refuses a cookie for it. What
you see: the password is accepted (`POST /api/auth/login` answers `200`) and the page
returns to the login form, again and again. Nothing in any log says why.

It did not show in the tests of this service, which ran on `localhost`.

The fix is in the `nginx.conf` this folder installs over the image's own: one line,
`proxy_cookie_domain .ts.net $host;`, in each of the two proxied locations, which
rewrites that `Domain` to the host the browser used. A cookie for any other domain
passes untouched. It is the project's `var/docker/nginx.conf` of `v2.24.0` and nothing
else, so **on a version bump, compare them** and carry the two lines over:

```bash
diff <(curl -s https://raw.githubusercontent.com/gitroomhq/postiz-app/v2.24.0/var/docker/nginx.conf) \
     <(sed -n '/^user /,$p' ~/.config/containers/volumes/postiz/config/nginx.conf)
```

## Instagram needs a public media URL

To publish an image or a video, Postiz hands Instagram a **URL** and Instagram
downloads the file from it (`image_url=...` and `video_url=...` in
`instagram.provider.ts`). With the default local storage that URL is
`https://postiz.<your-tailnet>.ts.net/uploads/...`, which Instagram's servers
cannot reach: it exists only on your tailnet. The Postiz documentation says the
same of every provider that pulls media from a URL, and recommends a CDN.

So the post is created and scheduled, and fails when the hour comes. What the
code and the documentation show, **not tested against Meta with a real account**,
because that needs your Meta app.

The way out the Postiz docs give is **Cloudflare R2**, a bucket with a public URL:
uncomment the block at the bottom of `~/.config/containers/env/postiz.env`, fill
in the six values, and `systemctl --user restart postiz`. The app itself stays
private on the tailnet. R2 has a free tier; it needs a Cloudflare account.

## Connecting Instagram

Both ways use one Meta app, made at [developers.facebook.com](https://developers.facebook.com/apps/creation/)
(type *Other*). Put the keys in `~/.config/containers/env/postiz.env`, then
`systemctl --user restart postiz`.

| | Facebook Business | Standalone |
| --- | --- | --- |
| Needs | an Instagram account linked to a Facebook page | a **professional** Instagram account |
| Keys | `FACEBOOK_APP_ID`, `FACEBOOK_APP_SECRET` | `INSTAGRAM_APP_ID`, `INSTAGRAM_APP_SECRET` |
| Redirect URI | `https://postiz.<your-tailnet>.ts.net/integrations/social/instagram` | `https://postiz.<your-tailnet>.ts.net/integrations/social/instagram-standalone` |
| Meta product | Facebook Login for Business | Instagram Business Login |

The Postiz docs ask for business verification only for **public** apps; for your
own accounts, add them under the app's *App Roles* as *Instagram Tester*. The
scopes to request, step by step, are in the
[official guide](https://docs.postiz.com/self-host/providers/instagram).

## What runs, and why it is five containers

Postiz hands the scheduling to **Temporal**, a workflow engine that keeps each
pending post in a database and runs it at its hour, even across a restart. That
is why a scheduler needs a second database. The official compose also ships
Elasticsearch for Temporal; this does not.

- **No Elasticsearch.** Measured: Temporal's SQL visibility does the job, and one
  container less. It takes one setting, `SKIP_ADD_CUSTOM_SEARCH_ATTRIBUTES=true`.
  Without it the image reserves two `Text` attributes of the three the database
  allows, Postiz needs two more, and the backend dies on boot with
  `Unable to create search attributes: cannot have more than 3 search attribute of type Text`.
- **Valkey in place of Redis 7.2**, like the rest of this repository. Measured
  working: connected, no errors. The Postgres images are the compose's own.
- **Left out of the compose:** `spotlight` (Sentry debugging), `temporal-ui` and
  `temporal-admin-tools`. The compose's `/config` volume is also not mounted:
  nothing in the code reads it.

## Starting, and what it does every time

The image alone is 5.5 GB. The first start takes 25 to 50 seconds; the unit allows more. Two things in the
image's own start command are worth knowing:

- **It downloads the Prisma CLI from npm on every start** (`pnpm dlx prisma@6.5.0`,
  about 244 MB). The container needs internet at start, not only to publish.
- **It then runs `prisma db push --accept-data-loss`.** There is no migration
  history: an update that changes the schema applies it directly, and can drop
  columns. Back up before every update.

It uses about **2 GB of RAM** (the sum of each process's resident set, which counts
shared pages twice, so a ceiling) and 197 processes at rest, plus about 230 MB of
tmpfs.

## Hardening

Everything but the Temporal container is read-only, with no capabilities, and every
one runs as a user other than root. Tested by exercising the app: sign-up, login,
a 9 MB image upload through the nginx buffer, a post scheduled on a channel and
run by the Temporal worker, on a fresh database and on one already in use.

- **Postiz runs as `www-data` (`User=33`)**, which needs no capability at all.
  As root it needs four (`CHOWN`, `DAC_OVERRIDE`, `SETGID`, `SETUID`) just for
  nginx to start.
- **`HOME` points at a tmpfs**, `/home/postiz`, which holds pm2's files and the
  pnpm cache. The image's own `/root` is `0700`.
- **`PidsLimit=512`.** 197 at rest, a peak of 202: the repository's 256 is too
  tight for this one.
- **Temporal is not read-only.** It renders its configuration into
  `/etc/temporal/config` on every start.

Every refusal, with its error, is in
[the refusals](../../docs/hardening.md#refusals-on-record). One of them is easy to
undo by accident: the pnpm cache must stay a tmpfs. Measured with it as a volume,
the backend never opened port 3000 in 2 of 9 starts, with nothing in any log.

## Update

```bash
qh postiz --backup --apply --out ~/backups    # first: see "Starting"
qh postiz --update --apply
```

Pinned to `1.28.1`, `16`, `17-alpine`, `9.1.1-alpine3.24`, `v2.24.0`. Nothing updates
on its own. Postgres follows the compose of the Postiz version you are going to,
so a major jump of its image is its own migration.

## Backup

```bash
qh postiz --backup --apply --out ~/backups
```

It stops the five units, packs the four folders and the secrets, and starts them
again. Cold on purpose: copying a database in use gives a file that only fails at
restore. The scheduled posts live in Temporal's database, so they are in it.

## Remove

```bash
qh postiz --remove --apply           # stops it, keeps the data
qh postiz --remove --purge --apply   # and deletes the volumes and secrets
```

The tailnet node is not deregistered by this — that is done in the Tailscale admin.

## Commands

```bash
systemctl --user status postiz postiz-temporal postiz-postgres postiz-redis postiz-temporal-postgres
podman logs -f postiz
podman exec postiz pm2 list                     # backend, frontend, orchestrator
podman exec postiz-temporal sh -c 'temporal workflow list --address $(hostname -i):7233'
```

If a post fails with `getaddrinfo EAI_AGAIN graph.facebook.com`, that is the DNS of
Podman's network, not Postiz: on the machine this was tested on, the first lookup
after some idle time timed out while the host's resolver never did (0 of 40 against
1 in 20). Postiz reports it as *"The account is missing some permissions"*, the same
message it shows for a real permission problem.

## Credits

[gitroomhq/postiz-app](https://github.com/gitroomhq/postiz-app) — AGPL-3.0

[Official documentation](https://docs.postiz.com)
