# Postfix

<img src="https://api.iconify.design/mdi/email-fast.svg?color=%23888888" width="64" height="64" alt="">

**[🇧🇷 Leia em português](./README.pt-BR.md)**

A relay ("null client") for the other containers. They hand mail to one
address instead of each carrying the provider's credentials, and only this
service knows how the mail leaves the house.

Sends only. It is not an inbox, and there is no web interface — the mail goes
in on port **1587** and out through whatever `RELAYHOST` you configure.

## First run

Then edit `~/.config/containers/env/postfix.env`: `POSTFIX_myhostname`, and a
`RELAYHOST` if you have one (see below). Restart with `qh postfix --update
--apply`.

Point an app at it — host `<host-ip>`, port **1587**, no authentication:

```
SMTP_HOST=<host-ip>
SMTP_PORT=1587
```

## Files

```
postfix.container   unit
.env.example        environment
```

Queue in `~/.config/containers/volumes/postfix/spool`, on port **1587**. The
queue is on a volume on purpose: a restart with mail still in it would lose the
mail otherwise.

## Delivering the mail

Without a `RELAYHOST`, Postfix delivers by itself. That needs outbound port 25
open — most home connections have it blocked — and a domain whose SPF, DKIM and
reverse DNS agree, or the message is filed as spam. A relay is the practical
path:

```ini
RELAYHOST=[smtp.gmail.com]:587
RELAYHOST_USERNAME=you@gmail.com
POSTFIX_smtp_tls_security_level=encrypt
```

The password goes in a secret, not in the `.env`:

```bash
podman secret create postfix-relayhost-password -
# paste the password, then Ctrl-D
```

Then uncomment the `Secret=` line in the unit and run `qh postfix --update
--apply`. It is `type=env` and not a mounted file, because a mounted secret
needs a mount point the image does not have.

## Who may send

Whoever reaches port 1587 sends mail as you. Two settings decide the reach:

- `ALLOWED_SENDER_DOMAINS` names the domains accepted as the sender.
  `ALLOW_EMPTY_SENDER_DOMAINS=true`, the shipped default, accepts any of them.
- `POSTFIX_mynetworks` names the networks allowed to hand mail in.

The port is published on the LAN, not on the tailnet: tsdproxy proxies HTTP,
and this speaks SMTP. On a network you do not control, narrow both.

## Backup

It stops the service, packs the queue and the `.env`, and starts it again.

## Remove

`--purge` throws away anything still queued.

## Credits

[docker-postfix](https://github.com/bokysan/docker-postfix) by
[bokysan](https://github.com/bokysan) — MIT

[Official documentation](https://github.com/bokysan/docker-postfix#readme)
