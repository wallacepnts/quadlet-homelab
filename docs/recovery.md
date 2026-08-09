# Recovery and migration

## The machine died

Install first, restore afterwards. `--restore` does not create the unit, the
directories or the env — it only puts the data back over an install that is
already there.

```bash
# 1. Host: rootless Podman, systemd --user, and the folders
curl -fsSL https://raw.githubusercontent.com/wallacepnts/quadlet-homelab/main/bootstrap.sh | bash

# 2. If you use a tailnet, this one comes before the rest
qh tsdproxy --apply

# 3. Service by service
qh <app> --apply
qh <app> --restore ~/backups/<app>-....tar.gz --apply

# 4. Check
systemctl --user is-active <app>
podman ps --filter "name=<app>"
```

The restore asks for the typed service name, because it deletes the current
data before unpacking.

## What the backup does not carry

- **The images.** The first start pulls them again, and that is the slow part.
- **The tailnet identity.** A new node with the same name and a different
  address; the old one is removed in the Tailscale admin.
- **Addresses recorded inside the data** — `DOMAIN`, `ALLOWED_HOSTS` and the
  like. If the host's name changed, these need reviewing by hand.

## Migrating from another server

```bash
# on the old server
qh <app> --backup --apply --out ~/backups

# transfer
scp ~/backups/<app>-....tar.gz newhost:~/backups/

# on the new one
qh <app> --apply
qh <app> --restore ~/backups/<app>-....tar.gz --apply
```

Before calling it migrated: the service answers on its port, the data is there,
and any address the app wrote into its own database points at the new host.
