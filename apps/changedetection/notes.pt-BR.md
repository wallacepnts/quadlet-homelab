Abrir `https://changedetection.<your-tailnet>.ts.net`. Defina uma senha em
**Settings → General** se mais alguém alcança a sua tailnet.

### Notificações

Ele fala [Apprise](https://github.com/caronc/apprise), então o destino é uma
URL. Para o ntfy deste repositório, em **Settings →
Notifications**:

```
ntfy://ntfy:2586/changes
```

O `BASE_URL` do `.env` é para onde apontam os links dentro dessas mensagens.
Sem ele, os links levam o hostname do container, que não resolve no seu
celular.

### Páginas que exigem navegador

A busca padrão é uma requisição HTTP simples: rápida, barata e suficiente para
a maioria das páginas. Página que monta o conteúdo com JavaScript volta vazia,
e o seletor visual de elemento também precisa de navegador de verdade.

A saída é um sidecar com Chrome e a linha `PLAYWRIGHT_DRIVER_URL`, comentada no
`.env`. Ela fica desligada de propósito: é um segundo container com um
navegador dentro, maquinário demais para uma página que normalmente dá para
vigiar pelo endpoint JSON dela. Procure por um antes de acrescentar meio
gigabyte de Chrome.

### Backup

Para o serviço, empacota o datastore e o `.env`, e sobe de novo.
