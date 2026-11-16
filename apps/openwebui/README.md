# Open WebUI

<img src="https://cdn.jsdelivr.net/gh/homarr-labs/dashboard-icons/svg/open-webui.svg" width="64" height="64" alt="">

**[🇧🇷 Leia em português](./README.pt-BR.md)**

A web chat interface plus a local LLM server, CPU-only by default (NVIDIA/AMD GPU options are documented).

## First run

Open `http://<host-ip>:3003` or `https://ollama.<your-tailnet>.ts.net`.

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

## Remove

The tailnet node is not deregistered when an app is removed: do that in the Tailscale admin.

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
