# Beaver Habits

<img src="https://avatars.githubusercontent.com/u/6239652?s=200&v=4" width="64" height="64" alt="">

**[🇺🇸 Read in English](./README.md)**

Acompanhamento de hábitos sem metas: você marca o dia e segue. A graça do
projeto é o que ele deixa de fora — nenhuma meta para falhar, nenhuma tela de
culpa.

## Primeiro acesso

Abra `http://<ip-do-host>:8015` ou `https://habits.<your-tailnet>.ts.net` e
crie a conta. **Quem alcançar o endereço também pode criar uma** — assim que a
sua existir, ponha `MAX_USER_COUNT=1` no `.env` e reinicie.

## Arquivos

```
beaverhabits.container   unit
.env.example             ambiente
```

Dados em `~/.config/containers/volumes/beaverhabits/data`, na porta **8015**.
O `HABITS_STORAGE=USER_DISK` guarda os hábitos como JSON nesse diretório — sem
banco de dados, então o backup é o diretório.

## API

Existe uma API REST, e é com ela que falam o switch do Home Assistant, o
plugin do Stream Deck e o atalho do iPhone listados no README do projeto. Veja
o [guia da API](https://github.com/daya0576/beaverhabits/wiki/Beaver-Habit-Tracker-API-How%E2%80%90to-Guide).

## Backup

Para o serviço, empacota os dados e o `.env`, e religa.

## Créditos

[Beaver Habit Tracker](https://github.com/daya0576/beaverhabits) por
[daya0576](https://github.com/daya0576) — BSD-3-Clause

[Documentação oficial](https://github.com/daya0576/beaverhabits/wiki)
