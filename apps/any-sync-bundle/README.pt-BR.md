# any-sync-bundle

<img src="https://cdn.jsdelivr.net/gh/homarr-labs/dashboard-icons/svg/anytype.svg" width="64" height="64" alt="">

**[🇺🇸 Read in English](./README.md)**

Backend do protocolo Any-Sync, que sincroniza os dados do Anytype entre dispositivos sem depender da nuvem da empresa.

## Primeiro acesso

Abrir `http://<ip-do-host>:33010` ou `https://any-sync.<your-tailnet>.ts.net`.

## Arquivos

```
any-sync-bundle.container   unit
.env.example                ambiente
```

## Conectando o app do Anytype

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

## Backup

Para a cópia agendada, o Zerobyte também precisa encontrar este serviço
parado — o [gancho de backup](../zerobyte/README.pt-BR.md#gancho-de-backup)
faz isso, com `any-sync-bundle` na allowlist.

## Remover

O nó da tailnet não é desregistrado ao remover um app: isso é no admin do Tailscale.

## Créditos

[grishy/any-sync-bundle](https://github.com/grishy/any-sync-bundle) — MIT

[Documentação oficial](https://github.com/grishy/any-sync-bundle#readme)
