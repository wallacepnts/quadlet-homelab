Abra `http://<ip-do-host>:8015` ou `https://habits.<your-tailnet>.ts.net` e
crie a conta. **Quem alcançar o endereço também pode criar uma** — assim que a
sua existir, ponha `MAX_USER_COUNT=1` no `.env` e reinicie.

### API

Existe uma API REST, e é com ela que falam o switch do Home Assistant, o
plugin do Stream Deck e o atalho do iPhone listados no README do projeto. Veja
o [guia da API](https://github.com/daya0576/beaverhabits/wiki/Beaver-Habit-Tracker-API-How%E2%80%90to-Guide).

### Backup

Para o serviço, empacota os dados e o `.env`, e religa.
