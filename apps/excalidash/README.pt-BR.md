# ExcaliDash

<img src="https://cdn.jsdelivr.net/gh/homarr-labs/dashboard-icons/svg/excalidraw.svg" width="64" height="64" alt="">

**[🇺🇸 Read in English](./README.md)**

Excalidraw com onde guardar os desenhos: pastas, vários usuários, e links que
você compartilha por desenho em vez de por instância.

Dois containers — o frontend que você abre e o backend que guarda o banco
SQLite. O frontend requer o backend, então subir o `excalidash` sobe os dois.

## Primeiro acesso

Abra `http://<ip-do-host>:8016` ou `https://excalidash.<your-tailnet>.ts.net` e
crie a conta.

## Arquivos

```
excalidash.container           o frontend, e a unit que você sobe
excalidash-backend.container   a API e o banco
excalidash-net.network         a rede que os dois compartilham
.env.example                   ambiente
install.ini                    as receitas dos segredos
```

Dados em `~/.config/containers/volumes/excalidash/data`, na porta **8016**. O
`DATABASE_PROVIDER=sqlite` guarda tudo nesse diretório; o projeto também fala
Postgres, que este deploy não roda.

O frontend alcança o backend pelo nome da unit, via `BACKEND_URL` — a imagem
usa por padrão o hostname `backend`, que exigiria um container chamado assim.

## Entrar pelo Authentik

O padrão é `AUTH_MODE=local`: as contas ficam no ExcaliDash. Para usar o
[Authentik](../authentik/README.pt-BR.md), ponha `AUTH_MODE=hybrid` (os dois)
ou `oidc_enforced` (só o Authentik) e preencha `OIDC_ISSUER_URL`,
`OIDC_CLIENT_ID`, `OIDC_CLIENT_SECRET` e `OIDC_REDIRECT_URI` no `.env`.

## Atualizar

As duas imagens usam a mesma tag, e sobem juntas.

## Backup

Para os dois, empacota os dados, o `.env` e os segredos, e religa. Os segredos
importam aqui: restaurar o banco sem o mesmo `JWT_SECRET` desloga todo mundo.

## Créditos

[ExcaliDash](https://github.com/ZimengXiong/ExcaliDash) por
[ZimengXiong](https://github.com/ZimengXiong) — LGPL-3.0

Sobre o [Excalidraw](https://github.com/excalidraw/excalidraw) — MIT

[Documentação oficial](https://github.com/ZimengXiong/ExcaliDash#readme)
