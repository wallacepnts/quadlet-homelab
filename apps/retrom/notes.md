Put the games under `~/.config/containers/volumes/retrom/library`, in the
[folder structure Retrom
expects](https://github.com/JMBeresford/retrom/wiki/Library-Structure), then
open `http://<host-ip>:5101` or `https://retrom.<your-tailnet>.ts.net`.

**The first start takes about 90 seconds** — it downloads EmulatorJS and runs
the database migrations. `TimeoutStartSec=300` and a 180 second health start
period are there for that; a restart afterwards is quick.

### Metadata

Cover art and descriptions come from IGDB or SteamGridDB, and both want an API
key. Without one the library still works, listed by filename. The keys are set
from the client, not here — see [Metadata
Providers](https://github.com/JMBeresford/retrom/wiki/Metadata-Providers).

### Backup

It stops the service, packs the three volumes and the `.env`, and starts it
again. Cold on purpose: Retrom carries an embedded PostgreSQL, and copying it
live gives an archive that only fails when you restore it. That is also why
`stop` is the mode to use if you add it to
[Zerobyte's backup hook](../zerobyte).

### Remove

`--purge` deletes the library too — the games are in a volume like everything
else.
