Open `https://searxng.<your-tailnet>.ts.net`.

### Open WebUI

SearXNG answers `/search?q=...&format=json`, and that is the interface Open
WebUI's web search uses. With it, the model answers from pages fetched at the
time of the question instead of only from what it was trained on.

In `~/.config/containers/env/openwebui.env`:

```ini
ENABLE_RAG_WEB_SEARCH=True
RAG_WEB_SEARCH_ENGINE=searxng
SEARXNG_QUERY_URL=http://searxng:8080/search?q=<query>
```

Then `qh openwebui --update --apply`. The two containers share
`tsdproxy-net`, so `searxng` resolves by name — no host IP and no published
port involved.

`format=json` is not a SearXNG default; without the `formats` block in
`settings.yml` it answers **403** to anything that is not a browser, and Open
WebUI's search silently returns nothing.

### Update

SearXNG publishes no GitHub releases and tags by date plus commit, so `qh-updates` compares against the registry's tag list instead of the usual release redirect.

### Backup

There is little to lose: the settings file is in this repository and the search
history is nobody's, not even the server's. The backup exists for the
preferences you may have set.
