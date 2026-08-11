# Open WebUI

<img src="https://cdn.jsdelivr.net/gh/homarr-labs/dashboard-icons/svg/open-webui.svg" width="64" height="64" alt="">

**[🇧🇷 Leia em português](./README.pt-BR.md)**

A web chat interface plus a local LLM server, CPU-only by default (NVIDIA/AMD GPU options are documented).

## Install

```bash
qh openwebui            # shows the plan
qh openwebui --apply
```

Open `http://<host-ip>:3003` or `https://ollama.<your-tailnet>.ts.net`.

<details>
<summary><b>Manual install</b></summary>

```bash
# 1. Download the units (no need to clone the repository)
mkdir -p ~/.config/containers/systemd/openwebui
wget -P ~/.config/containers/systemd/openwebui/ \
  https://raw.githubusercontent.com/wallacepnts/quadlet-homelab/main/apps/openwebui/openwebui-net.network \
  https://raw.githubusercontent.com/wallacepnts/quadlet-homelab/main/apps/openwebui/openwebui-ollama.container \
  https://raw.githubusercontent.com/wallacepnts/quadlet-homelab/main/apps/openwebui/openwebui.container

# 2. Data directories — a bind mount requires them to exist before the start
mkdir -p ~/.config/containers/volumes/openwebui/{ollama,webui}

# 3. Non-secret env
mkdir -p ~/.config/containers/env
wget -O ~/.config/containers/env/openwebui.env \
  https://raw.githubusercontent.com/wallacepnts/quadlet-homelab/main/apps/openwebui/.env.example

# 4. Secret — the key used to sign Open WebUI's login sessions
mkdir -p ~/.config/containers/secrets/openwebui
python3 -c "import secrets; print(secrets.token_hex(32))" \
  > ~/.config/containers/secrets/openwebui/secret-key.txt
chmod 600 ~/.config/containers/secrets/openwebui/secret-key.txt
podman secret create openwebui-secret-key \
  ~/.config/containers/secrets/openwebui/secret-key.txt

# 5. Start it (Ollama first — Open WebUI brings it up by itself via
#    Requires=, but both can be started at once through the main unit)
systemctl --user daemon-reload
systemctl --user start openwebui
```

```bash
podman exec -it ollama ollama pull llama3.2
```

</details>

## Files

```
openwebui-ollama.container
openwebui.container
openwebui-net.network
.env.example
install.ini
```

Units in this stack:

- `openwebui-ollama`
- `openwebui`
- `openwebui-n`

## Update

```bash
qh openwebui --update --apply
```

Pinned to `0.32.6`, `v0.11.0`. Nothing updates on its own — a new version is applied
when you run the command above.

## Backup

```bash
qh openwebui --backup --apply --out ~/backups
```

It stops the service, packs the data, the `.env` and the secrets, and starts
it again. Cold on purpose: copying a live database gives an archive that only
fails when you restore it.

To restore, over the current data:

```bash
qh openwebui --restore ~/backups/openwebui-20260809-1200.tar.gz --apply
```

It asks you to type `openwebui` to confirm, because the current data is deleted
before the archive is unpacked.

## Remove

```bash
qh openwebui --remove --apply           # stops it, keeps the data
qh openwebui --remove --purge --apply   # and deletes volumes, secrets and .env
```

`--purge` asks for the typed name too. The tailnet node is not deregistered by
this — that is done in the Tailscale admin.

## Commands

```bash
systemctl --user status openwebui
podman logs -f openwebui
```

## Web search

With [SearXNG](../searxng) running, the model can answer from pages fetched at
the time of the question. Uncomment the three lines in
`~/.config/containers/env/openwebui.env` and run `qh openwebui --update
--apply`:

```ini
ENABLE_RAG_WEB_SEARCH=True
RAG_WEB_SEARCH_ENGINE=searxng
SEARXNG_QUERY_URL=http://searxng:8080/search?q=<query>
```

Both containers are on `tsdproxy-net`, so `searxng` resolves by name.

## Credits

[ollama/ollama](https://github.com/ollama/ollama) — MIT

[Official documentation](https://ollama.com)
