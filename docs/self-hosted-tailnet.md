# A tailnet of your own

Replacing Tailscale's control plane with [headscale](../apps/headscale), its
interface with [headplane](../apps/headplane), and the certificates with
[Caddy](../apps/caddy) signing for names that [AdGuard Home](../apps/adguardhome)
resolves.

Nothing here touches the Tailscale you already run. The four services stand up
beside it, and you switch clients over when you are convinced — or never.

## What each piece is for

| | |
| --- | --- |
| **headscale** | hands out keys, decides who talks to whom, answers MagicDNS |
| **headplane** | the screen for the above |
| **Caddy** | HTTPS for `*.qh`, signed by a CA it runs itself |
| **AdGuard Home** | answers `*.qh` with the host's address |

The last two exist because of one fact: without a domain you own, nobody will
issue you a public certificate, and nothing resolves a name you invented.

## 1. The services

Order matters — headplane mounts headscale's configuration, so a bind mount
of a directory that does not exist would fail:

```bash
qh headscale --apply
qh headplane --apply
qh caddy --apply
qh adguardhome --apply
```

## 2. Two name spaces, not one

headscale refuses to start when `server_url` sits inside `base_domain`:

```
server_url cannot be part of base_domain in a way that could make the
DERP and headscale server unreachable
```

A node called `headscale` would shadow the server. So they are kept apart, and
this is what the shipped `config.yaml` uses:

- `server_url: https://headscale.qh` — the control plane
- `base_domain: rede.qh` — what MagicDNS appends, so a laptop answers to
  `laptop.rede.qh`

## 3. Routes in Caddy

In `~/.config/containers/volumes/caddy/config/Caddyfile`:

```
headscale.qh {
	reverse_proxy headscale:8080
}

headplane.qh {
	reverse_proxy headplane:3000
}
```

```bash
podman exec caddy caddy reload --config /etc/caddy/Caddyfile
```

Container names, not addresses: everything shares `tsdproxy-net`, so Caddy
reaches each service by name with nothing published on the LAN.

## 4. AdGuard answers the names

The first start only serves the setup wizard — the DNS server does not come up
until it is configured. Through its API, from a container on the same network:

```bash
curl -X POST http://adguardhome:3000/control/install/configure \
  -H 'Content-Type: application/json' \
  -d '{"web":{"ip":"0.0.0.0","port":3000},"dns":{"ip":"0.0.0.0","port":53},
       "username":"admin","password":"<yours>"}'
```

Then one rewrite sends every `.qh` name at the host:

```bash
curl -u admin:<yours> -X POST http://adguardhome:3000/control/rewrite/add \
  -H 'Content-Type: application/json' \
  -d '{"domain":"*.qh","answer":"<host tailscale ip>"}'
```

Check it:

```bash
dig +short @127.0.0.1 -p 5335 headscale.qh
```

**The port is the catch.** Rootless Podman cannot bind 53, so AdGuard listens
on **5335**, and Tailscale's DNS settings take an address without a port. Until
that is solved, name resolution works for whoever points at `5335` explicitly —
which is enough to test, and not enough for phones. Two ways out: lower the
floor on the host once,

```bash
echo 'net.ipv4.ip_unprivileged_port_start=53' | sudo tee /etc/sysctl.d/50-unprivileged-ports.conf
sudo sysctl --system
```

and publish `53:53`, or skip AdGuard for names entirely and put them in
headscale's own `dns.extra_records`, which its clients receive with no resolver
in the middle.

## 5. Trust the certificate authority

Every device that will open these names has to trust Caddy's CA once:

```bash
find ~/.config/containers/volumes/caddy/data -name root.crt
# openSUSE
sudo cp <that file> /etc/pki/trust/anchors/caddy-local.crt
sudo update-ca-certificates
```

This includes the machine running `tailscale`: the client validates TLS against
the control plane, so without the CA it will not log in.

## 6. A client

```bash
podman exec headscale /ko-app/headscale users create casa
podman exec headscale /ko-app/headscale preauthkeys create --user casa --expiration 24h

sudo tailscale up --login-server https://headscale.qh:8443 --authkey <key>
```

The port is in the URL because Caddy publishes 8443, for the same reason
AdGuard publishes 5335. With the sysctl above and `443:443` in the unit, it
becomes `https://headscale.qh`.

`headscale apikeys create --expiration 90d` gives you the key headplane asks
for at sign-in.

## What is still missing to leave the house

Everything above works on your own network. For a device on mobile data to
reach `server_url`, it needs a public address and an open port, or headscale on
a VPS. Without that, the tailnet coordinates at home and nowhere else.

The relays are the other half: with `derp.server.enabled: false`, as shipped,
NAT traversal falls back to Tailscale's public DERP servers — their
infrastructure, carrying no plaintext. The embedded DERP makes it yours and
needs a reachable UDP port.

## Verified

Measured on the host this was written from, with the four services healthy:

```
dig @127.0.0.1 -p 5335 headscale.qh   ->  100.x.y.z
https://headscale.qh:8443/health      ->  {"status":"pass"}
https://headplane.qh:8443/admin/      ->  302
```
