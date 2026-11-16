Open `https://docuseal.<your-tailnet>.ts.net` and create the first account —
that is the setup. Then put your address in `HOST` in the `.env` and restart,
or the links you send will point at the container's own hostname.

### SQLite, not PostgreSQL

DocuSeal's own default is SQLite, and that is what this unit uses. The official
compose shows PostgreSQL in a second container — right for a company, one
container and one more database to back up for a household. Rule of this
repository: SQLite whenever the project offers it.

### The mount goes one level deeper

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

### HOST is what the other side clicks

`HOST` in the `.env` is what the signing links are built from. Wrong, and the
person you sent the document to gets a link that opens nothing — the failure
lands on them, not on you, which is the worst place for it.

### Backup

Stops it, packs the database and the documents, starts it again. A signed
document you cannot produce later is a document you did not sign, so this one
is worth checking after the first real use.
