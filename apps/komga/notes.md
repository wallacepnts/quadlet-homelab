Open `https://komga.<your-tailnet>.ts.net` and create the first account — that
is the setup. Then add a library pointing at `/books`.

### Where the comics live

```ini
Volume=${MEDIA_DATA_DIR}/comics:/books:ro,Z
```

`${MEDIA_DATA_DIR}` is the same root [media-stack](../media-stack) uses, out of
`~/.config/environment.d` — one variable, several services, which is rule 19 of
the conventions.

Mounted **read-only**: Komga indexes, reads and writes nothing where your files
are. Deleting from the interface is off as a consequence, which is the right
trade for a library you curate elsewhere.

### Memory

`JAVA_TOOL_OPTIONS=-Xmx1g` in the `.env`, because the JVM helps itself to a
quarter of the host's RAM otherwise, and scanning a large library is the moment
it does. On a box running seventy other containers, that cap is the difference
between a slow scan and a machine that starts killing things.

### Backup

Packs `config/`: the databases, the index and the thumbnails. Losing it loses
the reading progress and the metadata you corrected, not the comics.

### Remove

Neither touches the comics: they live outside the volume.
