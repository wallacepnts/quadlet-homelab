Open `http://<host-ip>:3003` or `https://ollama.<your-tailnet>.ts.net`.

### Web search

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
