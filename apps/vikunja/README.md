# Vikunja

<img src="https://cdn.jsdelivr.net/gh/selfhst/icons/svg/vikunja.svg" width="64" height="64" alt="">

**[🇧🇷 Leia em português](./README.pt-BR.md)**

Tasks that belong to a project and have a date: the same list shown as a list,
a kanban board, a table or a gantt chart, with subtasks, labels, attachments
and reminders.

Next to [donetick](../donetick), the split is what each is for. Donetick is for
the chores that come back — bins on Tuesday, filter every six months. This is
for the work that ends: a move, a renovation, a trip.

## Install

```bash
qh vikunja            # shows the plan
qh vikunja --apply
```

Open `https://vikunja.<your-tailnet>.ts.net` and register. Then set
`VIKUNJA_SERVICE_ENABLEREGISTRATION=false` in the `.env` and restart, or anyone
who reaches your tailnet can create an account.

<details>
<summary><b>Manual install (advanced)</b></summary>

```bash
mkdir -p ~/.config/containers/systemd ~/.config/containers/env
mkdir -p ~/.config/containers/volumes/vikunja/{db,files}

wget -P ~/.config/containers/systemd/ \
  https://raw.githubusercontent.com/wallacepnts/quadlet-homelab/main/apps/vikunja/vikunja.container
wget -O ~/.config/containers/env/vikunja.env \
  https://raw.githubusercontent.com/wallacepnts/quadlet-homelab/main/apps/vikunja/.env.example
# edit ~/.config/containers/env/vikunja.env: VIKUNJA_SERVICE_PUBLICURL

# The container runs as uid 1000, which is not yours after the mapping
podman unshare chown -R 1000:1000 ~/.config/containers/volumes/vikunja

systemctl --user daemon-reload
systemctl --user start vikunja
```

</details>

## Files

```
vikunja.container   unit
.env.example        environment
```

Two volumes on purpose: `db/` for `vikunja.db` and `files/` for the
attachments. Split, a backup can tell a corrupted database from a missing file,
and restoring one does not overwrite the other.

## PUBLICURL is not decoration

`VIKUNJA_SERVICE_PUBLICURL` is the address the frontend calls the API on.
Wrong, and the symptom misleads: the interface loads, looks right, and every
request fails. It is also what invitation and reminder links carry.

## Hardening

The whole ladder: `ReadOnly=true`, every capability dropped, `User=1000` — the
uid the image itself declares. Measured with the migrations run and the API
answering, not just with the container up.

The health check is the binary's own subcommand, in exec form:

```ini
HealthCmd=["CMD", "/app/vikunja/vikunja", "healthcheck"]
```

The image is distroless — `/app/vikunja/vikunja` and a CA bundle are the whole
of it — so `CMD-SHELL` would have no shell to run in.

## Update

```bash
qh vikunja --update --apply
```

Pinned to `2.5.0`. It migrates the database on start, which is why the release
notes are worth a look before a major bump.

## Backup

```bash
qh vikunja --backup --apply --out ~/backups
```

Stops it, packs both volumes and the `.env`, starts it again.

To restore, over the current data:

```bash
qh vikunja --restore ~/backups/vikunja-20260811-1200.tar.gz --apply
```

## Remove

```bash
qh vikunja --remove --apply           # stops it, keeps the tasks
qh vikunja --remove --purge --apply   # and deletes them
```

## Commands

```bash
systemctl --user status vikunja
podman logs -f vikunja

# a user, without the interface
podman exec vikunja /app/vikunja/vikunja user list
```

## Credits

[go-vikunja/vikunja](https://github.com/go-vikunja/vikunja) — AGPL-3.0.

[Official documentation](https://vikunja.io/docs/)
