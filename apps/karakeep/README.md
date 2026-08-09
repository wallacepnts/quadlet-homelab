# Karakeep

<img src="https://cdn.jsdelivr.net/gh/homarr-labs/dashboard-icons/svg/karakeep.svg" width="64" height="64" alt="">

**[🇧🇷 Leia em português](./README.pt-BR.md)**

A bookmark manager with full-text search and automatic archiving of every saved page's content.

## Install

```bash
qh karakeep            # shows the plan
qh karakeep --apply
```

Open `http://<host-ip>:8092` or `https://karakeep.<your-tailnet>.ts.net`.

<details>
<summary><b>Manual install</b></summary>

```bash
# 1. Baixar as units pra uma subpasta dedicada (sem precisar clonar o
#    repository)
mkdir -p ~/.config/containers/systemd/karakeep
for f in karakeep-net.network karakeep-chrome.container \
         karakeep-meilisearch.container karakeep.container; do
  wget -P ~/.config/containers/systemd/karakeep/ \
    "https://raw.githubusercontent.com/wallacepnts/quadlet-homelab/main/apps/karakeep/$f"
done

# 2. Data directories — a bind mount requires them to exist before the start
mkdir -p ~/.config/containers/volumes/karakeep/{data,meilisearch}

# 3. Secrets — generated once, never versioned. The same
#    karakeep-meili-key is used in both containers (meilisearch validates
#    the key, karakeep authenticates with it).
mkdir -p ~/.config/containers/secrets/karakeep
openssl rand -base64 36 | tr -d '\n' > ~/.config/containers/secrets/karakeep/nextauth-secret.txt
openssl rand -base64 36 | tr -dc 'A-Za-z0-9' > ~/.config/containers/secrets/karakeep/meili-master-key.txt
chmod 600 ~/.config/containers/secrets/karakeep/*.txt

podman secret create karakeep-nextauth-secret ~/.config/containers/secrets/karakeep/nextauth-secret.txt
podman secret create karakeep-meili-key ~/.config/containers/secrets/karakeep/meili-master-key.txt

# 4. Non-secret env — download the example
#    match the address used in the browser exactly
mkdir -p ~/.config/containers/env
wget -O ~/.config/containers/env/karakeep.env \
  https://raw.githubusercontent.com/wallacepnts/quadlet-homelab/main/apps/karakeep/.env.example
# edit ~/.config/containers/env/karakeep.env: NEXTAUTH_URL

# 5. Start it (chrome and meilisearch come up first, via Requires=)
systemctl --user daemon-reload
systemctl --user start karakeep
```

</details>

## Files

```
karakeep-chrome.container
karakeep-meilisearch.container
karakeep.container
karakeep-net.network
.env.example
install.ini
```

Units in this stack:

- `karakeep-chrome`
- `karakeep-meilisearch`
- `karakeep`
- `karakeep-n`

## Update

```bash
qh karakeep --update --apply
```

Pinned to `0.33.1`, `124`, `v1.41.0`. Nothing updates on its own — a new version is applied
when you run the command above.

## Backup

```bash
qh karakeep --backup --apply --out ~/backups
```

It stops the service, packs the data, the `.env` and the secrets, and starts
it again. Cold on purpose: copying a live database gives an archive that only
fails when you restore it.

To restore, over the current data:

```bash
qh karakeep --restore ~/backups/karakeep-20260809-1200.tar.gz --apply
```

It asks you to type `karakeep` to confirm, because the current data is deleted
before the archive is unpacked.

## Remove

```bash
qh karakeep --remove --apply           # stops it, keeps the data
qh karakeep --remove --purge --apply   # and deletes volumes, secrets and .env
```

`--purge` asks for the typed name too. The tailnet node is not deregistered by
this — that is done in the Tailscale admin.

## Commands

```bash
systemctl --user status karakeep
podman logs -f karakeep
```

## Credits

[karakeep-app/karakeep](https://github.com/karakeep-app/karakeep) — AGPL-3.0.

[Official documentation](https://karakeep.app)
