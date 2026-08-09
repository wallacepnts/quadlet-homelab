# FreshRSS

<img src="https://cdn.jsdelivr.net/gh/homarr-labs/dashboard-icons/svg/freshrss.svg" width="64" height="64" alt="">

**[🇧🇷 Leia em português](./README.pt-BR.md)**

A self-hosted RSS/Atom feed aggregator, with a compatible API for mobile apps.

## Install

```bash
qh freshrss            # shows the plan
qh freshrss --apply
```

Open `http://<host-ip>:8104` or `https://freshrss.<your-tailnet>.ts.net`.

<details>
<summary><b>Manual install</b></summary>

```bash
# 1. Download the units (no need to clone the repository)
mkdir -p ~/.config/containers/systemd
wget -P ~/.config/containers/systemd/ \
  https://raw.githubusercontent.com/wallacepnts/quadlet-homelab/main/apps/freshrss/freshrss.container

# 2. Data directory — a bind mount requires it to exist before the start
mkdir -p ~/.config/containers/volumes/freshrss/data

# 3. Non-secret env — download the example, adjust TZ if needed
mkdir -p ~/.config/containers/env
wget -O ~/.config/containers/env/freshrss.env \
  https://raw.githubusercontent.com/wallacepnts/quadlet-homelab/main/apps/freshrss/.env.example

# 4. Start it
systemctl --user daemon-reload
systemctl --user start freshrss
```

</details>

## Files

```
freshrss.container
.env.example
```

## Update

```bash
qh freshrss --update --apply
```

Pinned to `1.29.1-alpine`. Nothing updates on its own — a new version is applied
when you run the command above.

## Backup

```bash
qh freshrss --backup --apply --out ~/backups
```

It stops the service, packs the data, the `.env` and the secrets, and starts
it again. Cold on purpose: copying a live database gives an archive that only
fails when you restore it.

To restore, over the current data:

```bash
qh freshrss --restore ~/backups/freshrss-20260809-1200.tar.gz --apply
```

It asks you to type `freshrss` to confirm, because the current data is deleted
before the archive is unpacked.

## Remove

```bash
qh freshrss --remove --apply           # stops it, keeps the data
qh freshrss --remove --purge --apply   # and deletes volumes, secrets and .env
```

`--purge` asks for the typed name too. The tailnet node is not deregistered by
this — that is done in the Tailscale admin.

## Commands

```bash
systemctl --user status freshrss
podman logs -f freshrss
```

## Credits

[FreshRSS/FreshRSS](https://github.com/FreshRSS/FreshRSS) — AGPL-3.0

[Official documentation](https://freshrss.org)
