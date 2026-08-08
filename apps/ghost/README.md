# Ghost — Podman Quadlet (rootless)

**[🇧🇷 Leia em português](./README.pt-BR.md)**

Deploy do [Ghost](https://ghost.org) (plataforma de blog/newsletter
self-hosted) via Podman Quadlet, usando a imagem oficial
[`ghost`](https://hub.docker.com/_/ghost) (variante Alpine).

## SQLite in development mode — a deliberate decision

Ghost **only officially supports SQLite in `development` mode**
(`NODE_ENV=development`) — real production, by the project's own account,
requires MySQL. The same trade-off already accepted for
[ownCloud](../owncloud/) here: a single container, simpler, outside what the
projeto recomenda oficialmente, mas funcional pra uso pessoal/baixo
volume. If the "official" route is needed later, switching to MySQL is just
adding a database container and changing the three `database__*` variables
(see the [official documentation](https://docs.ghost.org/install/docker)).

## Architecture

A single container, running as root internally (no `PUID`/`PGID`, no
`UserNS=keep-id` — the image adjusts permissions itself, the same pattern as
several other apps here). A single volume
(`/var/lib/ghost/content`) — guarda o banco SQLite, imagens/temas
uploads, and the configuration.

The healthcheck uses the site endpoint of Ghost's own admin API
(`/ghost/api/admin/site/`, unauthenticated and light) — tested in practice,
and cheaper than fetching the whole home page.

**Expected noise in the log**: Ghost tries to work out its own favicon's size
by fetching the configured `url` — if that URL does not resolve back to the
container itself (common behind a proxy/tailnet, tested in practice), an
`ECONNREFUSED`/`IMAGE_SIZE_URL` error appears in the log. Cosmetic; it does
not stop the site working.

**Sem acesso local por IP:porta depois de configurar a `url`** —
tested in practice: as soon as `url` points at the real domain
(tsdproxy/tailnet), o Ghost passa a redirecionar (301) **qualquer**
any request that does not match that URL, `http://<host-ip>:9094` included —
this is not a bug, it is the application's expected behaviour (it treats `url`
as canonical).
Acessar sempre pela URL configurada (`https://ghost.<your-tailnet>.ts.net`),
not by the host's IP.

## Files

```
ghost.container       # main unit
```

## Prerequisites

- Rootless Podman with systemd `--user` working

## Installation

```bash
python3 install.py ghost            # dry-run: shows what it will do
python3 install.py ghost --apply
```

For the local network only, `--access local`; on the tailnet and the LAN,
`--access both`. Adding `--href-local` points the dashboard link at the LAN.
The script creates the directories, writes the `.env`, generates the secrets,
fixes the volumes' ownership, starts the service and prints the address at the
end — see [Installing and operating](../../docs/installing.md).

Reach it through [tsdproxy](../tsdproxy/) at
`https://ghost.<your-tailnet>.ts.net/ghost/` and create the admin account in
the first-access installation wizard. **It only works through the URL
configured in step 3** — local access straight at `http://<host-ip>:9094` is
redirected to that URL as soon as `url` points at the real domain (see "No
local access…" above).

<details>
<summary><b>Manual installation</b> (advanced) — the same steps, one at a time</summary>


```bash
# 1. Download the units (no need to clone the repository)
mkdir -p ~/.config/containers/systemd
wget -P ~/.config/containers/systemd/ \
  https://raw.githubusercontent.com/wallacepnts/quadlet-homelab/main/apps/ghost/ghost.container

# 2. Data directory — a bind mount requires it to exist before the start
mkdir -p ~/.config/containers/volumes/ghost/content

# 3. Non-secret env — download the example
#    antes de subir (mesmo motivo do Monica: deixar o placeholder gera
#    link/e-mail quebrado)
mkdir -p ~/.config/containers/env
wget -O ~/.config/containers/env/ghost.env \
  https://raw.githubusercontent.com/wallacepnts/quadlet-homelab/main/apps/ghost/.env.example

# 4. Start it
systemctl --user daemon-reload
systemctl --user start ghost
```

Reach it through [tsdproxy](../tsdproxy/) at
`https://ghost.<your-tailnet>.ts.net/ghost/` and create the admin account in
the first-access installation wizard. **It only works through the URL
configured in step 3** — local access straight at `http://<host-ip>:9094` is
redirected to that URL as soon as `url` points at the real domain (see "No
local access…" above).

</details>

## Auto-update

No `AutoUpdate=` — an explicit tag (`6.56.0-alpine`), bumped by hand
([rule 9](../../docs/conventions.md)). The image has `wget` and a real
healthcheck — `AutoUpdate=registry` could be enabled with working rollback,
but posts and configuration are the user's real data, so review by hand before
updating. Schema migrations between Ghost's major versions are not rare either
— check the changelog before changing tag.

## Backup & recovery

```bash
systemctl --user stop ghost
tar -czf ghost-backup-$(date +%Y%m%d-%H%M%S).tar.gz \
  -C ~/.config/containers/volumes ghost
systemctl --user start ghost
```

## Useful commands

```bash
systemctl --user status ghost
podman logs -f ghost
podman exec ghost wget -qO- http://127.0.0.1:2368/ghost/api/admin/site/
```

## Credits

Quadlet deploy based on [Ghost](https://github.com/TryGhost/Ghost)
(MIT).
