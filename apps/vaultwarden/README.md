# Vaultwarden

<img src="https://cdn.jsdelivr.net/gh/homarr-labs/dashboard-icons/svg/vaultwarden.svg" width="64" height="64" alt="">

**[🇧🇷 Leia em português](./README.pt-BR.md)**

A password vault compatible with Bitwarden's protocol, light enough to run anywhere.

## Install

```bash
qh vaultwarden            # shows the plan
qh vaultwarden --apply
```

Open `http://<host-ip>:8082` or `https://vaultwarden.<your-tailnet>.ts.net`.

<details>
<summary><b>Manual install</b></summary>

```bash
# 1. Download the unit (no need to clone the repository)
mkdir -p ~/.config/containers/systemd
wget -P ~/.config/containers/systemd/ \
  https://raw.githubusercontent.com/wallacepnts/quadlet-homelab/main/apps/vaultwarden/vaultwarden.container

# 2. Data directory — a bind mount requires it to exist before the start
mkdir -p ~/.config/containers/volumes/vaultwarden/data

# 3. ADMIN_TOKEN as an Argon2id hash (not plain text) — the form the
#    project itself recommends. The official `vaultwarden hash` command
#    requires an interactive TTY (it cannot be scripted), so we generate the
#    equivalent hash in Python with the SAME parameters as the "bitwarden"
#    preset the binary uses (m=65540, t=3, p=4).
mkdir -p ~/.config/containers/secrets/vaultwarden
python3 - <<'PYEOF'
from argon2 import PasswordHasher
from argon2.low_level import Type
import secrets
import os

secrets_dir = os.path.expanduser("~/.config/containers/secrets/vaultwarden")
ph = PasswordHasher(time_cost=3, memory_cost=65540, parallelism=4, hash_len=32, salt_len=16, type=Type.ID)
raw_secret = secrets.token_urlsafe(32)
phc = ph.hash(raw_secret)

with open(f"{secrets_dir}/admin-token-raw.txt", "w") as f:
    f.write(raw_secret)
with open(f"{secrets_dir}/admin-token-hash.txt", "w") as f:
    f.write(phc)

print("Admin token (keep it somewhere safe — it is the /admin panel's PASSWORD):")
print(raw_secret)
PYEOF
chmod 600 ~/.config/containers/secrets/vaultwarden/*.txt

podman secret create vaultwarden-admin-token ~/.config/containers/secrets/vaultwarden/admin-token-hash.txt

# 4. Non-secret env — download the example
mkdir -p ~/.config/containers/env
wget -O ~/.config/containers/env/vaultwarden.env \
  https://raw.githubusercontent.com/wallacepnts/quadlet-homelab/main/apps/vaultwarden/.env.example
# edit ~/.config/containers/env/vaultwarden.env: DOMAIN (and remember to
# switch SIGNUPS_ALLOWED to "false" once the first account exists — see the
# Security section below)

# 5. Start it
systemctl --user daemon-reload
systemctl --user start vaultwarden
```

</details>

## Files

```
vaultwarden.container
.env.example
install.ini
```

## Update

```bash
qh vaultwarden --update --apply
```

Pinned to `1.37.1-alpine`. Nothing updates on its own — a new version is applied
when you run the command above.

## Backup

```bash
qh vaultwarden --backup --apply --out ~/backups
```

It stops the service, packs the data, the `.env` and the secrets, and starts
it again. Cold on purpose: copying a live database gives an archive that only
fails when you restore it.

To restore, over the current data:

```bash
qh vaultwarden --restore ~/backups/vaultwarden-20260809-1200.tar.gz --apply
```

It asks you to type `vaultwarden` to confirm, because the current data is deleted
before the archive is unpacked.

## Remove

```bash
qh vaultwarden --remove --apply           # stops it, keeps the data
qh vaultwarden --remove --purge --apply   # and deletes volumes, secrets and .env
```

`--purge` asks for the typed name too. The tailnet node is not deregistered by
this — that is done in the Tailscale admin.

## Commands

```bash
systemctl --user status vaultwarden
podman logs -f vaultwarden
```

## Credits

[dani-garcia/vaultwarden](https://github.com/dani-garcia/vaultwarden) — AGPL-3.0.

[Official documentation](https://github.com/dani-garcia/vaultwarden/wiki)
