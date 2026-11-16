# Vaultwarden

<img src="https://cdn.jsdelivr.net/gh/homarr-labs/dashboard-icons/png/vaultwarden.png" width="64" height="64" alt="">

**[🇺🇸 Read in English](./README.md)**

Cofre de senhas compatível com o protocolo do Bitwarden, leve o bastante pra rodar em qualquer lugar.

## Primeiro acesso

Abrir `https://vaultwarden.<your-tailnet>.ts.net`.

O cofre é alcançável só pela tailnet. O `PublishPort=8082:80` vem comentado na
unit: publicar a porta faria ele atender também a qualquer um na LAN, que é
porta mais larga do que um cofre de senhas precisa. Descomente se quiser o
`http://<ip-do-host>:8082` também.

## Arquivos

```
vaultwarden.container
.env.example
install.ini
```

## Remover

O nó da tailnet não é desregistrado ao remover um app: isso é no admin do Tailscale.

## Créditos

[dani-garcia/vaultwarden](https://github.com/dani-garcia/vaultwarden) — AGPL-3.0.

[Documentação oficial](https://github.com/dani-garcia/vaultwarden/wiki)
