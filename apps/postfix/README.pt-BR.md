# Postfix

<img src="https://cdn.jsdelivr.net/gh/Templarian/MaterialDesign-SVG@v7.4.47/svg/email-fast.svg" width="64" height="64" alt="">

**[🇺🇸 Read in English](./README.md)**

Relay ("null client") para os outros containers. Eles entregam o e-mail num
endereço só, em vez de cada um carregar a credencial do provedor, e só este
serviço sabe como o e-mail sai de casa.

Só envia. Não é caixa de entrada e não tem interface web — o e-mail entra na
porta **1587** e sai pelo `RELAYHOST` que você configurar.

## Instalação

```bash
qh postfix            # mostra o plano
qh postfix --apply
```

Depois edite o `~/.config/containers/env/postfix.env`: o `POSTFIX_myhostname`
e um `RELAYHOST`, se você tiver (veja abaixo). Reinicie com `qh postfix
--update --apply`.

Aponte um app para ele — host `<ip-do-host>`, porta **1587**, sem autenticação:

```
SMTP_HOST=<ip-do-host>
SMTP_PORT=1587
```

<details>
<summary><b>Instalação manual</b></summary>

```bash
mkdir -p ~/.config/containers/systemd ~/.config/containers/env
mkdir -p ~/.config/containers/volumes/postfix/spool

wget -P ~/.config/containers/systemd/ \
  https://raw.githubusercontent.com/wallacepnts/quadlet-homelab/main/apps/postfix/postfix.container
wget -O ~/.config/containers/env/postfix.env \
  https://raw.githubusercontent.com/wallacepnts/quadlet-homelab/main/apps/postfix/.env.example

systemctl --user daemon-reload
systemctl --user start postfix
```

</details>

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

## Atualizar

```bash
qh postfix --update --apply
```

Pinado em `v5.1.0`. Nada atualiza sozinho — a versão nova entra quando você
roda o comando acima.

## Backup

```bash
qh postfix --backup --apply --out ~/backups
```

Para o serviço, empacota a fila e o `.env`, e religa.

Para restaurar, por cima dos dados atuais:

```bash
qh postfix --restore ~/backups/postfix-20260809-1200.tar.gz --apply
```

## Remover

```bash
qh postfix --remove --apply           # para, mantém a fila
qh postfix --remove --purge --apply   # e apaga o volume e o .env
```

O `--purge` joga fora o que ainda estiver na fila.

## Comandos

```bash
systemctl --user status postfix
podman logs -f postfix
podman exec postfix postqueue -p     # o que está esperando, e por quê
podman exec postfix postqueue -f     # tenta de novo agora
```

Enviar uma mensagem de teste a partir do host:

```bash
python3 -c "import smtplib; smtplib.SMTP('127.0.0.1', 1587).sendmail(
  'homelab@test.local', ['voce@example.com'], 'Subject: hello\n\nfuncionou')"
```

## Créditos

[docker-postfix](https://github.com/bokysan/docker-postfix) por
[bokysan](https://github.com/bokysan) — MIT

[Documentação oficial](https://github.com/bokysan/docker-postfix#readme)
