# Monica

<img src="https://cdn.jsdelivr.net/gh/homarr-labs/dashboard-icons/svg/monica.svg" width="64" height="64" alt="">

**[🇺🇸 Read in English](./README.md)**

CRM pessoal — histórico de relacionamentos, contatos, lembretes.

## Primeiro acesso

Abrir `http://<ip-do-host>:9092` ou `https://monica.<your-tailnet>.ts.net`.

## Arquivos

```
monica.container
.env.example
install.ini
```

## Atualizar

Por digest, porque o `monica-next` não publica imagem com versão — só `main` e
`main-fpm`, reconstruídas conforme o branch anda. O digest congela um build dela.

## Remover

O nó da tailnet não é desregistrado ao remover um app: isso é no admin do Tailscale.

## Créditos

[monicahq/monica](https://github.com/monicahq/monica) — AGPL-3.0

[Documentação oficial](https://beta.monicahq.com)
