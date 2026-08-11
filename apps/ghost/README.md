# Ghost

<img src="https://cdn.jsdelivr.net/gh/selfhst/icons/webp/ghost.webp" width="64" height="64" alt="">

**[🇧🇷 Leia em português](./README.pt-BR.md)**

A self-hosted blog/newsletter.

## Install

```bash
qh ghost            # shows the plan
qh ghost --apply
```

Open `http://<host-ip>:2368` or `https://ghost.<your-tailnet>.ts.net`.

<details>
<summary><b>Manual install</b></summary>

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

</details>

## Files

```
ghost.container
.env.example
install.ini
```

## Update

```bash
qh ghost --update --apply
```

Pinned to `6.56.0-alpine`. Nothing updates on its own — a new version is applied
when you run the command above.

## Backup

```bash
qh ghost --backup --apply --out ~/backups
```

It stops the service, packs the data, the `.env` and the secrets, and starts
it again. Cold on purpose: copying a live database gives an archive that only
fails when you restore it.

To restore, over the current data:

```bash
qh ghost --restore ~/backups/ghost-20260809-1200.tar.gz --apply
```

It asks you to type `ghost` to confirm, because the current data is deleted
before the archive is unpacked.

## Remove

```bash
qh ghost --remove --apply           # stops it, keeps the data
qh ghost --remove --purge --apply   # and deletes volumes, secrets and .env
```

`--purge` asks for the typed name too. The tailnet node is not deregistered by
this — that is done in the Tailscale admin.

## Commands

```bash
systemctl --user status ghost
podman logs -f ghost
```

## Credits

[TryGhost/Ghost](https://github.com/TryGhost/Ghost) — MIT

[Official documentation](https://ghost.org)
