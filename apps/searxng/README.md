# SearXNG

<img src="https://cdn.jsdelivr.net/gh/homarr-labs/dashboard-icons/png/searxng.png" width="64" height="64" alt="">

**[🇧🇷 Leia em português](./README.pt-BR.md)**

A metasearch engine: it forwards your query to dozens of other engines and
merges the results. It stores no profile, sets no tracking cookie, and the
engines see the server asking, not you.

It also answers in JSON, which is what makes it useful to
[Open WebUI](../openwebui) — see [below](#open-webui).

## First run

Open `https://searxng.<your-tailnet>.ts.net`.

## Files

```
searxng.container      unit
config/settings.yml    the settings, into the volume
install.ini
```

The file is short because of its first line, `use_default_settings: true`:
everything else comes from the defaults inside the image, so a new version's
engine list arrives on its own instead of being frozen in a copy here. What
this repository sets on top is the JSON output.

`secret_key` is not in it. The image would generate one into `settings.yml` on
first start, but that file ships from here and is mounted read-only, so the key
arrives as `${SEARXNG_SECRET}` from a Podman secret — which the defaults
already read.

## Open WebUI

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

## Update

SearXNG publishes no GitHub releases and tags by date plus commit, so `qh-updates` compares against the registry's tag list instead of the usual release redirect.

## Backup

There is little to lose: the settings file is in this repository and the search
history is nobody's, not even the server's. The backup exists for the
preferences you may have set.

## Credits

[searxng/searxng](https://github.com/searxng/searxng) — AGPL-3.0.

[Official documentation](https://docs.searxng.org/)
