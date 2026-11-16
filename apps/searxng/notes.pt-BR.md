Abrir `https://searxng.<your-tailnet>.ts.net`.

### Open WebUI

O SearXNG responde `/search?q=...&format=json`, e é essa a interface que a
busca web do Open WebUI usa. Com ela, o modelo responde a partir de páginas
buscadas na hora da pergunta, e não só do que ele foi treinado.

No `~/.config/containers/env/openwebui.env`:

```ini
ENABLE_RAG_WEB_SEARCH=True
RAG_WEB_SEARCH_ENGINE=searxng
SEARXNG_QUERY_URL=http://searxng:8080/search?q=<query>
```

Depois `qh openwebui --update --apply`. Os dois containers dividem a
`tsdproxy-net`, então `searxng` resolve pelo nome — sem IP do host e sem porta
publicada no meio.

O `format=json` não é padrão do SearXNG; sem o bloco `formats` no
`settings.yml` ele responde **403** para o que não é navegador, e a busca do
Open WebUI volta vazia em silêncio.

### Atualizar

O SearXNG não publica release no GitHub e marca por data mais commit, então o `qh-updates` compara com a lista de tags do registry, e não com o redirect de release de sempre.

### Backup

Há pouco a perder: o arquivo de configuração está neste repositório e o
histórico de busca não é de ninguém, nem do servidor. O backup existe pelas
preferências que você tenha ajustado.
