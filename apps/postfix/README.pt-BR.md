# Postfix

<img src="https://api.iconify.design/mdi/email-fast.svg?color=%23888888" width="64" height="64" alt="">

**[🇺🇸 Read in English](./README.md)**

Relay ("null client") para os outros containers. Eles entregam o e-mail num
endereço só, em vez de cada um carregar a credencial do provedor, e só este
serviço sabe como o e-mail sai de casa.

Só envia. Não é caixa de entrada e não tem interface web — o e-mail entra na
porta **1587** e sai pelo `RELAYHOST` que você configurar.

## Primeiro acesso

Depois edite o `~/.config/containers/env/postfix.env`: o `POSTFIX_myhostname`
e um `RELAYHOST`, se você tiver (veja abaixo). Reinicie com `qh postfix
--update --apply`.

Aponte um app para ele — host `<ip-do-host>`, porta **1587**, sem autenticação:

```
SMTP_HOST=<ip-do-host>
SMTP_PORT=1587
```

## Arquivos

```
postfix.container   unit
.env.example        ambiente
```

Fila em `~/.config/containers/volumes/postfix/spool`, na porta **1587**. A fila
fica num volume de propósito: reiniciar com e-mail dentro dela perderia o
e-mail.

## Entregando o e-mail

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

## Quem pode enviar

Quem alcança a porta 1587 manda e-mail como você. Duas configurações definem o
alcance:

- `ALLOWED_SENDER_DOMAINS` lista os domínios aceitos como remetente. O
  `ALLOW_EMPTY_SENDER_DOMAINS=true`, que vem ligado, aceita qualquer um.
- `POSTFIX_mynetworks` lista as redes que podem entregar.

A porta é publicada na LAN, não na tailnet: o tsdproxy faz proxy de HTTP, e
isto fala SMTP. Em rede que você não controla, restrinja as duas.

## Backup

Para o serviço, empacota a fila e o `.env`, e religa.

## Remover

O `--purge` joga fora o que ainda estiver na fila.

## Créditos

[docker-postfix](https://github.com/bokysan/docker-postfix) por
[bokysan](https://github.com/bokysan) — MIT

[Documentação oficial](https://github.com/bokysan/docker-postfix#readme)
