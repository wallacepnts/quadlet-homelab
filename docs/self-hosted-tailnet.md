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
until it is configured. Do it in the browser, at
`https://adguardhome.<your-tailnet>.ts.net` or `http://<host-ip>:3006`, and
keep two answers in mind: the admin interface has to stay on port **3000**, and
the DNS server on **53**. Those are the ports the unit maps.

Then one rewrite, under **Filters → DNS rewrites**, sends every name at the
host:

| Domain | Answer |
| --- | --- |
| `*.qh` | the host's tailnet address |
| `qh` | the same |

The wildcard is the point: a service added next month resolves without touching
DNS again. Only Caddy needs a new route.

### Which address it listens on

Not `0.0.0.0`. That address includes the container network's own gateway, where
`aardvark-dns` answers, and publishing over it takes down name resolution
*between every container on the host* — measured here, and it broke
`zerobyte → ntfy`, `caddy → headscale` and everything else at once.

So the unit binds one address, and takes it from `environment.d` (rule 19 of
the conventions), the same way `${TAILNET}` works:

```bash
echo 'AGH_DNS_BIND=100.x.y.z' > ~/.config/environment.d/adguardhome.conf
systemctl --user set-environment AGH_DNS_BIND=100.x.y.z
qh adguardhome --update --apply
```

Binding port 53 at all needs the sysctl from the previous step. Without it,
leave the unit on `5335` and use the `/etc/hosts` route below.

### Handing the resolver to every device

Split DNS: only `.qh` goes to AdGuard, everything else keeps working as it did.
It is what makes the setup usable from a phone, and the reason AdGuard binds a
tailnet address rather than a LAN one.

**Once the clients are on headscale**, it is in its own `config.yaml` and needs
a restart:

```yaml
dns:
  nameservers:
    split:
      qh:
        - 100.x.y.z
```

**While they are still on Tailscale** — which is the case until you switch the
last client — the same setting lives in their admin, because that is who hands
your devices their DNS today:

1. **DNS → Nameservers → Add nameserver → Custom**
2. address: the host's tailnet address, the same one in `AGH_DNS_BIND`
3. tick **Restrict to domain** and put `qh`

The two are the same idea in two control planes, and during the migration you
will want both: a device that has moved reads headscale's, one that has not
reads Tailscale's.

Check it:

```bash
dig +short @100.x.y.z karakeep.qh
```

### The one-machine shortcut

Until the split DNS is set, `/etc/hosts` does the same job for one computer:

```bash
echo "100.x.y.z karakeep.qh homepage.qh" | sudo tee -a /etc/hosts
```

Delete it afterwards. A partial `/etc/hosts` beats DNS and wins, which gives
the worst outcome: three services resolving, the rest not, for no visible
reason.

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
