Then, in the Ferdium desktop app: **Settings → Ferdium account → Use custom
server**, pointing at `https://ferdium.<your-tailnet>.ts.net`. Create your
account, then set `IS_REGISTRATION_ENABLED=false` in the `.env` and run
`qh ferdium-server --update --apply` so nobody else can.

### The first start is slow

`TimeoutStartSec=300` is not padding: before serving anything the entrypoint
installs pnpm, clones the recipes and runs the database migrations. Around 90
seconds on a cold volume, and `HealthStartPeriod=180s` covers it.

### Backup

Stops it, packs both volumes and the `.env`, starts it again. The recipes are a
git clone and would come back on their own, but the database and the keys are
the account itself.
