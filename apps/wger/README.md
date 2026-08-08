# wger — Podman Quadlet (rootless)

**[🇧🇷 Leia em português](./README.pt-BR.md)**

Deploy do [wger](https://github.com/wger-project/wger) (planejamento e
acompanhamento de treinos) via Podman Quadlet, usando a imagem oficial
`docker.io/wger/server`.

Routines, a log of sets and loads, body measurements, weight, and a public
exercise database with images and video. It replaced Wingfit in this
repository.

## Architecture

**A single container.** This is a deliberate divergence from the project:
wger's production `docker-compose.yml` stands up **six** containers — `web`,
`nginx`, Postgres, Redis, `celery_worker` e `celery_beat`.

For a single user, that is far too expensive. The unit here uses the same
`wger/server` with three changes ([rule 22](../../docs/conventions.md)):

| Piece of the official compose | Here | How |
| --- | --- | --- |
| Postgres | **SQLite** | `PS_DATABASE_URI=sqlite:////home/wger/db/database.sqlite` |
| Redis | an in-memory cache | `DJANGO_CACHE_BACKEND=…LocMemCache` |
| celery worker + beat | nothing | `USE_CELERY=False` |
| nginx | the server itself | it serves the static files directly |

The SQLite path is not an invention: it is the same `PS_DATABASE_URI` the
project's `dev-sqlite` compose uses, on the same image. Tested all the way
through — Django's migrations run and the app answers.

**What is lost without Celery**: the automatic, background sync of the public
exercise and ingredient database. It can be pulled on demand (see below). If
you use the ingredient search a lot, it is worth reconsidering.

Hardening: it takes `ReadOnly=true` and `DropCapability=ALL`. **There is no
`User=`** because the image already runs as uid 1000 (the `wger` user) —
declaring it again would be redundant.

## Files

```
wger.container   # main unit
.env.example     # database, hosts, signup, syncing
```

## Installation

```bash
python3 install.py wger            # dry-run: shows what it will do
python3 install.py wger --apply
```

For the local network only, `--access local`; on the tailnet and the LAN,
`--access both`. Adding `--href-local` points the dashboard link at the LAN.
The script creates the directories, writes the `.env`, generates the secrets,
fixes the volumes' ownership, starts the service and prints the address at the
end — see [Installing and operating](../../docs/installing.md).

Open `http://<host-ip>:8102` (or through [tsdproxy](../tsdproxy/) at
`https://wger.<your-tailnet>.ts.net`).

<details>
<summary><b>Manual installation</b> (advanced) — the same steps, one at a time</summary>


```bash
# 1. Download the unit (no need to clone the repository)
mkdir -p ~/.config/containers/systemd
wget -P ~/.config/containers/systemd/ \
  https://raw.githubusercontent.com/wallacepnts/quadlet-homelab/main/apps/wger/wger.container

# 2. Directories, with the owner matching the image's uid 1000
mkdir -p ~/.config/containers/volumes/wger/{db,static,media}
podman unshare chown -R 1000:1000 ~/.config/containers/volumes/wger

# 3. Variables — replace <your-tailnet> in ALLOWED_HOSTS and CSRF_TRUSTED_ORIGINS
mkdir -p ~/.config/containers/env
wget -O ~/.config/containers/env/wger.env \
  https://raw.githubusercontent.com/wallacepnts/quadlet-homelab/main/apps/wger/.env.example
${EDITOR:-vi} ~/.config/containers/env/wger.env

# 4. SECRET_KEY — it signs sessions and cookies
mkdir -p ~/.config/containers/secrets/wger
openssl rand -hex 32 > ~/.config/containers/secrets/wger/secret-key.txt
chmod 600 ~/.config/containers/secrets/wger/secret-key.txt
podman secret create wger-secret-key ~/.config/containers/secrets/wger/secret-key.txt

# 5. Start it. The first start runs ALL of Django's migrations and collects
#    the static files — it takes minutes, hence TimeoutStartSec=300.
systemctl --user daemon-reload
systemctl --user start wger
podman logs -f wger    # follow it until it stops applying migrations
```

Open `http://<host-ip>:8102` (ou via [tsdproxy](../tsdproxy/) em
`https://wger.<your-tailnet>.ts.net`).

</details>

## Creating your account

The `.env.example` already ships `ALLOW_REGISTRATION=False`. To create the
first user, the route is `manage.py` — there is no need to open signup:

```bash
podman exec -it wger python3 manage.py createsuperuser
```

## Syncing exercises and ingredients

Without Celery this does not run on its own. Pull it whenever you want:

```bash
podman exec wger python3 manage.py sync-exercises
podman exec wger python3 manage.py download-exercise-images
podman exec wger python3 manage.py sync-ingredients        # large, slow
```

A `systemd --user` timer is worth it if you want it periodic — the same
pattern as the sidecars described in [zerobyte](../zerobyte/).

## Auto-update

No `AutoUpdate=` — an explicit tag (`2.6.0`), bumped by hand
(rule 9 of the [conventions](../../docs/conventions.md)). Two extra reasons here: a logged workout is real data, and wger is Django,
so bumping the version means running migrations — which do not go back. Back
up first.

Upstream publishes `-dev` and `-alpha` alongside the stable releases
(`2.6-dev`, `2.7.0-alpha1`), hence the `wud.tag.include` restricting it to
`X.Y.Z`.

## Backup & recovery

```bash
systemctl --user stop wger
tar -czf wger-backup-$(date +%Y%m%d-%H%M%S).tar.gz \
  -C ~/.config/containers/volumes wger
systemctl --user start wger
```

`db/` is the entire database; `media/` is the images you uploaded.
`static/` regenerates at start. The secret needs a separate backup — without
the same `SECRET_KEY`, every session drops.

## Useful commands

```bash
systemctl --user status wger
podman logs -f wger
podman exec wger python3 manage.py showmigrations | tail -20
```

## Credits

Quadlet deploy based on [wger](https://github.com/wger-project/wger)
(AGPL-3.0).
