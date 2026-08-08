# nginx — Podman Quadlet (rootless)

**[🇧🇷 Leia em português](./README.pt-BR.md)**

A [nginx](https://nginx.org) deploy as a static file server via Podman
Quadlet, using the official [`nginx`](https://hub.docker.com/_/nginx) image
(the Alpine variant).

## Architecture

A single container. Two bind mounts, both `:ro` on purpose (nginx only
reads; you are the one who edits, straight on the host):

- `html/` → `/usr/share/nginx/html` — the static content itself (whatever is
  mounted here is what gets served).
- `conf.d/` → `/etc/nginx/conf.d` — the server blocks. **It cannot be
  empty**: mounting an empty directory over `/etc/nginx/conf.d` erases the
  image's built-in `default.conf` — with no `server { listen 80; }` at all,
  nginx comes up but listens on no port whatsoever (`wget: can't connect to
  remote host` in the healthcheck, tested in practice). That is why this
  repository versions a copy of the image's original `default.conf` under
  `conf.d/` — downloaded in step 2 of the installation; edit that file (or
  add other `.conf` files alongside it) to customise the routes.

## Files

```
nginx.container         # main unit

conf.d/
└── default.conf        # a copy of the image's original default.conf
```

No `.env.example` — nothing here depends on an environment variable.

## Prerequisites

- Rootless Podman with systemd `--user` working

## Installation

```bash
python3 install.py nginx            # dry-run: shows what it will do
python3 install.py nginx --apply
```

For the local network only, `--access local`; on the tailnet and the LAN,
`--access both`. Adding `--href-local` points the dashboard link at the LAN.
The script creates the directories, writes the `.env`, generates the secrets,
fixes the volumes' ownership, starts the service and prints the address at the
end — see [Installing and operating](../../docs/installing.md).

Open it at `http://<host-ip>:8103`, ou via [tsdproxy](../tsdproxy/)
(tailnet) em `https://nginx.<your-tailnet>.ts.net`.

<details>
<summary><b>Manual installation</b> (advanced) — the same steps, one at a time</summary>


```bash
# 1. Download the units (no need to clone the repository)
mkdir -p ~/.config/containers/systemd
wget -P ~/.config/containers/systemd/ \
  https://raw.githubusercontent.com/wallacepnts/quadlet-homelab/main/apps/nginx/nginx.container

# 2. Data directories — a bind mount requires them to exist before the start
mkdir -p ~/.config/containers/volumes/nginx/{html,conf.d}
echo "<h1>Funcionando</h1>" > ~/.config/containers/volumes/nginx/html/index.html
wget -O ~/.config/containers/volumes/nginx/conf.d/default.conf \
  https://raw.githubusercontent.com/wallacepnts/quadlet-homelab/main/apps/nginx/conf.d/default.conf

# 3. Start it
systemctl --user daemon-reload
systemctl --user start nginx
```

Open it at `http://<host-ip>:8103`, ou via [tsdproxy](../tsdproxy/)
(tailnet) em `https://nginx.<your-tailnet>.ts.net`.

</details>

## Auto-update

No `AutoUpdate=` — an explicit tag (`1.30.4-alpine`, atual `stable`), bumped by hand
([rule 9](../../docs/conventions.md)). The image has `wget` and a real healthcheck — `AutoUpdate=registry` could be
enabled with genuine rollback, but it is kept manual by default like the rest
of the repository.

## Backup & recovery

```bash
tar -czf nginx-backup-$(date +%Y%m%d-%H%M%S).tar.gz \
  -C ~/.config/containers/volumes nginx
```

No need to stop the container (read-only, with no state of its own beyond
the static content).

## Useful commands

```bash
systemctl --user status nginx
podman logs -f nginx
podman exec nginx wget -qO- http://127.0.0.1:80/
```

## Credits

Deploy Quadlet usando a imagem oficial [nginx](https://hub.docker.com/_/nginx)
(BSD-2-Clause).
