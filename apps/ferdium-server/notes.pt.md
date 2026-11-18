No app Ferdium do desktop: **Configurações → Conta Ferdium → Usar servidor personalizado**, apontando para `https://ferdium.<your-tailnet>.ts.net`. Crie a conta, depois coloque `IS_REGISTRATION_ENABLED=false` no `.env` e rode `qh ferdium-server --update --apply` para que ninguém mais crie.

O primeiro início leva uns 90 segundos (ele instala e migra antes de servir).
