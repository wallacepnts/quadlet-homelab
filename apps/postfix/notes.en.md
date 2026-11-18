Edit `~/.config/containers/env/postfix.env`: `POSTFIX_myhostname`, and a `RELAYHOST` if you have one. Restart with `qh postfix --update --apply`.

Point an app at it: host `<host-ip>`, port **1587**, no authentication.

Without a relay Postfix delivers by itself, which needs outbound port 25 open (most home connections block it) and a domain with SPF, DKIM and reverse DNS in agreement, or the mail is filed as spam. A relay is the practical path:

```ini
RELAYHOST=[smtp.gmail.com]:587
RELAYHOST_USERNAME=you@gmail.com
POSTFIX_smtp_tls_security_level=encrypt
```

The password goes in a secret, not in the `.env`: `podman secret create postfix-relayhost-password -`, paste it, Ctrl-D, uncomment the `Secret=` line in the unit and run `qh postfix --update --apply`.
