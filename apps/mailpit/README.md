# Mailpit

<img src="https://cdn.jsdelivr.net/gh/homarr-labs/dashboard-icons/svg/mailpit.svg" width="64" height="64" alt="">

**[🇧🇷 Leia em português](./README.pt-BR.md)**

An SMTP server that accepts every message and delivers none. Point an app's
mail settings at it and read what it sent in the browser, instead of at a real
address.

## First run

The install prints the user and password at the end. Open
`http://<host-ip>:8025` or `https://mailpit.<your-tailnet>.ts.net`.

Then point your app at the SMTP port — host `<host-ip>`, port **1025**, no
authentication, no TLS:

```
SMTP_HOST=<host-ip>
SMTP_PORT=1025
```

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

## Your own password

The install generates one. To choose it, at install time or any time after:

```bash
qh mailpit --reinstall --ask-secrets --apply
```

and type **user and password together**, the way Mailpit reads them:

```
admin:your-password
```

Measured on v1.31.2, two ways to get it wrong without an error:

- **No space in the password.** Mailpit splits the value at whitespace to allow
  several users, so `admin:my password` makes the password just `my` — and
  `password` a second entry. The service is up and the password you typed is
  refused.
- **Only the password alone**, with no `admin:` in front, and the service still
  comes up, with authentication on and no one able to log in.

A `:` in the password is fine — it splits at the first one. Enter with nothing
typed generates a random one again. `--reinstall` recreates the secret and
restarts the service, and leaves the stored mail alone — but it also puts
`.env.example` back over `~/.config/containers/env/mailpit.env`, so save any
change of yours there first. `qh mailpit` prints the
user and password in use.

## Remove

The tailnet node is not deregistered when an app is removed: do that in the Tailscale admin.

## Credits

[Mailpit](https://github.com/axllent/mailpit) — MIT

[Official documentation](https://mailpit.axllent.org/docs/)
