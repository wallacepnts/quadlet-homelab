Zerobyte calls a **backup hook** before and after each job, so Restic never copies a database mid-write. Per unit there are two modes: `sqlite` (online copy into `<volume>/.dbbackup/`, no downtime) and `stop` (stops the unit during the copy, the default). The hook runs on the host, because stopping a unit is `systemctl --user`.

```bash
# which units it may act on, and how (anything unlisted gets a 404)
systemctl --user edit --full zerobyte-backup-hook.service
#    Environment=ZEROBYTE_HOOK_UNITS=vaultwarden:sqlite,any-sync-bundle:stop

mkdir -p ~/.config/zerobyte-backup-hook
openssl rand -hex 32 > ~/.config/zerobyte-backup-hook/token
chmod 600 ~/.config/zerobyte-backup-hook/token

systemctl --user enable --now zerobyte-backup-hook.service
curl -s http://127.0.0.1:8766/healthz     # {"ok": true}
```

Each job then carries `http://<host-ip>:8766/hooks/<unit>/pre-backup` and `.../post-backup`, which `qh --zerobyte` writes for you and checks against the allowlist: a unit missing there is a backup that fails at 03:00 with a 404 nobody watches. `ZEROBYTE_HOOK_PORT` moves the port (`WEBHOOK_ALLOWED_ORIGINS` must agree).
