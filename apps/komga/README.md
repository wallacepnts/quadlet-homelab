# Komga

<img src="https://cdn.jsdelivr.net/gh/selfhst/icons/svg/komga.svg" width="64" height="64" alt="">

**[🇧🇷 Leia em português](./README.pt-BR.md)**

A comics and manga library: CBZ, CBR, PDF and EPUB, read in the browser or
through any OPDS reader. It keeps the page you stopped on, per user, so a
volume started on the tablet carries on from the phone.

Next to [calibre-web-automated](../calibre-web-automated) and
[audiobookshelf](../audiobookshelf), the split is by format: books there,
audio there, page-by-page reading here.

## Install

```bash
qh komga            # shows the plan
qh komga --apply
```

Open `https://komga.<your-tailnet>.ts.net` and create the first account — that
is the setup. Then add a library pointing at `/books`.

<details>
<summary><b>Manual install (advanced)</b></summary>

```bash
mkdir -p ~/.config/containers/systemd ~/.config/containers/env
mkdir -p ~/.config/containers/volumes/komga/config
mkdir -p "$MEDIA_DATA_DIR/comics"

wget -P ~/.config/containers/systemd/ \
  https://raw.githubusercontent.com/wallacepnts/quadlet-homelab/main/apps/komga/komga.container
wget -O ~/.config/containers/env/komga.env \
  https://raw.githubusercontent.com/wallacepnts/quadlet-homelab/main/apps/komga/.env.example

# The container runs as uid 1000, which is not yours after the mapping
podman unshare chown -R 1000:1000 ~/.config/containers/volumes/komga

systemctl --user daemon-reload
systemctl --user start komga
```

</details>

## Files

```
komga.container   unit
.env.example      environment
```

`config/` holds two SQLite databases — the library and the task queue — plus
the Lucene search index and the thumbnails. That folder is the backup; the
comics themselves are yours already.

## Where the comics live

```ini
Volume=${MEDIA_DATA_DIR}/comics:/books:ro,Z
```

`${MEDIA_DATA_DIR}` is the same root [media-stack](../media-stack) uses, out of
`~/.config/environment.d` — one variable, several services, which is rule 19 of
the conventions.

Mounted **read-only**: Komga indexes, reads and writes nothing where your files
are. Deleting from the interface is off as a consequence, which is the right
trade for a library you curate elsewhere.

## Memory

`JAVA_TOOL_OPTIONS=-Xmx1g` in the `.env`, because the JVM helps itself to a
quarter of the host's RAM otherwise, and scanning a large library is the moment
it does. On a box running seventy other containers, that cap is the difference
between a slow scan and a machine that starts killing things.

## Hardening

The whole ladder: `ReadOnly=true`, every capability dropped, `User=1000`.
Measured with the application actually up — `Started ApplicationKt` in the log
and `/actuator/health` answering 200 — not just with the container running.

`HealthStartPeriod=90s` is not padding: a JVM takes about eleven seconds to
boot here before the first scan, and a cold library takes longer.

## Update

```bash
qh komga --update --apply
```

Pinned to `1.26.1`.

## Backup

```bash
qh komga --backup --apply --out ~/backups
```

Packs `config/`: the databases, the index and the thumbnails. Losing it loses
the reading progress and the metadata you corrected, not the comics.

To restore, over the current data:

```bash
qh komga --restore ~/backups/komga-20260811-1200.tar.gz --apply
```

## Remove

```bash
qh komga --remove --apply           # stops it, keeps the library data
qh komga --remove --purge --apply   # and deletes progress and thumbnails
```

Neither touches the comics: they live outside the volume.

## Commands

```bash
systemctl --user status komga
podman logs -f komga

du -sh ~/.config/containers/volumes/komga/config
```

## Credits

[gotson/komga](https://github.com/gotson/komga) — MIT.

[Official documentation](https://komga.org/)
