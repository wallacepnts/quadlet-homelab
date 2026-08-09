# Stirling-PDF

<img src="https://cdn.jsdelivr.net/gh/homarr-labs/dashboard-icons/svg/stirling-pdf.svg" width="64" height="64" alt="">

**[🇧🇷 Leia em português](./README.pt-BR.md)**

Local PDF manipulation — merge, split, convert, OCR and sign, in place of the "online PDF" sites.

## Install

```bash
qh stirling-pdf            # shows the plan
qh stirling-pdf --apply
```

Open `http://<host-ip>:8095` or `https://stirling-pdf.<your-tailnet>.ts.net`.

<details>
<summary><b>Manual install</b></summary>

```bash
# 1. Download the units (no need to clone the repository)
mkdir -p ~/.config/containers/systemd
wget -P ~/.config/containers/systemd/ \
  https://raw.githubusercontent.com/wallacepnts/quadlet-homelab/main/apps/stirling-pdf/stirling-pdf.container

# 2. Data directories — a bind mount requires them to exist before the start
mkdir -p ~/.config/containers/volumes/stirling-pdf/{config,tessdata,logs}

# 3. Environment variables
mkdir -p ~/.config/containers/env
wget -O ~/.config/containers/env/stirling-pdf.env \
  https://raw.githubusercontent.com/wallacepnts/quadlet-homelab/main/apps/stirling-pdf/.env.example

# 4. Start it
systemctl --user daemon-reload
systemctl --user start stirling-pdf
```

</details>

## Files

```
stirling-pdf.container
.env.example
install.ini
```

## Update

```bash
qh stirling-pdf --update --apply
```

Pinned to `2.14.3`. Nothing updates on its own — a new version is applied
when you run the command above.

## Backup

```bash
qh stirling-pdf --backup --apply --out ~/backups
```

It stops the service, packs the data, the `.env` and the secrets, and starts
it again. Cold on purpose: copying a live database gives an archive that only
fails when you restore it.

To restore, over the current data:

```bash
qh stirling-pdf --restore ~/backups/stirling-pdf-20260809-1200.tar.gz --apply
```

It asks you to type `stirling-pdf` to confirm, because the current data is deleted
before the archive is unpacked.

## Remove

```bash
qh stirling-pdf --remove --apply           # stops it, keeps the data
qh stirling-pdf --remove --purge --apply   # and deletes volumes, secrets and .env
```

`--purge` asks for the typed name too. The tailnet node is not deregistered by
this — that is done in the Tailscale admin.

## Commands

```bash
systemctl --user status stirling-pdf
podman logs -f stirling-pdf
```

## Credits

[Stirling-Tools/Stirling-PDF](https://github.com/Stirling-Tools/Stirling-PDF) — MIT

[Official documentation](https://stirling.com)
