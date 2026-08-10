# ExcaliDash

<img src="https://cdn.jsdelivr.net/gh/homarr-labs/dashboard-icons/svg/excalidraw.svg" width="64" height="64" alt="">

**[🇺🇸 Read in English](./README.md)**

Excalidraw com onde guardar os desenhos: pastas, vários usuários, e links que
você compartilha por desenho em vez de por instância.

Dois containers — o frontend que você abre e o backend que guarda o banco
SQLite. O frontend requer o backend, então subir o `excalidash` sobe os dois.

## Instalação

```bash
qh excalidash            # mostra o plano
qh excalidash --apply
```

Abra `http://<ip-do-host>:8016` ou `https://excalidash.<your-tailnet>.ts.net` e
crie a conta.

<details>
<summary><b>Instalação manual</b></summary>

```bash
mkdir -p ~/.config/containers/systemd/excalidash ~/.config/containers/env
mkdir -p ~/.config/containers/volumes/excalidash/data

openssl rand -hex 32 | podman secret create excalidash-jwt-secret -
openssl rand -hex 32 | podman secret create excalidash-csrf-secret -

wget -P ~/.config/containers/systemd/excalidash/ \
  https://raw.githubusercontent.com/wallacepnts/quadlet-homelab/main/apps/excalidash/excalidash.container \
  https://raw.githubusercontent.com/wallacepnts/quadlet-homelab/main/apps/excalidash/excalidash-backend.container \
  https://raw.githubusercontent.com/wallacepnts/quadlet-homelab/main/apps/excalidash/excalidash-net.network
wget -O ~/.config/containers/env/excalidash.env \
  https://raw.githubusercontent.com/wallacepnts/quadlet-homelab/main/apps/excalidash/.env.example

systemctl --user daemon-reload
systemctl --user start excalidash
```

</details>

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

```bash
qh excalidash --update --apply
```

Pinado em `0.5.1`. As duas imagens usam a mesma tag, e sobem juntas.

## Backup

```bash
qh excalidash --backup --apply --out ~/backups
```

Para os dois, empacota os dados, o `.env` e os segredos, e religa. Os segredos
importam aqui: restaurar o banco sem o mesmo `JWT_SECRET` desloga todo mundo.

Para restaurar, por cima dos dados atuais:

```bash
qh excalidash --restore ~/backups/excalidash-20260810-1200.tar.gz --apply
```

## Remover

```bash
qh excalidash --remove --apply           # para, mantém os dados
qh excalidash --remove --purge --apply   # e apaga volumes, segredos e .env
```

## Comandos

```bash
systemctl --user status excalidash
podman logs -f excalidash-backend
podman exec excalidash-backend node -e "require('http').get('http://127.0.0.1:8000/health', r => console.log(r.statusCode))"
```

## Créditos

[ExcaliDash](https://github.com/ZimengXiong/ExcaliDash) por
[ZimengXiong](https://github.com/ZimengXiong) — LGPL-3.0

Sobre o [Excalidraw](https://github.com/excalidraw/excalidraw) — MIT

[Documentação oficial](https://github.com/ZimengXiong/ExcaliDash#readme)
