Abra `http://<ip-do-host>:8016` ou `https://excalidash.<your-tailnet>.ts.net` e
crie a conta.

### Entrar pelo Authentik

O padrão é `AUTH_MODE=local`: as contas ficam no ExcaliDash. Para usar o
Authentik, ponha `AUTH_MODE=hybrid` (os dois)
ou `oidc_enforced` (só o Authentik) e preencha `OIDC_ISSUER_URL`,
`OIDC_CLIENT_ID`, `OIDC_CLIENT_SECRET` e `OIDC_REDIRECT_URI` no `.env`.

### Atualizar

As duas imagens usam a mesma tag, e sobem juntas.

### Backup

Para os dois, empacota os dados, o `.env` e os segredos, e religa. Os segredos
importam aqui: restaurar o banco sem o mesmo `JWT_SECRET` desloga todo mundo.
