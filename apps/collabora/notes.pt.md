Em `~/.config/containers/env/collabora.env`, ponha o endereço do seu ownCloud em `aliasgroup1` (uma expressão regular, com os pontos escapados: `https://owncloud\.<your-tailnet>\.ts\.net:443`) e reinicie com `qh collabora --update --apply`. No ownCloud, uma vez:

```bash
podman exec owncloud occ app:enable richdocuments
podman exec owncloud occ config:app:set richdocuments wopi_url \
  --value="https://collabora.<your-tailnet>.ts.net"
```

`wopi_url` é de onde *o seu navegador* carrega o editor. Um host fora de `aliasgroup1` recebe `unauthorized WOPI host`, que parece um documento carregando para sempre. Ao remover, rode também `occ app:disable richdocuments`.
