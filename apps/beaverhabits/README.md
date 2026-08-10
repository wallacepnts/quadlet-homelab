# Beaver Habits

<img src="https://api.iconify.design/mdi/check-circle-outline.svg?color=%23888888" width="64" height="64" alt="">

**[🇧🇷 Leia em português](./README.pt-BR.md)**

Habit tracking with no goals: you mark the day and move on. The point of the
project is what it leaves out — no targets to miss, no guilt screen.

## Install

```bash
qh beaverhabits            # shows the plan
qh beaverhabits --apply
```

Open `http://<host-ip>:8015` or `https://habits.<your-tailnet>.ts.net` and
create the account. **Anyone who reaches the address can create one too** —
set `MAX_USER_COUNT=1` in the `.env` once yours exists, and restart.

<details>
<summary><b>Manual install</b></summary>

```bash
mkdir -p ~/.config/containers/systemd ~/.config/containers/env
mkdir -p ~/.config/containers/volumes/beaverhabits/data
podman unshare chown -R 1000:1000 ~/.config/containers/volumes/beaverhabits

wget -P ~/.config/containers/systemd/ \
  https://raw.githubusercontent.com/wallacepnts/quadlet-homelab/main/apps/beaverhabits/beaverhabits.container
wget -O ~/.config/containers/env/beaverhabits.env \
  https://raw.githubusercontent.com/wallacepnts/quadlet-homelab/main/apps/beaverhabits/.env.example

systemctl --user daemon-reload
systemctl --user start beaverhabits
```

</details>

## Files

```
beaverhabits.container   unit
.env.example             environment
```

Data in `~/.config/containers/volumes/beaverhabits/data`, on port **8015**.
`HABITS_STORAGE=USER_DISK` keeps the habits as JSON in that directory — no
database, so the backup is the directory.

## API

There is a REST API, which is what the Home Assistant switch, the Stream Deck
plugin and the Apple Shortcut in the project's README talk to. See the
[API guide](https://github.com/daya0576/beaverhabits/wiki/Beaver-Habit-Tracker-API-How%E2%80%90to-Guide).

## Update

```bash
qh beaverhabits --update --apply
```

Pinned to `0.10.0`. Nothing updates on its own — a new version is applied when
you run the command above.

## Backup

```bash
qh beaverhabits --backup --apply --out ~/backups
```

It stops the service, packs the data and the `.env`, and starts it again.

To restore, over the current data:

```bash
qh beaverhabits --restore ~/backups/beaverhabits-20260810-1200.tar.gz --apply
```

## Remove

```bash
qh beaverhabits --remove --apply           # stops it, keeps the data
qh beaverhabits --remove --purge --apply   # and deletes the volume and the .env
```

## Commands

```bash
systemctl --user status beaverhabits
podman logs -f beaverhabits
podman exec beaverhabits python -c "import urllib.request as u; print(u.urlopen('http://127.0.0.1:8080/health').status)"
```

## Credits

[Beaver Habit Tracker](https://github.com/daya0576/beaverhabits) by
[daya0576](https://github.com/daya0576) — BSD-3-Clause

[Official documentation](https://github.com/daya0576/beaverhabits/wiki)
