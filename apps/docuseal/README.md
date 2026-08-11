# DocuSeal

<img src="https://cdn.jsdelivr.net/gh/selfhst/icons/svg/docuseal.svg" width="64" height="64" alt="">

**[🇧🇷 Leia em português](./README.pt-BR.md)**

Signing documents, at home. You upload a PDF, mark where the signature,
initials and dates go, send a link, and the other side signs in the browser —
with the file and the audit trail staying on your disk.

It replaces handing a contract to a company so it can be signed, which is the
part of that transaction nobody thinks about: the document, the parties and the
timestamps all end up in someone else's database.

## Install

```bash
qh docuseal            # shows the plan
qh docuseal --apply
```

Open `https://docuseal.<your-tailnet>.ts.net` and create the first account —
that is the setup. Then put your address in `HOST` in the `.env` and restart,
or the links you send will point at the container's own hostname.

<details>
<summary><b>Manual install (advanced)</b></summary>

```bash
mkdir -p ~/.config/containers/systemd ~/.config/containers/env
mkdir -p ~/.config/containers/volumes/docuseal/data

wget -P ~/.config/containers/systemd/ \
  https://raw.githubusercontent.com/wallacepnts/quadlet-homelab/main/apps/docuseal/docuseal.container
wget -O ~/.config/containers/env/docuseal.env \
  https://raw.githubusercontent.com/wallacepnts/quadlet-homelab/main/apps/docuseal/.env.example

# The container runs as uid 1000, which is not yours after the mapping
podman unshare chown -R 1000:1000 ~/.config/containers/volumes/docuseal

systemctl --user daemon-reload
systemctl --user start docuseal
```

</details>

## Files

```
docuseal.container   unit
.env.example         environment
```

The volume holds `db.sqlite3` and the uploaded documents. It is the whole of
it: the templates, the signatures and the audit trail that makes a signature
worth anything.

## SQLite, not PostgreSQL

DocuSeal's own default is SQLite, and that is what this unit uses. The official
compose shows PostgreSQL in a second container — right for a company, one
container and one more database to back up for a household. Rule of this
repository: SQLite whenever the project offers it.

## The mount goes one level deeper

```ini
Volume=%h/.config/containers/volumes/docuseal/data:/data/docuseal:Z
```

Not at `/data`. The app creates `/data/docuseal/` itself on first start, and as
a non-root user on a read-only filesystem it cannot:

```
Permission denied @ rb_sysopen - /data/docuseal/docuseal.env
```

Mounting the path it wants removes the creation step. Measured both ways
before settling on it.

## HOST is what the other side clicks

`HOST` in the `.env` is what the signing links are built from. Wrong, and the
person you sent the document to gets a link that opens nothing — the failure
lands on them, not on you, which is the worst place for it.

## Hardening

The whole ladder: `ReadOnly=true`, every capability dropped, `User=1000`.
Measured with the application serving — Puma listening and the interface
answering — not just with the container up.

## Update

```bash
qh docuseal --update --apply
```

Pinned to `3.2.0`.

## Backup

```bash
qh docuseal --backup --apply --out ~/backups
```

Stops it, packs the database and the documents, starts it again. A signed
document you cannot produce later is a document you did not sign, so this one
is worth checking after the first real use.

To restore, over the current data:

```bash
qh docuseal --restore ~/backups/docuseal-20260811-1200.tar.gz --apply
```

## Remove

```bash
qh docuseal --remove --apply           # stops it, keeps the documents
qh docuseal --remove --purge --apply   # and deletes them
```

## Commands

```bash
systemctl --user status docuseal
podman logs -f docuseal
```

## Credits

[docusealco/docuseal](https://github.com/docusealco/docuseal) — AGPL-3.0.

[Official documentation](https://www.docuseal.com/docs)
