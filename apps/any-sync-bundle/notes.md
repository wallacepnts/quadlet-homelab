Open `http://<host-ip>:33010` or `https://any-sync.<your-tailnet>.ts.net`.

### Connecting the Anytype app

The first start writes `client-config.yml` into the data volume — that is what
points an Anytype client here instead of at the company's cloud. Import it in
the app, following [Anytype's
instructions](https://doc.anytype.io/anytype-docs/advanced/data-and-security/self-hosting/self-hosted#how-to-switch-to-a-self-hosted-network).

```bash
cat ~/.config/containers/volumes/any-sync-bundle/data/client-config.yml
```

It is regenerated on every start, so it needs no backup. `bundle-config.yml`,
next to it, is the opposite: it carries the private keys, and losing it means
losing the network.

### Backup

For the scheduled copy, Zerobyte has to find this service stopped too — its
backup hook does that, with
`any-sync-bundle` in the allowlist.
