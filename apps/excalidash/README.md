# ExcaliDash

<img src="https://cdn.jsdelivr.net/gh/homarr-labs/dashboard-icons/svg/excalidraw.svg" width="64" height="64" alt="">

**[🇧🇷 Leia em português](./README.pt-BR.md)**

Excalidraw with somewhere to put the drawings: folders, several users, and
links you can share per drawing instead of per instance.

Two containers — the frontend you open and the backend that holds the SQLite
database. The frontend requires the backend, so starting `excalidash` brings
both up.

## First run

Open `http://<host-ip>:8016` or `https://excalidash.<your-tailnet>.ts.net` and
create the account.

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

Both images carry the same tag, and they are bumped together.

## Backup

It stops both, packs the data, the `.env` and the secrets, and starts them
again. The secrets matter here: restoring the database without the same
`JWT_SECRET` logs everyone out.

## Credits

[ExcaliDash](https://github.com/ZimengXiong/ExcaliDash) by
[ZimengXiong](https://github.com/ZimengXiong) — LGPL-3.0

Built on [Excalidraw](https://github.com/excalidraw/excalidraw) — MIT

[Official documentation](https://github.com/ZimengXiong/ExcaliDash#readme)
