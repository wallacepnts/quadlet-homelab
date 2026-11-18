The first start writes `client-config.yml` into the data volume: that is what points an Anytype client here instead of at the company's cloud. Import it in the app, following [Anytype's instructions](https://doc.anytype.io/anytype-docs/advanced/data-and-security/self-hosting/self-hosted#how-to-switch-to-a-self-hosted-network).

```bash
cat ~/.config/containers/volumes/any-sync-bundle/data/client-config.yml
```

Back up `bundle-config.yml`, next to it: it carries the private keys, and losing it means losing the network.
