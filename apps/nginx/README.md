# nginx

<img src="https://cdn.jsdelivr.net/gh/homarr-labs/dashboard-icons/svg/nginx.svg" width="64" height="64" alt="">

**[🇧🇷 Leia em português](./README.pt-BR.md)**

A static file server.

## Install

```bash
qh nginx            # shows the plan
qh nginx --apply
```

Open `http://<host-ip>:8103` or `https://nginx.<your-tailnet>.ts.net`.

<details>
<summary><b>Manual install</b></summary>

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

</details>

## Files

```
nginx.container
install.ini
```

## Update

```bash
qh nginx --update --apply
```

Pinned to `1.30.4-alpine`. Nothing updates on its own — a new version is applied
when you run the command above.

## Backup

```bash
qh nginx --backup --apply --out ~/backups
```

It stops the service, packs the data, the `.env` and the secrets, and starts
it again. Cold on purpose: copying a live database gives an archive that only
fails when you restore it.

To restore, over the current data:

```bash
qh nginx --restore ~/backups/nginx-20260809-1200.tar.gz --apply
```

It asks you to type `nginx` to confirm, because the current data is deleted
before the archive is unpacked.

## Remove

```bash
qh nginx --remove --apply           # stops it, keeps the data
qh nginx --remove --purge --apply   # and deletes volumes, secrets and .env
```

`--purge` asks for the typed name too. The tailnet node is not deregistered by
this — that is done in the Tailscale admin.

## Commands

```bash
systemctl --user status nginx
podman logs -f nginx
```

## Credits

[](https://hub.docker.com/_/nginx) — BSD-2-Clause

[Official documentation](https://nginx.org/en/docs/)
