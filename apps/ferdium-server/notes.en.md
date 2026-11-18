In the Ferdium desktop app: **Settings → Ferdium account → Use custom server**, pointing at `https://ferdium.<your-tailnet>.ts.net`. Create your account, then set `IS_REGISTRATION_ENABLED=false` in the `.env` and run `qh ferdium-server --update --apply` so nobody else can.

The first start takes about 90 seconds (it installs and migrates before serving).
