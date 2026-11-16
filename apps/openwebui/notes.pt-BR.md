Abrir `http://<ip-do-host>:3003` ou `https://ollama.<your-tailnet>.ts.net`.

### Busca web

Com o SearXNG rodando, o modelo passa a responder
a partir de páginas buscadas na hora da pergunta. Descomente as três linhas do
`~/.config/containers/env/openwebui.env` e rode `qh openwebui --update
--apply`:

```ini
ENABLE_RAG_WEB_SEARCH=True
RAG_WEB_SEARCH_ENGINE=searxng
SEARXNG_QUERY_URL=http://searxng:8080/search?q=<query>
```

Os dois containers estão na `tsdproxy-net`, então `searxng` resolve pelo nome.
