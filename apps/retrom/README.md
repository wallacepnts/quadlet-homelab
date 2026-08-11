# Retrom

<img src="https://cdn.jsdelivr.net/gh/selfhst/icons/webp/retrom.webp" width="64" height="64" alt="">

**[🇧🇷 Leia em português](./README.pt-BR.md)**

A game library for emulation: one collection on the server, played in the
browser or through Retrom's desktop client.

## Install

```bash
qh retrom            # shows the plan
qh retrom --apply
```

Put the games under `~/.config/containers/volumes/retrom/library`, in the
[folder structure Retrom
expects](https://github.com/JMBeresford/retrom/wiki/Library-Structure), then
open `http://<host-ip>:5101` or `https://retrom.<your-tailnet>.ts.net`.

**The first start takes about 90 seconds** — it downloads EmulatorJS and runs
the database migrations. `TimeoutStartSec=300` and a 180 second health start
period are there for that; a restart afterwards is quick.

<details>
<summary><b>Manual install</b></summary>

```bash
mkdir -p ~/.config/containers/systemd ~/.config/containers/env
mkdir -p ~/.config/containers/volumes/retrom/{config,data,library}

wget -P ~/.config/containers/systemd/ \
  https://raw.githubusercontent.com/wallacepnts/quadlet-homelab/main/apps/retrom/retrom.container
wget -O ~/.config/containers/env/retrom.env \
  https://raw.githubusercontent.com/wallacepnts/quadlet-homelab/main/apps/retrom/.env.example

systemctl --user daemon-reload
systemctl --user start retrom
```

</details>

## Files

```
retrom.container   unit
.env.example       environment
```

Config, data and library in `~/.config/containers/volumes/retrom/`, on port
**5101**.

The entrypoint chowns all three on every start, to whatever `PUID`/`PGID` say.
On a large library that is minutes of disk churn for an owner that did not
change — `SKIP_RECURSIVE_CHOWN=true` in the `.env` turns it off.

## Metadata

Cover art and descriptions come from IGDB or SteamGridDB, and both want an API
key. Without one the library still works, listed by filename. The keys are set
from the client, not here — see [Metadata
Providers](https://github.com/JMBeresford/retrom/wiki/Metadata-Providers).

## Update

```bash
qh retrom --update --apply
```

Pinned to `0.8.4`. Nothing updates on its own — a new version is applied when
you run the command above.

## Backup

```bash
qh retrom --backup --apply --out ~/backups
```

It stops the service, packs the three volumes and the `.env`, and starts it
again. Cold on purpose: Retrom carries an embedded PostgreSQL, and copying it
live gives an archive that only fails when you restore it. That is also why
`stop` is the mode to use if you add it to
[Zerobyte's backup hook](../zerobyte).

To restore, over the current data:

```bash
qh retrom --restore ~/backups/retrom-20260810-1200.tar.gz --apply
```

## Remove

```bash
qh retrom --remove --apply           # stops it, keeps the data
qh retrom --remove --purge --apply   # and deletes the volumes and the .env
```

`--purge` deletes the library too — the games are in a volume like everything
else.

## Commands

```bash
systemctl --user status retrom
podman logs -f retrom
podman exec retrom curl -fsS -o /dev/null http://127.0.0.1:5101/
```

## Credits

[Retrom](https://github.com/JMBeresford/retrom) by
[JMBeresford](https://github.com/JMBeresford) — GPL-3.0

[Official documentation](https://github.com/JMBeresford/retrom/wiki)
