# Vaultwarden — Podman Quadlet (rootless)

**[🇧🇷 Leia em português](./README.pt-BR.md)**

Deploy do [Vaultwarden](https://github.com/dani-garcia/vaultwarden)
(an alternative Bitwarden server implementation, in Rust) via Podman Quadlet.
A self-hosted password vault — compatible with Bitwarden's official apps (just
change the "server URL" in the app's settings).

## Architecture

A single container, with embedded SQLite (`/data/db.sqlite3`) — no separate
database service, unlike [immich](../immich/). It exposes `80`
internamente (mapeado pra `8082` no host).

## Files

```
vaultwarden.container   # main unit
```

## Prerequisites

- Rootless Podman with systemd `--user` working
- `python3` with the `argon2-cffi` package (`pip3 install --user
  argon2-cffi`) — only to generate the `ADMIN_TOKEN` with a secure hash during
  installation

## Installation

```bash
python3 install.py vaultwarden            # dry-run: shows what it will do
python3 install.py vaultwarden --apply
```

For the local network only, `--access local`; on the tailnet and the LAN,
`--access both`. Adding `--href-local` points the dashboard link at the LAN.
The script creates the directories, writes the `.env`, generates the secrets,
fixes the volumes' ownership, starts the service and prints the address at the
end — see [Installing and operating](../../docs/installing.md).

Reach it through [tsdproxy](../tsdproxy/) (tailnet) at
`https://vaultwarden.<your-tailnet>.ts.net`, or locally at
`http://localhost:8082`. Create the first account, then follow the Security
section below.

<details>
<summary><b>Manual installation</b> (advanced) — the same steps, one at a time</summary>


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

Reach it through [tsdproxy](../tsdproxy/) (tailnet) at
`https://vaultwarden.<your-tailnet>.ts.net`, or locally at
`http://localhost:8082`. Create the first account, then follow the Security
section below.

**The value printed as "Admin token"** (the raw string, not the hash) is the
`/admin` panel's password — keep it somewhere safe (in Vaultwarden itself once
it exists, ironically, or in another manager). What is saved in
`admin-token-hash.txt` is only the Argon2id hash — the original password
cannot be recovered from it.

</details>

## Security

- **Desabilitar cadastro depois da primeira conta**: `SIGNUPS_ALLOWED=false`
  em `vaultwarden.env`, `systemctl --user restart vaultwarden`.
  Without that, anyone who reaches the URL can create an account of their
  own.
- **`ADMIN_TOKEN` as a hash, not plain text** — already this setup's
  default
  (ver passo 3). Um `ADMIN_TOKEN` em texto puro no arquivo de secret, se
  leaks, it gives full access to the admin panel (every user, organisation
  and server setting). The Argon2id hash is not reversible.
- **Never publish the `/admin` panel outside the tailnet** — only the client
  app (ordinary login) needs to be reachable from outside; the admin panel is
  yours alone.

## Auto-update

No `AutoUpdate=` — an explicit tag (`1.37.1-alpine`), bumped by hand
([rule 9](../../docs/conventions.md)). The image has `wget`/`curl` (Alpine),
so it could be turned on
auto-update com rollback de verdade se decidir habilitar — mas pra um
a password vault, a manually reviewed update is the recommended default
aqui.

## Backup & recovery

Everything lives in `volumes/vaultwarden/data/` (SQLite plus attachments
plus cached icons). It is the most sensitive data in this entire repository —
stop it before
copiar:

```bash
systemctl --user stop vaultwarden
tar -czf vaultwarden-backup-$(date +%Y%m%d-%H%M%S).tar.gz \
  -C ~/.config/containers/volumes vaultwarden
systemctl --user start vaultwarden
```

`admin-token-raw.txt` (the admin panel's password) needs a separate backup
too — there is no recovering it if lost, only resetting by creating a new
`ADMIN_TOKEN`.

## Useful commands

```bash
systemctl --user status vaultwarden
podman logs -f vaultwarden
curl http://127.0.0.1:8082/alive
```

## Credits

Quadlet deploy based on [Vaultwarden](https://github.com/dani-garcia/vaultwarden),
by [Daniel García (@dani-garcia)](https://github.com/dani-garcia).
Original licence: AGPL-3.0.
