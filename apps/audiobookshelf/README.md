# Audiobookshelf

<img src="https://cdn.jsdelivr.net/gh/homarr-labs/dashboard-icons/svg/audiobookshelf.svg" width="64" height="64" alt="">

**[🇧🇷 Leia em português](./README.pt-BR.md)**

An audiobook and podcast server, with progress synced across devices.

## Install

```bash
qh audiobookshelf            # shows the plan
qh audiobookshelf --apply
```

Open `http://<host-ip>:13378` or `https://audiobookshelf.<your-tailnet>.ts.net`.

<details>
<summary><b>Manual install</b></summary>

```bash
# 1. Download the units (no need to clone the repository)
mkdir -p ~/.config/containers/systemd
wget -P ~/.config/containers/systemd/ \
  https://raw.githubusercontent.com/wallacepnts/quadlet-homelab/main/apps/audiobookshelf/audiobookshelf.container

# 2. Data directories — a bind mount requires them to exist before the start
mkdir -p ~/.config/containers/volumes/audiobookshelf/{config,metadata,audiobooks,podcasts}

# 3. Non-secret env — download the example, adjust TZ if needed
mkdir -p ~/.config/containers/env
wget -O ~/.config/containers/env/audiobookshelf.env \
  https://raw.githubusercontent.com/wallacepnts/quadlet-homelab/main/apps/audiobookshelf/.env.example

# 4. Start it
systemctl --user daemon-reload
systemctl --user start audiobookshelf
```

</details>

## Files

```
audiobookshelf.container
.env.example
```

## Update

```bash
qh audiobookshelf --update --apply
```

Pinned to `2.36.0`. Nothing updates on its own — a new version is applied
when you run the command above.

## Backup

```bash
qh audiobookshelf --backup --apply --out ~/backups
```

It stops the service, packs the data, the `.env` and the secrets, and starts
it again. Cold on purpose: copying a live database gives an archive that only
fails when you restore it.

To restore, over the current data:

```bash
qh audiobookshelf --restore ~/backups/audiobookshelf-20260809-1200.tar.gz --apply
```

It asks you to type `audiobookshelf` to confirm, because the current data is deleted
before the archive is unpacked.

## Remove

```bash
qh audiobookshelf --remove --apply           # stops it, keeps the data
qh audiobookshelf --remove --purge --apply   # and deletes volumes, secrets and .env
```

`--purge` asks for the typed name too. The tailnet node is not deregistered by
this — that is done in the Tailscale admin.

## Commands

```bash
systemctl --user status audiobookshelf
podman logs -f audiobookshelf
```

## Credits

[advplyr/audiobookshelf](https://github.com/advplyr/audiobookshelf) — GPL-3.0

[Official documentation](https://audiobookshelf.org)
