# ownCloud

<img src="https://cdn.jsdelivr.net/gh/homarr-labs/dashboard-icons/svg/owncloud.svg" width="64" height="64" alt="">

**[🇺🇸 Read in English](./README.md)**

Sincronização e compartilhamento de arquivos em nuvem própria.

## Primeiro acesso

Abrir `http://<ip-do-host>:8094` ou `https://owncloud.<your-tailnet>.ts.net`.

## Arquivos

```
owncloud.container
.env.example
install.ini
```

## Remover

O nó da tailnet não é desregistrado ao remover um app: isso é no admin do Tailscale.

## Editando documentos

Com o [Collabora](../collabora/README.pt-BR.md) rodando, `.docx`, `.xlsx` e
`.odt` abrem no navegador em vez de só baixar. Ligue o app uma vez:

```bash
podman exec owncloud occ app:enable richdocuments
podman exec owncloud occ config:app:set richdocuments wopi_url \
  --value="https://collabora.<your-tailnet>.ts.net"
```

O `wopi_url` é de onde o **seu navegador** carrega o editor, então é o endereço
da tailnet e não um nome de container.

## Créditos

[owncloud/core](https://github.com/owncloud/core) — AGPL-3.0.

[Documentação oficial](https://owncloud.com)
