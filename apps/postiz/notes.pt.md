Abra `https://postiz.<your-tailnet>.ts.net` e crie a sua conta. O primeiro cadastro funciona e depois a página fecha (`DISABLE_REGISTRATION=true` está no `.env`). Para adicionar alguém depois, ponha `false`, reinicie, crie a conta e volte para `true`.

O endereço precisa ser o da tailnet: o Postiz monta os links de login e OAuth a partir dele, e a Meta só aceita redirecionamento HTTPS.

O `nginx.conf` que esta pasta instala reescreve o `Domain` do cookie de sessão (`proxy_cookie_domain .ts.net $host;`): `ts.net` é um sufixo público, então os navegadores recusam o cookie e o login fica em laço. É o `var/docker/nginx.conf` do projeto mais essas duas linhas: **numa troca de versão, compare-os** e leve as linhas adiante.
