Depois edite o `~/.config/containers/env/postfix.env`: o `POSTFIX_myhostname`
e um `RELAYHOST`, se você tiver (veja abaixo). Reinicie com `qh postfix
--update --apply`.

Aponte um app para ele — host `<ip-do-host>`, porta **1587**, sem autenticação:

```
SMTP_HOST=<ip-do-host>
SMTP_PORT=1587
```

### Entregando o e-mail

Sem `RELAYHOST`, o Postfix entrega sozinho. Isso exige a porta 25 de saída
aberta — a maioria das conexões domésticas bloqueia — e um domínio cujo SPF,
DKIM e DNS reverso concordem, ou a mensagem cai no spam. O caminho prático é um
relay:

```ini
RELAYHOST=[smtp.gmail.com]:587
RELAYHOST_USERNAME=voce@gmail.com
POSTFIX_smtp_tls_security_level=encrypt
```

A senha vai num secret, não no `.env`:

```bash
podman secret create postfix-relayhost-password -
# cole a senha e dê Ctrl-D
```

Depois descomente a linha `Secret=` na unit e rode `qh postfix --update
--apply`. É `type=env` e não arquivo montado, porque secret montado precisa de
um ponto de montagem que a imagem não tem.

### Quem pode enviar

Quem alcança a porta 1587 manda e-mail como você. Duas configurações definem o
alcance:

- `ALLOWED_SENDER_DOMAINS` lista os domínios aceitos como remetente. O
  `ALLOW_EMPTY_SENDER_DOMAINS=true`, que vem ligado, aceita qualquer um.
- `POSTFIX_mynetworks` lista as redes que podem entregar.

A porta é publicada na LAN, não na tailnet: o tsdproxy faz proxy de HTTP, e
isto fala SMTP. Em rede que você não controla, restrinja as duas.

### Backup

Para o serviço, empacota a fila e o `.env`, e religa.

### Remover

O `--purge` joga fora o que ainda estiver na fila.
