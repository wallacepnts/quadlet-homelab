Depois, no Ferdium desktop: **Settings → Ferdium account → Use custom server**,
apontando para `https://ferdium.<your-tailnet>.ts.net`. Crie a sua conta,
depois ponha `IS_REGISTRATION_ENABLED=false` no `.env` e rode
`qh ferdium-server --update --apply` para que mais ninguém crie.

### O primeiro start é lento

O `TimeoutStartSec=300` não é folga: antes de servir qualquer coisa o
entrypoint instala o pnpm, clona as receitas e roda as migrações do banco. São
uns 90 segundos com o volume vazio, e o `HealthStartPeriod=180s` cobre isso.

### Backup

Para o serviço, empacota os dois volumes e o `.env`, e sobe de novo. As
receitas são um clone git e voltariam sozinhas, mas o banco e as chaves são a
conta em si.
