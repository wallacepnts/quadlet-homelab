### Update

Each shell carries its own tag — the table above lists them. Arch is the
exception, pinned by digest because its only tag is `latest`.

### Backup

It stops the four, packs the four `/work` directories and starts them again.
There is no `.env` and no secret here to pack. A single shell can be backed up
on its own — `qh toolbx-fedora --backup --apply` — because none of them shares
a directory with the others.

### Remove

`--purge` asks for the typed name too, and deletes the `/work` of all four.
There is no tailnet node to deregister: none of these is published.
