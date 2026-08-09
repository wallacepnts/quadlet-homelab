# Gitea

<img src="https://cdn.jsdelivr.net/gh/homarr-labs/dashboard-icons/svg/gitea.svg" width="64" height="64" alt="">

**[🇧🇷 Leia em português](./README.pt-BR.md)**

A light but complete Git server — repositories, issues, pull requests and CI in a single interface.

## Install

```bash
qh gitea            # shows the plan
qh gitea --apply
```

Open `http://<host-ip>:3002` or `https://gitea.<your-tailnet>.ts.net`.

<details>
<summary><b>Manual install</b></summary>

```bash
# 1. Download the unit (no need to clone the repository)
mkdir -p ~/.config/containers/systemd
wget -P ~/.config/containers/systemd/ \
  https://raw.githubusercontent.com/wallacepnts/quadlet-homelab/main/apps/gitea/gitea.container

# 2. Data directory — a bind mount requires it to exist before the start
mkdir -p ~/.config/containers/volumes/gitea/data

# 3. Secrets — generated with the image itself; Gitea uses its own format
#    (this is not a generic openssl rand)
mkdir -p ~/.config/containers/secrets/gitea
podman run --rm docker.io/gitea/gitea:1.27.1 gitea generate secret SECRET_KEY \
  > ~/.config/containers/secrets/gitea/secret-key.txt
podman run --rm docker.io/gitea/gitea:1.27.1 gitea generate secret INTERNAL_TOKEN \
  > ~/.config/containers/secrets/gitea/internal-token.txt
chmod 600 ~/.config/containers/secrets/gitea/*.txt

podman secret create gitea-secret-key ~/.config/containers/secrets/gitea/secret-key.txt
podman secret create gitea-internal-token ~/.config/containers/secrets/gitea/internal-token.txt

# 4. Non-secret env — download the example
#    installation: the DB and the domain come out right, all that is left
#    is creating the admin account in the UI)
mkdir -p ~/.config/containers/env
wget -O ~/.config/containers/env/gitea.env \
  https://raw.githubusercontent.com/wallacepnts/quadlet-homelab/main/apps/gitea/.env.example
# edit ~/.config/containers/env/gitea.env: GITEA__server__DOMAIN and
# GITEA__server__ROOT_URL

# 5. Start it
systemctl --user daemon-reload
systemctl --user start gitea
```

</details>

## Files

```
gitea.container
.env.example
install.ini
```

## Update

```bash
qh gitea --update --apply
```

Pinned to `1.27.1`. Nothing updates on its own — a new version is applied
when you run the command above.

## Backup

```bash
qh gitea --backup --apply --out ~/backups
```

It stops the service, packs the data, the `.env` and the secrets, and starts
it again. Cold on purpose: copying a live database gives an archive that only
fails when you restore it.

To restore, over the current data:

```bash
qh gitea --restore ~/backups/gitea-20260809-1200.tar.gz --apply
```

It asks you to type `gitea` to confirm, because the current data is deleted
before the archive is unpacked.

## Remove

```bash
qh gitea --remove --apply           # stops it, keeps the data
qh gitea --remove --purge --apply   # and deletes volumes, secrets and .env
```

`--purge` asks for the typed name too. The tailnet node is not deregistered by
this — that is done in the Tailscale admin.

## Commands

```bash
systemctl --user status gitea
podman logs -f gitea
```

## Credits

[go-gitea/gitea](https://github.com/go-gitea/gitea) — MIT

[Official documentation](https://gitea.com)
