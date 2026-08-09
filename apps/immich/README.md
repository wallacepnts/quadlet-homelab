# Immich

<img src="https://cdn.jsdelivr.net/gh/homarr-labs/dashboard-icons/svg/immich.svg" width="64" height="64" alt="">

**[🇧🇷 Leia em português](./README.pt-BR.md)**

Photo and video backup and organisation, with face recognition and smart search.

## Install

```bash
qh immich            # shows the plan
qh immich --apply
```

Open `http://<host-ip>:2283` or `https://immich.<your-tailnet>.ts.net`.

<details>
<summary><b>Manual install</b></summary>

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

</details>

## Files

```
immich-machine-learning.container
immich-postgres.container
immich-redis.container
immich.container
immich-net.network
.env.example
install.ini
```

Units in this stack:

- `immich-machine-learning`
- `immich-postgres`
- `immich-redis`
- `immich`
- `immich-n`

## Update

```bash
qh immich --update --apply
```

Pinned to `8e8d64b405ce18f41b8e5ee20aa4687a8ed0022d1298f2ce31cdcf3a76e09411`, `bcf63357191b76a916ae5eb93464d65c07511da41e3bf7a8416db519b40b1c23`, `v3.1.0`. Nothing updates on its own — a new version is applied
when you run the command above.

## Backup

```bash
qh immich --backup --apply --out ~/backups
```

It stops the service, packs the data, the `.env` and the secrets, and starts
it again. Cold on purpose: copying a live database gives an archive that only
fails when you restore it.

To restore, over the current data:

```bash
qh immich --restore ~/backups/immich-20260809-1200.tar.gz --apply
```

It asks you to type `immich` to confirm, because the current data is deleted
before the archive is unpacked.

## Remove

```bash
qh immich --remove --apply           # stops it, keeps the data
qh immich --remove --purge --apply   # and deletes volumes, secrets and .env
```

`--purge` asks for the typed name too. The tailnet node is not deregistered by
this — that is done in the Tailscale admin.

## Commands

```bash
systemctl --user status immich
podman logs -f immich
```

## Credits

[immich-app/immich](https://github.com/immich-app/immich) — AGPL-3.0.

[Official documentation](https://immich.app)
