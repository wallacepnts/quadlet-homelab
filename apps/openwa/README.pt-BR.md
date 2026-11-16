# OpenWA

<img src="https://cdn.jsdelivr.net/gh/rmyndharis/OpenWA@main/docs/logo/openwa.svg" width="64" height="64" alt="">

**[🇺🇸 Read in English](./README.md)**

Gateway de API do WhatsApp — transforma a conta em REST + webhooks, pro n8n e o Home Assistant usarem.

## Primeiro acesso

Abrir `http://<ip-do-host>:2785` ou `https://openwa.<your-tailnet>.ts.net`.

## Arquivos

```
openwa.container
.env.example
install.ini
```

## Mudança de comportamento na 0.15.0

Enquanto o WhatsApp Web recarrega a própria página — medido em torno de cinco
minutos depois de um pareamento novo — todas as rotas do engine respondem `409`
em vez do `500` cru de antes. Cliente que tenta de novo em 5xx e desiste em 4xx
vai falhar onde antes se recuperava, então vale conferir os fluxos que chamam
essa API.

## Remover

O nó da tailnet não é desregistrado ao remover um app: isso é no admin do Tailscale.

## Créditos

[rmyndharis/OpenWA](https://github.com/rmyndharis/OpenWA) — MIT

[Documentação oficial](https://www.open-wa.org)
