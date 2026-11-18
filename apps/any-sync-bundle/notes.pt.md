O primeiro início grava `client-config.yml` no volume de dados: é ele que aponta o cliente do Anytype para cá em vez de para a nuvem da empresa. Importe-o no app, seguindo as [instruções do Anytype](https://doc.anytype.io/anytype-docs/advanced/data-and-security/self-hosting/self-hosted#how-to-switch-to-a-self-hosted-network).

```bash
cat ~/.config/containers/volumes/any-sync-bundle/data/client-config.yml
```

Guarde uma cópia do `bundle-config.yml`, ao lado dele: tem as chaves privadas, e perdê-lo é perder a rede.
