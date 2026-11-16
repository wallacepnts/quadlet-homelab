Depois, no `~/.config/containers/env/collabora.env`, ponha o endereço do seu
ownCloud no `aliasgroup1` e reinicie com `qh collabora --update --apply`. Do
lado do ownCloud, uma vez:

```bash
podman exec owncloud occ app:enable richdocuments
podman exec owncloud occ config:app:set richdocuments wopi_url \
  --value="https://collabora.<your-tailnet>.ts.net"
```

### As duas pontas da ligação

Elas precisam concordar, e cada uma falha de um jeito quando não concordam:

- **`aliasgroup1`**, aqui, é quem pode embutir o editor — é expressão regular,
  então os pontos vão escapados:
  `https://owncloud\.<your-tailnet>\.ts\.net:443`. Host fora da lista recebe
  `unauthorized WOPI host`, o que no ownCloud aparece como documento que roda
  para sempre sem abrir.
- **`wopi_url`**, no ownCloud, é de onde o navegador carrega o editor. Tem que
  ser o endereço que o **seu navegador** alcança, não um nome de container — a
  página é desenhada na sua máquina.

Servidor a servidor eles conversam pela `tsdproxy-net` pelo nome, que é como o
ownCloud lê `http://collabora:9980/hosting/discovery` sem porta publicada.

O `extra_params=--o:ssl.enable=false --o:ssl.termination=true` não é opcional
atrás do tsdproxy: sem a segunda flag o Collabora monta as URLs dele como
`http://` e o navegador bloqueia como conteúdo misto; sem a primeira ele serve
TLS por conta própria, com um certificado que ninguém confia.

### Atualizar

O Collabora não publica release no GitHub, então o `qh-updates` compara com a lista de tags do registry.

### Backup

Não há o que copiar — veja [Arquivos](#arquivos). Os documentos são do
ownCloud, e o `qh owncloud --backup` cobre eles.

### Remover

Desligue também do lado do ownCloud, senão o menu de arquivo segue oferecendo
um editor que não existe mais:

```bash
podman exec owncloud occ app:disable richdocuments
```
