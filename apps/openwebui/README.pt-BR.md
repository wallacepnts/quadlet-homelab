# Open WebUI

<img src="https://cdn.jsdelivr.net/gh/homarr-labs/dashboard-icons/svg/open-webui.svg" width="64" height="64" alt="">

**[🇺🇸 Read in English](./README.md)**

Interface de chat web + servidor de LLMs locais, CPU-only por padrão (opções de GPU NVIDIA/AMD documentadas).

## Primeiro acesso

Abrir `http://<ip-do-host>:3003` ou `https://ollama.<your-tailnet>.ts.net`.

## Arquivos

```
openwebui-ollama.container
openwebui.container
openwebui-net.network
.env.example
install.ini
```

Units da stack:

- `openwebui-ollama`
- `openwebui`
- `openwebui-n`

## Remover

O nó da tailnet não é desregistrado ao remover um app: isso é no admin do Tailscale.

## Busca web

Com o [SearXNG](../searxng/README.pt-BR.md) rodando, o modelo passa a responder
a partir de páginas buscadas na hora da pergunta. Descomente as três linhas do
`~/.config/containers/env/openwebui.env` e rode `qh openwebui --update
--apply`:

```ini
ENABLE_RAG_WEB_SEARCH=True
RAG_WEB_SEARCH_ENGINE=searxng
SEARXNG_QUERY_URL=http://searxng:8080/search?q=<query>
```

Os dois containers estão na `tsdproxy-net`, então `searxng` resolve pelo nome.

## Créditos

[ollama/ollama](https://github.com/ollama/ollama) — MIT

[Documentação oficial](https://ollama.com)
