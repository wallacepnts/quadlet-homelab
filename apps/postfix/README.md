# Postfix

<img src="https://cdn.jsdelivr.net/gh/Templarian/MaterialDesign-SVG@v7.4.47/svg/email-fast.svg" width="64" height="64" alt="">

**[🇧🇷 Leia em português](./README.pt-BR.md)**

A relay ("null client") for the other containers. They hand mail to one
address instead of each carrying the provider's credentials, and only this
service knows how the mail leaves the house.

Sends only. It is not an inbox, and there is no web interface — the mail goes
in on port **1587** and out through whatever `RELAYHOST` you configure.

## Install

```bash
qh postfix            # shows the plan
qh postfix --apply
```

Then edit `~/.config/containers/env/postfix.env`: `POSTFIX_myhostname`, and a
`RELAYHOST` if you have one (see below). Restart with `qh postfix --update
--apply`.

Point an app at it — host `<host-ip>`, port **1587**, no authentication:

```
SMTP_HOST=<host-ip>
SMTP_PORT=1587
```

<details>
<summary><b>Manual install</b></summary>

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

## Update

```bash
qh postfix --update --apply
```

Pinned to `v5.1.0`. Nothing updates on its own — a new version is applied when
you run the command above.

## Backup

```bash
qh postfix --backup --apply --out ~/backups
```

It stops the service, packs the queue and the `.env`, and starts it again.

To restore, over the current data:

```bash
qh postfix --restore ~/backups/postfix-20260809-1200.tar.gz --apply
```

## Remove

```bash
qh postfix --remove --apply           # stops it, keeps the queue
qh postfix --remove --purge --apply   # and deletes the volume and the .env
```

`--purge` throws away anything still queued.

## Commands

```bash
systemctl --user status postfix
podman logs -f postfix
podman exec postfix postqueue -p     # what is waiting, and why
podman exec postfix postqueue -f     # try again now
```

Send a test message from the host:

```bash
python3 -c "import smtplib; smtplib.SMTP('127.0.0.1', 1587).sendmail(
  'homelab@test.local', ['you@example.com'], 'Subject: hello\n\nit works')"
```

## Credits

[docker-postfix](https://github.com/bokysan/docker-postfix) by
[bokysan](https://github.com/bokysan) — MIT

[Official documentation](https://github.com/bokysan/docker-postfix#readme)
