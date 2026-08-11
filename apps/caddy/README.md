# Caddy

<img src="https://cdn.jsdelivr.net/gh/homarr-labs/dashboard-icons/svg/caddy.svg" width="64" height="64" alt="">

**[🇧🇷 Leia em português](./README.pt-BR.md)**

A reverse proxy that gives your services HTTPS under names you choose, signed
by a certificate authority it runs itself. No domain to buy, no Let's Encrypt,
nothing published on the internet.

It is the alternative to [tsdproxy](../tsdproxy) for people who would rather
own the whole chain: one certificate authority here, one certificate per name,
and no control plane deciding whether you get one.

## Install

```bash
qh caddy            # shows the plan
qh caddy --apply
```

Then add a route per service in
`~/.config/containers/volumes/caddy/config/Caddyfile` and reload:

```
faved.casa {
	reverse_proxy faved:80
}
```

```bash
podman exec caddy caddy reload --config /etc/caddy/Caddyfile
```

<details>
<summary><b>Manual install (advanced)</b></summary>

```bash
mkdir -p ~/.config/containers/systemd
mkdir -p ~/.config/containers/volumes/caddy/{config,data,state}

wget -P ~/.config/containers/systemd/ \
  https://raw.githubusercontent.com/wallacepnts/quadlet-homelab/main/apps/caddy/caddy.container
wget -O ~/.config/containers/volumes/caddy/config/Caddyfile \
  https://raw.githubusercontent.com/wallacepnts/quadlet-homelab/main/apps/caddy/config/Caddyfile

systemctl --user daemon-reload
systemctl --user start caddy
```

</details>

## Files

```
caddy.container    unit
config/Caddyfile   the routes, into the volume
install.ini
```

`data/` holds the certificate authority and the certificates it issues — the
folder to back up, since losing it means every device has to trust a new CA.
`state/` is Caddy's own bookkeeping.

## The two things that are not automatic

**Each device has to trust the CA once.** That is the price of not having a
domain. The root certificate is at
`~/.config/containers/volumes/caddy/data/caddy/pki/authorities/local/root.crt`:

```bash
# openSUSE
sudo cp root.crt /etc/pki/trust/anchors/caddy-local.crt && sudo update-ca-certificates
```

On Android and iOS it is installed through the settings, and on iOS it also has
to be enabled under **Certificate Trust Settings** — two different screens.

**The names have to resolve.** Nothing knows what `faved.casa` is. Either an
entry per device in `/etc/hosts`, or a resolver everyone already uses — the
[adguardhome](../adguardhome) in this repository can answer `*.casa` with the
host's address, and the tailnet can be pointed at it as a split DNS.

## Ports

Rootless Podman refuses to publish a port below 1024, so the unit publishes
**8443** and **8114**, and the URLs carry the port. To drop it, raise the floor
on the host once and change the two `PublishPort` lines to `443:443` and
`80:80`:

```bash
echo 'net.ipv4.ip_unprivileged_port_start=80' | sudo tee /etc/sysctl.d/50-unprivileged-ports.conf
sudo sysctl --system
```

## Hardening

`ReadOnly=true` with every capability dropped except `NET_BIND_SERVICE`, which
it needs because it listens on 443 **inside** the container. Measured serving a
real request through to another container.

One error appears in the log and is harmless:

```
pki.ca.local  failed to install root certificate
```

Caddy tries to add its own CA to the container's trust store and cannot,
because it has no capability to write there. The certificate it serves is the
same either way — and a container that cannot rewrite its own trust store is
the behaviour to want.

## Update

```bash
qh caddy --update --apply
```

Pinned to `2.11.4-alpine`.

## Backup

```bash
qh caddy --backup --apply --out ~/backups
```

The `data/` folder is the one that matters: it carries the CA. Restoring it
means the devices that already trust you keep trusting you.

## Remove

```bash
qh caddy --remove --apply           # stops it, keeps the CA
qh caddy --remove --purge --apply   # and deletes the CA and every certificate
```

`--purge` invalidates every device that trusts the current CA.

## Commands

```bash
systemctl --user status caddy
podman logs -f caddy

podman exec caddy caddy validate --config /etc/caddy/Caddyfile
podman exec caddy caddy reload --config /etc/caddy/Caddyfile
```

## Credits

[caddyserver/caddy](https://github.com/caddyserver/caddy) — Apache-2.0.

[Official documentation](https://caddyserver.com/docs/)
