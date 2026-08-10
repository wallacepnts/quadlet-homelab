# ExcaliDash

<img src="https://cdn.jsdelivr.net/gh/homarr-labs/dashboard-icons/svg/excalidraw.svg" width="64" height="64" alt="">

**[🇧🇷 Leia em português](./README.pt-BR.md)**

Excalidraw with somewhere to put the drawings: folders, several users, and
links you can share per drawing instead of per instance.

Two containers — the frontend you open and the backend that holds the SQLite
database. The frontend requires the backend, so starting `excalidash` brings
both up.

## Install

```bash
qh excalidash            # shows the plan
qh excalidash --apply
```

Open `http://<host-ip>:8016` or `https://excalidash.<your-tailnet>.ts.net` and
create the account.

<details>
<summary><b>Manual install</b></summary>

```bash
mkdir -p ~/.config/containers/systemd/excalidash ~/.config/containers/env
mkdir -p ~/.config/containers/volumes/excalidash/data

openssl rand -hex 32 | podman secret create excalidash-jwt-secret -
openssl rand -hex 32 | podman secret create excalidash-csrf-secret -

wget -P ~/.config/containers/systemd/excalidash/ \
  https://raw.githubusercontent.com/wallacepnts/quadlet-homelab/main/apps/excalidash/excalidash.container \
  https://raw.githubusercontent.com/wallacepnts/quadlet-homelab/main/apps/excalidash/excalidash-backend.container \
  https://raw.githubusercontent.com/wallacepnts/quadlet-homelab/main/apps/excalidash/excalidash-net.network
wget -O ~/.config/containers/env/excalidash.env \
  https://raw.githubusercontent.com/wallacepnts/quadlet-homelab/main/apps/excalidash/.env.example

systemctl --user daemon-reload
systemctl --user start excalidash
```

</details>

## Files

```
excalidash.container           the frontend, and the unit you start
excalidash-backend.container   the API and the database
excalidash-net.network         the network the two share
.env.example                   environment
install.ini                    the secrets' recipes
```

Data in `~/.config/containers/volumes/excalidash/data`, on port **8016**.
`DATABASE_PROVIDER=sqlite` keeps everything in that directory; the project also
speaks Postgres, which this deployment does not run.

The frontend reaches the backend by unit name, through `BACKEND_URL` — the
image defaults to the hostname `backend`, which would need a container called
that.

## Signing in with Authentik

`AUTH_MODE=local` ships by default: accounts live in ExcaliDash. To use
[Authentik](../authentik) instead, set `AUTH_MODE=hybrid` (both) or
`oidc_enforced` (only Authentik) and fill `OIDC_ISSUER_URL`, `OIDC_CLIENT_ID`,
`OIDC_CLIENT_SECRET` and `OIDC_REDIRECT_URI` in the `.env`.

## Update

```bash
qh excalidash --update --apply
```

Pinned to `0.5.1`. Both images carry the same tag, and they are bumped
together.

## Backup

```bash
qh excalidash --backup --apply --out ~/backups
```

It stops both, packs the data, the `.env` and the secrets, and starts them
again. The secrets matter here: restoring the database without the same
`JWT_SECRET` logs everyone out.

To restore, over the current data:

```bash
qh excalidash --restore ~/backups/excalidash-20260810-1200.tar.gz --apply
```

## Remove

```bash
qh excalidash --remove --apply           # stops it, keeps the data
qh excalidash --remove --purge --apply   # and deletes volumes, secrets and .env
```

## Commands

```bash
systemctl --user status excalidash
podman logs -f excalidash-backend
podman exec excalidash-backend node -e "require('http').get('http://127.0.0.1:8000/health', r => console.log(r.statusCode))"
```

## Credits

[ExcaliDash](https://github.com/ZimengXiong/ExcaliDash) by
[ZimengXiong](https://github.com/ZimengXiong) — LGPL-3.0

Built on [Excalidraw](https://github.com/excalidraw/excalidraw) — MIT

[Official documentation](https://github.com/ZimengXiong/ExcaliDash#readme)
