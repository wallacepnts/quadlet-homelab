# Mailpit

<img src="https://cdn.jsdelivr.net/gh/homarr-labs/dashboard-icons/svg/mailpit.svg" width="64" height="64" alt="">

**[🇧🇷 Leia em português](./README.pt-BR.md)**

An SMTP server that accepts every message and delivers none. Point an app's
mail settings at it and read what it sent in the browser, instead of at a real
address.

## Install

```bash
qh mailpit            # shows the plan
qh mailpit --apply
```

The install prints the user and password at the end. Open
`http://<host-ip>:8025` or `https://mailpit.<your-tailnet>.ts.net`.

Then point your app at the SMTP port — host `<host-ip>`, port **1025**, no
authentication, no TLS:

```
SMTP_HOST=<host-ip>
SMTP_PORT=1025
```

<details>
<summary><b>Manual install</b></summary>

```bash
mkdir -p ~/.config/containers/systemd ~/.config/containers/env
mkdir -p ~/.config/containers/volumes/mailpit/data
podman unshare chown -R 1000:1000 ~/.config/containers/volumes/mailpit

printf 'admin:%s' "$(openssl rand -hex 12)" \
  | podman secret create mailpit-ui-auth -

wget -P ~/.config/containers/systemd/ \
  https://raw.githubusercontent.com/wallacepnts/quadlet-homelab/main/apps/mailpit/mailpit.container
wget -O ~/.config/containers/env/mailpit.env \
  https://raw.githubusercontent.com/wallacepnts/quadlet-homelab/main/apps/mailpit/.env.example

systemctl --user daemon-reload
systemctl --user start mailpit
```

Read the password back with `podman secret inspect mailpit-ui-auth
--showsecret --format '{{.SecretData}}'`.

</details>

## Files

```
mailpit.container   unit
.env.example        environment
install.ini         the secret's recipe
```

Data in `~/.config/containers/volumes/mailpit/data`. Web on **8025**, SMTP on
**1025**.

## Authentication

The web UI asks for a password; the SMTP port does not. That is deliberate:
the apps sending mail are on your own network and would each need credentials,
while the UI holds everything they sent — password resets, confirmation links,
invoices.

Both come from one secret, `mailpit-ui-auth`, in the `user:password` form
Mailpit reads.

## Update

```bash
qh mailpit --update --apply
```

Pinned to `v1.30.7`. Nothing updates on its own — a new version is applied
when you run the command above.

## Backup

```bash
qh mailpit --backup --apply --out ~/backups
```

It stops the service, packs the data, the `.env` and the secrets, and starts it
again. Cold on purpose: copying a live database gives an archive that only
fails when you restore it.

To restore, over the current data:

```bash
qh mailpit --restore ~/backups/mailpit-20260809-1200.tar.gz --apply
```

It asks you to type `mailpit` to confirm, because the current data is deleted
before the archive is unpacked.

## Remove

```bash
qh mailpit --remove --apply           # stops it, keeps the data
qh mailpit --remove --purge --apply   # and deletes volumes, secrets and .env
```

`--purge` asks for the typed name too. The tailnet node is not deregistered by
this — that is done in the Tailscale admin.

## Commands

```bash
systemctl --user status mailpit
podman logs -f mailpit
podman exec mailpit /mailpit readyz
```

Send a test message from the host:

```bash
python3 -c "import smtplib; smtplib.SMTP('127.0.0.1', 1025).sendmail(
  'a@test', ['b@test'], 'Subject: hello\n\nit works')"
```

## Credits

[Mailpit](https://github.com/axllent/mailpit) — MIT

[Official documentation](https://mailpit.axllent.org/docs/)
