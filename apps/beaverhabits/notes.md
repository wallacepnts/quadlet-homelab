Open `http://<host-ip>:8015` or `https://habits.<your-tailnet>.ts.net` and
create the account. **Anyone who reaches the address can create one too** —
set `MAX_USER_COUNT=1` in the `.env` once yours exists, and restart.

### API

There is a REST API, which is what the Home Assistant switch, the Stream Deck
plugin and the Apple Shortcut in the project's README talk to. See the
[API guide](https://github.com/daya0576/beaverhabits/wiki/Beaver-Habit-Tracker-API-How%E2%80%90to-Guide).

### Backup

It stops the service, packs the data and the `.env`, and starts it again.
