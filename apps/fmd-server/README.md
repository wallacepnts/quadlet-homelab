# FMD Server

<img src="https://cdn.jsdelivr.net/gh/homarr-labs/dashboard-icons/svg/fmd.svg" width="64" height="64" alt="">

**[🇧🇷 Leia em português](./README.pt-BR.md)**

The server half of [FMD](https://fmd-foss.org) — find, ring, lock or wipe your
Android phone from a browser, without Google's Find My Device. The phone runs the
FMD app (on F-Droid); this is where it reports to.

Locations and pictures are **encrypted on the phone** before they are sent: the
server stores ciphertext and cannot read it. The flip side is that forgetting
the account password loses the data — there is nothing here to recover it with.

## First run

The install ends by printing the **registration token**. Enter it in the FMD app
when you point it at `https://fmd.<your-tailnet>.ts.net`.

## Files

```
fmd-server.container
install.ini
```

## Reaching it — and the phone reaching it

**FMD Server has to be served over HTTPS**: its web interface does not work over
plain HTTP. On the tailnet, tsdproxy provides that. Port `8124` on the LAN is
plain HTTP, so choosing LAN-only access at install time leaves the web
interface unusable.

The part that is easy to miss: the **phone** reports to
`fmd.<your-tailnet>.ts.net`, which only resolves while the Tailscale app is
running on the phone. Keep Tailscale always-on there — a lost phone with
Tailscale off reports nothing, however well this side is set up. The FMD app
can also be commanded by SMS, which does not depend on this server at all.

## The registration token

FMD Server only checks the token when one is set, and this unit always sets one.
Measured on 0.17.0: with `FMD_REGISTRATIONTOKEN` unset, a registration
carrying a wrong token is accepted; with it set, the same request answers
`401 Registration Token not valid`. The token matters only for **creating**
accounts — an existing account logs in with its own password.

## Update

The project is **pre-1.0, and says minor versions can introduce breaking
changes** — read the release notes before moving from 0.17 to 0.18, and back up
first. It lives on GitLab, so `install.ini` compares against the registry
there rather than a GitHub release page.

The `-alpine` variant, not the default Debian one or the smaller distroless,
because it is the one that carries `wget` — which `HealthCmd` needs, and
`Notify=healthy` needs `HealthCmd` (rule 14 of the conventions).

## Backup

The volume holds one SQLite database. It is ciphertext, so the backup is only
useful together with the account passwords.

## Remove

The tailnet node is not deregistered when an app is removed: do that in the Tailscale admin.

## Credits

[fmd-foss/fmd-server](https://gitlab.com/fmd-foss/fmd-server) — GPL-3.0-or-later

[Official documentation](https://fmd-foss.org/docs/fmd-server/overview)
