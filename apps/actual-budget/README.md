# Actual Budget

<img src="https://cdn.jsdelivr.net/gh/homarr-labs/dashboard-icons/svg/actual-budget.svg" width="64" height="64" alt="">

**[🇧🇷 Leia em português](./README.pt-BR.md)**

Fast, privacy-focused personal finance management using the envelope budgeting method.

## Install

```bash
qh actual-budget            # shows the plan
qh actual-budget --apply
```

Open `http://<host-ip>:5006` or `https://actual.<your-tailnet>.ts.net`.

<details>
<summary><b>Manual install</b></summary>

```bash
# 1. Download the unit (no need to clone the repository)
mkdir -p ~/.config/containers/systemd
wget -P ~/.config/containers/systemd/ \
  https://raw.githubusercontent.com/wallacepnts/quadlet-homelab/main/apps/actual-budget/actual.container

# 2. Data directory — a bind mount requires it to exist before the start.
#    Actual creates server-files/ and user-files/ inside it by itself.
mkdir -p ~/.config/containers/volumes/actual/data

# 3. Env — download the example (TZ is mandatory, the rest is optional — see
#    https://actualbudget.org/docs/config/)
mkdir -p ~/.config/containers/env
wget -O ~/.config/containers/env/actual.env \
  https://raw.githubusercontent.com/wallacepnts/quadlet-homelab/main/apps/actual-budget/.env.example

# 4. Start it
systemctl --user daemon-reload
systemctl --user start actual
```

</details>

## Files

```
actual.container
.env.example
```

## Update

```bash
qh actual-budget --update --apply
```

`AutoUpdate=registry` is on: the image updates on its own.

## Backup

```bash
qh actual-budget --backup --apply --out ~/backups
```

It stops the service, packs the data, the `.env` and the secrets, and starts
it again. Cold on purpose: copying a live database gives an archive that only
fails when you restore it.

To restore, over the current data:

```bash
qh actual-budget --restore ~/backups/actual-budget-20260809-1200.tar.gz --apply
```

It asks you to type `actual-budget` to confirm, because the current data is deleted
before the archive is unpacked.

## Remove

```bash
qh actual-budget --remove --apply           # stops it, keeps the data
qh actual-budget --remove --purge --apply   # and deletes volumes, secrets and .env
```

`--purge` asks for the typed name too. The tailnet node is not deregistered by
this — that is done in the Tailscale admin.

## Commands

```bash
systemctl --user status actual
podman logs -f actual
```

## Credits

[actualbudget/actual](https://github.com/actualbudget/actual) — MIT

[Official documentation](https://actualbudget.org)
