# any-sync-bundle

<img src="https://cdn.jsdelivr.net/gh/homarr-labs/dashboard-icons/svg/anytype.svg" width="64" height="64" alt="">

**[🇧🇷 Leia em português](./README.pt-BR.md)**

The Any-Sync protocol backend, which syncs Anytype's data across devices without relying on the company's cloud.

## First run

Open `http://<host-ip>:33010` or `https://any-sync.<your-tailnet>.ts.net`.

## Files

```
any-sync-bundle.container   unit
.env.example                environment
```

## Connecting the Anytype app

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

## Backup

For the scheduled copy, Zerobyte has to find this service stopped too — its
[backup hook](../zerobyte/README.md#backup-hook) does that, with
`any-sync-bundle` in the allowlist.

## Remove

The tailnet node is not deregistered when an app is removed: do that in the Tailscale admin.

## Credits

[grishy/any-sync-bundle](https://github.com/grishy/any-sync-bundle) — MIT

[Official documentation](https://github.com/grishy/any-sync-bundle#readme)
