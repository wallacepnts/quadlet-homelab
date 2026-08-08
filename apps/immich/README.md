# Immich — Podman Quadlet (rootless)

**[🇧🇷 Leia em português](./README.pt-BR.md)**

An [Immich](https://immich.app) (self-hosted photo and video backup and
organisation, with face recognition and smart search — an alternative
ao Google Photos) via Podman Quadlet, migrado do
[`docker-compose.rootless.yml`](https://github.com/immich-app/immich/blob/main/docker/docker-compose.rootless.yml)
official one (the variant already designed for rootless Docker/Podman —
fixed uid/gid
fixos em vez de root).

## Architecture

Quatro containers na rede `immich-net.network`:

- `immich-postgres` — Postgres with a vector extension (VectorChord/
  pgvecto.rs, the project's own image — not generic Postgres) — the data plus
  the similarity search index
- `immich-redis` — the asynchronous job queue (Valkey, Redis-compatible)
- `immich-machine-learning` — reconhecimento facial, busca por
  text/image (CLIP), automatic tagging
- `immich` — the application, exposing `2283`

`immich` only starts once postgres and redis report `healthy`
(`Requires=`/`After=`, the same pattern as
[paperless-ngx](../paperless-ngx/)/[karakeep](../karakeep/)) — o
the official compose does not list `machine-learning` as a start dependency
(the app only calls it over HTTP when it needs to; it does not block boot
waiting).

**Hostnames fixos**: o Immich resolve `database`/`redis`/
`immich-machine-learning` as those three services' **default** addresses
(these are not merely configurable environment variables — `DB_HOSTNAME` and
`REDIS_HOSTNAME` have those values as defaults, and the ML address is saved in
the application's own settings after the first start). That is why the three
dependency containers use `NetworkAlias=` with those exact names, without
having to declare the host variables
explicitamente.

**Hardening replicado do compose oficial**: `NoNewPrivileges=true` +
`--cap-drop=NET_RAW` nos quatro containers, `UserNS=keep-id` (a variante
the "rootless" one already runs as a fixed uid/gid `1000:1000`, with no
internal usermod —
mesmo motivo do Jellyfin/Seerr no [media-stack](../media-stack/)).

## Files

```
immich-net.network                 # rede dedicada
immich-redis.container             # fila (Valkey)
immich-postgres.container          # Postgres + the vector extension
immich-machine-learning.container  # reconhecimento facial / busca smart
immich.container                   # the application
```

## Prerequisites

- Rootless Podman with systemd `--user` working
- `openssl` (to generate the secret)
- Spare RAM for `immich-machine-learning` — the face recognition and CLIP
  models consume real memory when loaded; on a small homelab it is worth
  watching consumption over the first few days of use

## Installation

```bash
python3 install.py immich            # dry-run: shows what it will do
python3 install.py immich --apply
```

For the local network only, `--access local`; on the tailnet and the LAN,
`--access both`. Adding `--href-local` points the dashboard link at the LAN.
The script creates the directories, writes the `.env`, generates the secrets,
fixes the volumes' ownership, starts the service and prints the address at the
end — see [Installing and operating](../../docs/installing.md).

Reach it through [tsdproxy](../tsdproxy/) (tailnet) at
`https://immich.<your-tailnet>.ts.net`, or locally at
`http://localhost:2283`. Create the first account (it automatically becomes
admin) through the UI itself; there is no default username or password.

<details>
<summary><b>Manual installation</b> (advanced) — the same steps, one at a time</summary>


```bash
# 1. Baixar as units pra uma subpasta dedicada (sem precisar clonar o
#    repository)
mkdir -p ~/.config/containers/systemd/immich
for f in immich-net.network immich-redis.container immich-postgres.container \
         immich-machine-learning.container immich.container; do
  wget -P ~/.config/containers/systemd/immich/ \
    "https://raw.githubusercontent.com/wallacepnts/quadlet-homelab/main/apps/immich/$f"
done

# 2. Data directories — a bind mount requires them to exist before the start
mkdir -p ~/.config/containers/volumes/immich/{upload,postgres,redis,ml-cache,ml-dotcache,ml-config}
podman unshare chown -R 999:999 ~/.config/containers/volumes/immich/postgres   # o Postgres roda com User=999

# 3. Secret — senha do Postgres, mesma usada nos dois containers
mkdir -p ~/.config/containers/secrets/immich
openssl rand -base64 24 | tr -d '\n' > ~/.config/containers/secrets/immich/db-password.txt
chmod 600 ~/.config/containers/secrets/immich/db-password.txt
podman secret create immich-db-password ~/.config/containers/secrets/immich/db-password.txt

# 4. Non-secret env — download the example
mkdir -p ~/.config/containers/env
wget -O ~/.config/containers/env/immich.env \
  https://raw.githubusercontent.com/wallacepnts/quadlet-homelab/main/apps/immich/.env.example

# 5. Start it (redis e postgres sobem primeiro via Requires=)
systemctl --user daemon-reload
systemctl --user start immich
```

Reach it through [tsdproxy](../tsdproxy/) (tailnet) at
`https://immich.<your-tailnet>.ts.net`, or locally at
`http://localhost:2283`. Create the first account (it automatically becomes
admin) through the UI itself; there is no default username or password.

**The mobile apps** (iOS/Android) sync photos automatically — point them at
the same address used in the browser, on the app's login screen.

</details>

## Auto-update

No `AutoUpdate=` — explicit tags (`v3.1.0` for the app and ML; Postgres and
Redis locked to the official compose's exact tag+digest combination), bumped by
hand ([rule 9](../../docs/conventions.md)). Photos, videos and the face
recognition index are the user's real and irreplaceable data — review by hand
before updating, and check the changelog: database migrations between Immich's
major versions are not uncommon.

## Backup & recovery

What actually matters, in order of criticality: `upload/` (the photos and
videos themselves — unrecoverable if lost) and `postgres/` (metadata, albums,
recognised faces, shares — rebuildable by reprocessing the photos, but with a
lot of work). `redis/` is only the job queue and `ml-*` is a model cache; both
can be recreated from scratch with no loss.

```bash
systemctl --user stop immich immich-machine-learning immich-postgres immich-redis
tar -czf immich-backup-$(date +%Y%m%d-%H%M%S).tar.gz \
  -C ~/.config/containers/volumes immich
systemctl --user start immich
```

The secret (`~/.config/containers/secrets/immich/`) needs a separate backup
too.

## Useful commands

```bash
systemctl --user status immich immich-machine-learning immich-postgres immich-redis
podman logs -f immich
podman exec immich-postgres healthcheck.sh
```

## Credits

Quadlet deploy based on [Immich](https://github.com/immich-app/immich).
Original licence: AGPL-3.0.
