# Beaver Habits

<img src="https://avatars.githubusercontent.com/u/6239652?s=200&v=4" width="64" height="64" alt="">

**[🇧🇷 Leia em português](./README.pt-BR.md)**

Habit tracking with no goals: you mark the day and move on. The point of the
project is what it leaves out — no targets to miss, no guilt screen.

## First run

Open `http://<host-ip>:8015` or `https://habits.<your-tailnet>.ts.net` and
create the account. **Anyone who reaches the address can create one too** —
set `MAX_USER_COUNT=1` in the `.env` once yours exists, and restart.

## Files

```
beaverhabits.container   unit
.env.example             environment
```

Data in `~/.config/containers/volumes/beaverhabits/data`, on port **8015**.
`HABITS_STORAGE=USER_DISK` keeps the habits as JSON in that directory — no
database, so the backup is the directory.

## API

There is a REST API, which is what the Home Assistant switch, the Stream Deck
plugin and the Apple Shortcut in the project's README talk to. See the
[API guide](https://github.com/daya0576/beaverhabits/wiki/Beaver-Habit-Tracker-API-How%E2%80%90to-Guide).

## Backup

It stops the service, packs the data and the `.env`, and starts it again.

## Credits

[Beaver Habit Tracker](https://github.com/daya0576/beaverhabits) by
[daya0576](https://github.com/daya0576) — BSD-3-Clause

[Official documentation](https://github.com/daya0576/beaverhabits/wiki)
