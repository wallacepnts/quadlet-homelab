# Faved

<img src="https://api.iconify.design/mdi/bookmark-multiple.svg?color=%23888888" width="64" height="64" alt="">

**[🇧🇷 Leia em português](./README.pt-BR.md)**

A bookmark manager with nested tags. PHP, SQLite and Apache — no queue, no
search engine, no headless browser: a shelf for links, and fast because of it.

Next to [karakeep](../karakeep), which also holds bookmarks, the difference is
what each one is for. Karakeep archives the page, extracts text and runs a
model over it, and pays for that in three containers. Faved keeps the link and
your tags, in one.

## Install

```bash
qh faved            # shows the plan
qh faved --apply
```

Open `https://faved.<your-tailnet>.ts.net` and create the first account —
that is also the setup step, since the SQLite database is written on
registration.

<details>
<summary><b>Manual install (advanced)</b></summary>

```bash
mkdir -p ~/.config/containers/systemd
mkdir -p ~/.config/containers/volumes/faved/storage

wget -P ~/.config/containers/systemd/ \
  https://raw.githubusercontent.com/wallacepnts/quadlet-homelab/main/apps/faved/faved.container

# Apache drops to www-data (uid 33), which is not you after the mapping
podman unshare chown -R 33:33 ~/.config/containers/volumes/faved

systemctl --user daemon-reload
systemctl --user start faved
```

</details>

## Files

```
faved.container   unit
```

No `.env`: everything the container needs is in the unit, and the rest is
configured through the interface. The database is the single file under
`~/.config/containers/volumes/faved/storage`.

## Hardening

The whole ladder, measured: `ReadOnly=true` with tmpfs on `/tmp`, `/var/run`
and `/var/log/apache2`, every capability dropped except `NET_BIND_SERVICE`, and
`User=33`.

The capability is there because Apache listens on port 80 **inside** the
container, which is privileged. The `User=33` is www-data, the user the image
itself drops to — without it the volume belongs to root and the app answers
with an empty page after silently failing to write: `touch: cannot touch
'/var/www/html/storage/...': Permission denied`. `qh` does the `podman unshare
chown` for you because the unit declares `User=`.

## Update

```bash
qh faved --update --apply
```

Pinned to `2.10.0`.

## Backup

```bash
qh faved --backup --apply --out ~/backups
```

Stops it, packs the storage folder, starts it again. That folder is the whole
of it — the links, the tags and the accounts.

To restore, over the current data:

```bash
qh faved --restore ~/backups/faved-20260811-1200.tar.gz --apply
```

## Remove

```bash
qh faved --remove --apply           # stops it, keeps the bookmarks
qh faved --remove --purge --apply   # and deletes the storage folder
```

## Commands

```bash
systemctl --user status faved
podman logs -f faved
```

## Credits

[denho/faved](https://github.com/denho/faved) — MIT.

[Official documentation](https://faved.to/docs/)
