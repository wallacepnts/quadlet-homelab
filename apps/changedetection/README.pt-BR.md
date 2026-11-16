# changedetection.io

<img src="https://cdn.jsdelivr.net/gh/homarr-labs/dashboard-icons/svg/changedetection.svg" width="64" height="64" alt="">

**[🇺🇸 Read in English](./README.md)**

Vigia páginas e avisa o que mudou: um preço, um contador de estoque, um
parágrafo nos termos de uso de alguém. Ele guarda a versão anterior, então o
aviso vem como diferença, e não como "alguma coisa mexeu".

Substitui os sites de monitoramento que pedem conta e e-mail para fazer o
mesmo.

## Primeiro acesso

Abrir `https://changedetection.<your-tailnet>.ts.net`. Defina uma senha em
**Settings → General** se mais alguém alcança a sua tailnet.

## Arquivos

```
changedetection.container   unit
.env.example                ambiente
```

Tudo fica em `~/.config/containers/volumes/changedetection/datastore`: a lista
de páginas no `changedetection.json`, e uma pasta por página com os snapshots
que ele compara.

## Notificações

Ele fala [Apprise](https://github.com/caronc/apprise), então o destino é uma
URL. Para o [ntfy](../ntfy/README.pt-BR.md) deste repositório, em **Settings →
Notifications**:

```
ntfy://ntfy:2586/changes
```

O `BASE_URL` do `.env` é para onde apontam os links dentro dessas mensagens.
Sem ele, os links levam o hostname do container, que não resolve no seu
celular.

## Páginas que exigem navegador

A busca padrão é uma requisição HTTP simples: rápida, barata e suficiente para
a maioria das páginas. Página que monta o conteúdo com JavaScript volta vazia,
e o seletor visual de elemento também precisa de navegador de verdade.

A saída é um sidecar com Chrome e a linha `PLAYWRIGHT_DRIVER_URL`, comentada no
`.env`. Ela fica desligada de propósito: é um segundo container com um
navegador dentro, maquinário demais para uma página que normalmente dá para
vigiar pelo endpoint JSON dela. Procure por um antes de acrescentar meio
gigabyte de Chrome.

## Backup

Para o serviço, empacota o datastore e o `.env`, e sobe de novo.

## Créditos

[dgtlmoon/changedetection.io](https://github.com/dgtlmoon/changedetection.io)
— Apache-2.0.

[Documentação oficial](https://changedetection.io/)
