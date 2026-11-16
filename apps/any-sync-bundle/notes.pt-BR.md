Abrir `http://<ip-do-host>:33010` ou `https://any-sync.<your-tailnet>.ts.net`.

### Conectando o app do Anytype

O primeiro start escreve o `client-config.yml` no volume de dados — é ele que
aponta um cliente Anytype para cá em vez da nuvem da empresa. Importe no app
seguindo as [instruções do
Anytype](https://doc.anytype.io/anytype-docs/advanced/data-and-security/self-hosting/self-hosted#how-to-switch-to-a-self-hosted-network).

```bash
cat ~/.config/containers/volumes/any-sync-bundle/data/client-config.yml
```

Ele é regerado a cada start, então não precisa de backup. O
`bundle-config.yml`, ao lado, é o oposto: carrega as chaves privadas, e
perdê-lo é perder a rede.

### Backup

Para a cópia agendada, o Zerobyte também precisa encontrar este serviço
parado — o gancho de backup
faz isso, com `any-sync-bundle` na allowlist.
