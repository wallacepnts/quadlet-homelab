# Karakeep — Podman Quadlet (rootless)

**[🇧🇷 Leia em português](./README.pt-BR.md)**

Deploy do [Karakeep](https://karakeep.app) (gerenciador de bookmarks —
antigo Hoarder, renomeado pelo projeto) via Podman Quadlet, migrado do
`docker-compose.yml`
[oficial](https://github.com/karakeep-app/karakeep/blob/main/docker/docker-compose.yml).

## Architecture

Three containers on the `karakeep-net.network` network:

- `karakeep-chrome` — Chrome headless (`alpine-chrome`), usado pelo
  crawler to render pages and take a screenshot / archive the content of
  each saved link. No volume — stateless, so every restart is a fresh
  nova.
- `karakeep-meilisearch` — busca full-text sobre os bookmarks salvos
- `karakeep` — the application, exposing `3000` (mapped to `8092` on the
  host)

An **embedded SQLite** database in `/data` (no Postgres needed — unlike
[immich](../immich/), the other app here with
Meilisearch e worker separados).

`karakeep` only starts once chrome and meilisearch report `healthy`
(`Requires=`/`After=` in `[Unit]`, the same pattern as
[paperless-ngx](../paperless-ngx/)/[immich](../immich/)).

## Files

```
karakeep-net.network            # rede dedicada
karakeep-chrome.container       # Chrome headless (crawler)
karakeep-meilisearch.container  # busca full-text
karakeep.container              # the application
```

## Prerequisites

- Rootless Podman with systemd `--user` working
- `openssl` (pra gerar os segredos)

## Installation

```bash
python3 install.py karakeep            # dry-run: shows what it will do
python3 install.py karakeep --apply
```

For the local network only, `--access local`; on the tailnet and the LAN,
`--access both`. Adding `--href-local` points the dashboard link at the LAN.
The script creates the directories, writes the `.env`, generates the secrets,
fixes the volumes' ownership, starts the service and prints the address at the
end — see [Installing and operating](../../docs/installing.md).

Reach it through [tsdproxy](../tsdproxy/) (tailnet) at
`https://karakeep.<your-tailnet>.ts.net` — this setup's default. For local
access only instead, use `http://localhost:8092` **and** change `NEXTAUTH_URL`
in `karakeep.env` to match (NextAuth's rule: a single canonical URL, and that
is the one that counts in cookies and redirects).

<details>
<summary><b>Manual installation</b> (advanced) — the same steps, one at a time</summary>


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

Reach it through [tsdproxy](../tsdproxy/) (tailnet) at
`https://karakeep.<your-tailnet>.ts.net` — this setup's default. For local
access only instead, use `http://localhost:8092` **and** change `NEXTAUTH_URL`
in `karakeep.env` to match (NextAuth's rule: a single canonical URL, and that
is the one that counts in cookies and redirects).

Create the first account through the UI itself (there is no default username
or password). Afterwards, consider `DISABLE_SIGNUPS=true` in the `.env` (a
personal instance has no reason to leave signup open).

</details>

## Sincronizar bookmarks do navegador (Floccus)

[Floccus](https://floccus.org) (a browser extension — Chrome,
Firefox, Edge, Brave, Vivaldi, Opera) sincroniza os bookmarks nativos do
browser bookmarks with a backend of your own, with native Karakeep support
since version 5.6. The sync is bidirectional: saving a link in the browser
manda ele pro Karakeep, e salvar/editar pela UI do Karakeep reflete de
volta nos bookmarks do navegador (e nos outros navegadores que
sincronizam com a mesma conta).

1. Generate an API key in Karakeep: the user icon (top
   direito) → **User Settings** → **API Keys** → **New API Key** → dar um
   a name → **Create**. The key is only shown once, at that moment
   (formato `ak2_<id>_<segredo>`) — copiar antes de fechar.
2. Install Floccus in the browser and, in the configuration wizard,
   escolher **Karakeep** como tipo de conta — preencher a URL do servidor
   (`https://karakeep.<your-tailnet>.ts.net`) e a API key do passo 1.
3. Escolher quais pastas de bookmark sincronizar (o Floccus permite
   restringir a uma subpasta em vez do navegador inteiro).

## `Notify=healthy` with an image that already has a built-in HEALTHCHECK

Mesma pegadinha do paperless-ngx: a imagem oficial do
Karakeep already ships a `HEALTHCHECK` in its Dockerfile
(`wget --spider http://127.0.0.1:3000/api/health`), but that is not enough
pro Quadlet — `Notify=healthy` exige `HealthCmd=` declarado
explicitly in the `.container` too, repeating the same command
([rule 14](../../docs/conventions.md)).

## Auto-update

None of the three containers has `AutoUpdate=` — explicit tags, bumped by
hand ([rule 9](../../docs/conventions.md)). The official `docker-compose.yml`
uses `${KARAKEEP_VERSION:-release}` (a floating tag, always the latest stable
release) — swapped here for an exact version (`0.33.1`) on purpose, the same
default as the rest of the repository. Meilisearch and Chrome sit at the
versions the official compose recommends — changing them without checking
compatibility can break search or the crawler.

## Backup & recovery

What actually matters is `data/` (the embedded SQLite plus archived
assets/screenshots). `meilisearch/` is a search index — rebuildable from
scratch by reindexing, but restoring is faster than reindexing everything
again if the library is large.

```bash
systemctl --user stop karakeep karakeep-chrome karakeep-meilisearch
tar -czf karakeep-backup-$(date +%Y%m%d-%H%M%S).tar.gz \
  -C ~/.config/containers/volumes karakeep
systemctl --user start karakeep
```

The secrets (`~/.config/containers/secrets/karakeep/`) need a separate
backup too — without `NEXTAUTH_SECRET`, existing sessions are invalidated when
restoring onto a new host.

## Useful commands

```bash
systemctl --user status karakeep karakeep-chrome karakeep-meilisearch
podman logs -f karakeep
podman exec karakeep-chrome wget -qO- http://127.0.0.1:9222/json/version
```

## Credits

Quadlet deploy based on [Karakeep](https://github.com/karakeep-app/karakeep)
(antigo Hoarder). Original licence: AGPL-3.0.
