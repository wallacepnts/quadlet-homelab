# Invio — Podman Quadlet (rootless)

**[🇧🇷 Leia em português](./README.pt-BR.md)**

An [Invio](https://github.com/kittendevv/Invio) (invoicing and invoice
tracking) deploy via Podman Quadlet, using the official
`ghcr.io/kittendevv/invio` image.

*"Self-hosted invoicing without the bloat"* — cliente, item, fatura, PDF.
Sem contabilidade, sem CRM, sem assinatura mensal.

## Architecture

A single container (SvelteKit + supervisord), with **SQLite** in `/app/data`
([rule 22](../../docs/conventions.md)).

Hardening measured: `DropCapability=ALL` passes. **`ReadOnly` was refused** —
the image's supervisord writes `/app/supervisord.log`. Two workarounds were
tried and neither works: `Tmpfs=/app` masks the whole application, and binding
a file that does not exist makes Podman create a directory in its place. So it
goes without `ReadOnly`.

## `ORIGIN` is not decoration

SvelteKit validates the origin on every `POST` as CSRF protection. If `ORIGIN`
is not **exactly** the URL you reach it through, the app opens normally and
then refuses every form — the login included, with no helpful message. Replace
`<your-tailnet>` in the `.env` before starting.

## Files

```
invio.container   # main unit
.env.example      # the admin user, ORIGIN and the database path
install.ini       # the secret recipes
```

## Installation

```bash
python3 install.py invio            # dry-run: shows what it will do
python3 install.py invio --apply
```

For the local network only, `--access local`; on the tailnet and the LAN,
`--access both`. Adding `--href-local` points the dashboard link at the LAN.
The script creates the directories, writes the `.env`, generates the secrets,
fixes the volumes' ownership, starts the service and prints the address at the
end — see [Installing and operating](../../docs/installing.md).

Open `http://<host-ip>:8106` (or through [tsdproxy](../tsdproxy/) at
`https://invio.<your-tailnet>.ts.net`). The username is the `.env`'s
`ADMIN_USER`; the password is in
`~/.config/containers/secrets/invio/admin-pass.txt`.

<details>
<summary><b>Manual installation</b> (advanced) — the same steps, one at a time</summary>


```bash
# 1. Download the unit (no need to clone the repository)
mkdir -p ~/.config/containers/systemd
wget -P ~/.config/containers/systemd/ \
  https://raw.githubusercontent.com/wallacepnts/quadlet-homelab/main/apps/invio/invio.container

# 2. Data directory
mkdir -p ~/.config/containers/volumes/invio/data

# 3. Variables — replace <your-tailnet> in ORIGIN
mkdir -p ~/.config/containers/env
wget -O ~/.config/containers/env/invio.env \
  https://raw.githubusercontent.com/wallacepnts/quadlet-homelab/main/apps/invio/.env.example
${EDITOR:-vi} ~/.config/containers/env/invio.env

# 4. Secrets — the admin password and the key that signs the session. They
#    deliberately do not go in the .env ([rule 2](../../docs/conventions.md)).
mkdir -p ~/.config/containers/secrets/invio
python3 -c "import secrets;print(secrets.token_urlsafe(18),end='')" \
  > ~/.config/containers/secrets/invio/admin-pass.txt
python3 -c "import secrets;print(secrets.token_hex(32),end='')" \
  > ~/.config/containers/secrets/invio/jwt-secret.txt
chmod 600 ~/.config/containers/secrets/invio/*.txt
podman secret create invio-admin-pass ~/.config/containers/secrets/invio/admin-pass.txt
podman secret create invio-jwt-secret ~/.config/containers/secrets/invio/jwt-secret.txt

# 5. Start it
systemctl --user daemon-reload
systemctl --user start invio
```

Open `http://<host-ip>:8106` (or through [tsdproxy](../tsdproxy/) at
`https://invio.<your-tailnet>.ts.net`). The username is the `.env`'s
`ADMIN_USER`; the password is in
`~/.config/containers/secrets/invio/admin-pass.txt`.

Com o [`install.py`](../../install.py) os passos 2 a 5 saem de uma vez:

```bash
python3 install.py invio --apply
```

</details>

## Auto-update

No `AutoUpdate=` — an explicit tag (`v2.1.1`), bumped by hand
(rule 9 of the [conventions](../../docs/conventions.md)). An issued invoice is a tax record: back up before bumping the version. The
repository also publishes `main`, `latest` and PR tags (`pr-123`), hence the
`wud.tag.include` restricting it to `vX.Y.Z`.

## Backup & recovery

```bash
python3 install.py invio --backup --apply --out ~/backups
```

It takes the SQLite database, the secrets and the `.env` — enough to
restore. Changing `invio-jwt-secret` logs everyone out, so it has to come
along.

## Useful commands

```bash
systemctl --user status invio
podman logs -f invio
cat ~/.config/containers/secrets/invio/admin-pass.txt
```

## Credits

Quadlet deploy based on [Invio](https://github.com/kittendevv/Invio) de
[kittendevv](https://github.com/kittendevv) (Unlicense).
