Abrir `http://<ip-do-host>:8094` ou `https://owncloud.<your-tailnet>.ts.net`.

### Editando documentos

Com o Collabora rodando, `.docx`, `.xlsx` e
`.odt` abrem no navegador em vez de só baixar. Ligue o app uma vez:

```bash
podman exec owncloud occ app:enable richdocuments
podman exec owncloud occ config:app:set richdocuments wopi_url \
  --value="https://collabora.<your-tailnet>.ts.net"
```

O `wopi_url` é de onde o **seu navegador** carrega o editor, então é o endereço
da tailnet e não um nome de container.
