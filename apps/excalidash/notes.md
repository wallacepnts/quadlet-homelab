Open `http://<host-ip>:8016` or `https://excalidash.<your-tailnet>.ts.net` and
create the account.

### Signing in with Authentik

`AUTH_MODE=local` ships by default: accounts live in ExcaliDash. To use
[Authentik](../authentik) instead, set `AUTH_MODE=hybrid` (both) or
`oidc_enforced` (only Authentik) and fill `OIDC_ISSUER_URL`, `OIDC_CLIENT_ID`,
`OIDC_CLIENT_SECRET` and `OIDC_REDIRECT_URI` in the `.env`.

### Update

Both images carry the same tag, and they are bumped together.

### Backup

It stops both, packs the data, the `.env` and the secrets, and starts them
again. The secrets matter here: restoring the database without the same
`JWT_SECRET` logs everyone out.
