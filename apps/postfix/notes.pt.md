Edite `~/.config/containers/env/postfix.env`: `POSTFIX_myhostname` e, se tiver, um `RELAYHOST`. Reinicie com `qh postfix --update --apply`.

Aponte um app para ele: host `<host-ip>`, porta **1587**, sem autenticação.

Sem relay, o Postfix entrega sozinho, o que exige a porta 25 de saída aberta (a maioria das conexões residenciais bloqueia) e um domínio com SPF, DKIM e DNS reverso de acordo, ou o e-mail cai no spam. Um relay é o caminho prático:

```ini
RELAYHOST=[smtp.gmail.com]:587
RELAYHOST_USERNAME=voce@gmail.com
POSTFIX_smtp_tls_security_level=encrypt
```

A senha vai num secret, não no `.env`: `podman secret create postfix-relayhost-password -`, cole, Ctrl-D, descomente a linha `Secret=` na unit e rode `qh postfix --update --apply`.
