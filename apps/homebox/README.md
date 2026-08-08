# HomeBox — Podman Quadlet (rootless)

**[🇧🇷 Leia em português](./README.pt-BR.md)**

A [HomeBox](https://github.com/sysadminsmedia/homebox) (home inventory)
deploy via Podman Quadlet, using the official
`ghcr.io/sysadminsmedia/homebox`.

A catalogue of what you own: where it is, what it cost, when you bought it,
the receipt
fiscal e manual anexados, garantia com data de vencimento. Complementa o
[LubeLogger](../lubelogger/), which does the same for vehicles.

## Architecture

A single container, Go, with **embedded SQLite** — the image already ships
`HBOX_DATABASE_SQLITE_PATH` apontando pro `/data` (regra 22 do README
conventions). A single volume holds both the database and the attachments.

**It is the most hardened service in the repository**, alongside
[uptime-kuma](../uptime-kuma/) e [ntfy](../ntfy/): `ReadOnly=true`,
`DropCapability=ALL` e `User=1000` — testado exercitando o app, com a UI
e o `/api/v1/status` respondendo 200 e o banco sendo criado no volume.

### The mandatory secret

Since 0.26 HomeBox **does not start** without `HBOX_AUTH_API_KEY_PEPPER` —
the
processo morre no start com:

```
panic: auth.api_key_pepper must be set to at least 32 bytes;
generate with `openssl rand -base64 48`
```

Hence the `podman secret` in step 3. **Changing the value later invalidates
every API key already issued** (it does not affect ordinary login), so it goes
into the
backup junto com o volume.

### Sobre a tag da imagem

The GitHub releases are `v0.26.2`, but **the image tag has no `v`**:
`ghcr.io/sysadminsmedia/homebox:0.26.2`. Copying the number from the releases
page straight into `Image=` gives `manifest unknown`.

## Files

```
homebox.container   # main unit
.env.example        # cadastro, moeda, limite de upload
```

## Prerequisites

- Rootless Podman with systemd `--user` working
- `podman secret` ([regra 2](../../docs/conventions.md))

## Installation

```bash
python3 install.py homebox            # dry-run: shows what it will do
python3 install.py homebox --apply
```

For the local network only, `--access local`; on the tailnet and the LAN,
`--access both`. Adding `--href-local` points the dashboard link at the LAN.
The script creates the directories, writes the `.env`, generates the secrets,
fixes the volumes' ownership, starts the service and prints the address at the
end — see [Installing and operating](../../docs/installing.md).

Open `http://<host-ip>:3100` (ou via [tsdproxy](../tsdproxy/) em
`https://homebox.<your-tailnet>.ts.net`) e criar a conta.

<details>
<summary><b>Manual installation</b> (advanced) — the same steps, one at a time</summary>


```bash
# 1. Download the unit (no need to clone the repository)
mkdir -p ~/.config/containers/systemd
wget -P ~/.config/containers/systemd/ \
  https://raw.githubusercontent.com/wallacepnts/quadlet-homelab/main/apps/homebox/homebox.container

# 2. Directory, with the owner matching the unit's User=1000.
#    `podman unshare` runs the chown INSIDE the user namespace, which is
#    where the container's 1000 exists (on the host that becomes 100999).
mkdir -p ~/.config/containers/volumes/homebox/data
podman unshare chown -R 1000:1000 ~/.config/containers/volumes/homebox/data

# 3. The mandatory secret (see above)
mkdir -p ~/.config/containers/secrets/homebox
openssl rand -base64 48 | tr -d '\n' \
  > ~/.config/containers/secrets/homebox/api-key-pepper.txt
chmod 600 ~/.config/containers/secrets/homebox/api-key-pepper.txt
podman secret create homebox-api-key-pepper \
  ~/.config/containers/secrets/homebox/api-key-pepper.txt

# 4. Variables. Start with signup OPEN so you can create your account —
#    step 6 closes it afterwards.
mkdir -p ~/.config/containers/env
wget -O ~/.config/containers/env/homebox.env \
  https://raw.githubusercontent.com/wallacepnts/quadlet-homelab/main/apps/homebox/.env.example
sed -i 's/^HBOX_OPTIONS_ALLOW_REGISTRATION=false/HBOX_OPTIONS_ALLOW_REGISTRATION=true/' \
  ~/.config/containers/env/homebox.env

# 5. Start it
systemctl --user daemon-reload
systemctl --user start homebox
```

Open `http://<host-ip>:3100` (ou via [tsdproxy](../tsdproxy/) em
`https://homebox.<your-tailnet>.ts.net`) e criar a conta.

```bash
# 6. Fechar o cadastro depois de criar a sua conta
sed -i 's/^HBOX_OPTIONS_ALLOW_REGISTRATION=true/HBOX_OPTIONS_ALLOW_REGISTRATION=false/' \
  ~/.config/containers/env/homebox.env
systemctl --user restart homebox
# conferir: allowRegistration deve virar false
curl -s http://127.0.0.1:3100/api/v1/status | grep -o '"allowRegistration":[a-z]*'
```

</details>

## Configuration

The `.env.example` already carries two choices made by this repository:

- **`HBOX_OPTIONS_CHECK_GITHUB_RELEASE=false`** — o HomeBox consulta a
  GitHub API on its own to announce new versions. Here that job belongs to
  [wud](../wud/), so it is one fewer outbound connection.
- **`HBOX_WEB_MAX_UPLOAD_SIZE=50`** — the default is 10 MB, and a scanned
  receipt or a PDF manual goes past that easily.

Fora isso, `HBOX_OPTIONS_CURRENCIES=BRL` define a moeda dos valores.

## Auto-update

No `AutoUpdate=` — an explicit tag (`0.26.2`), bumped by hand
(rule 9 of the [conventions](../../docs/conventions.md)). The inventory is your real data, and schema migrations between HomeBox
versions are not rare: read the release notes and take a backup first.

## Backup & recovery

```bash
systemctl --user stop homebox
tar -czf homebox-backup-$(date +%Y%m%d-%H%M%S).tar.gz \
  -C ~/.config/containers/volumes homebox
systemctl --user start homebox
```

O secret (`~/.config/containers/secrets/homebox/`) precisa de backup
separado — sem o mesmo pepper, as API keys emitidas param de valer.

When restoring on another machine, redo step 2's `podman unshare chown`
after extracting: tar preserves the old uid, which may not be the same mapping
on the destination.

## Useful commands

```bash
systemctl --user status homebox
podman logs -f homebox
curl -s http://127.0.0.1:3100/api/v1/status
```

## Credits

Quadlet deploy based on
[HomeBox](https://github.com/sysadminsmedia/homebox) da
[Sysadmins Media](https://github.com/sysadminsmedia) (AGPL-3.0), fork
mantido do projeto original de [hay-kot](https://github.com/hay-kot).
