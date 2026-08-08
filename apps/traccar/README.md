# Traccar — Podman Quadlet (rootless)

**[🇧🇷 Leia em português](./README.pt-BR.md)**

Deploy do [Traccar](https://github.com/traccar/traccar) (plataforma de
rastreamento de GPS) via Podman Quadlet, usando a imagem oficial
`docker.io/traccar/traccar`.

A live map, trip history, geofences, reports and alerts —
com o app oficial no celular ou com rastreador dedicado. Convive com o
[OwnTracks](../owntracks/), which is simpler and MQTT-native; Traccar has
the reporting and geofencing side that OwnTracks does not.

## Architecture

A single container, JVM, with an **embedded H2 database** in `data/` —
Traccar's default, with no separate database service
([rule 22](../../docs/conventions.md)).

It takes this repository's strongest hardening level (`ReadOnly=true`,
`DropCapability=ALL`, `User=1000`), with one detail that only turned up
testando: **`podman diff` mostra que o Traccar cria `/opt/traccar/override`
at start**, and without a `Tmpfs=` there `ReadOnly` takes the service down.
It is where frontend overrides live — disposable content.

### Portas

| Host port | What for |
| --- | --- |
| `8099` | interface web (8082 dentro do container) |
| `5056` | protocolo OsmAnd, TCP e UDP (5055 dentro) |

The host's 5055 already belongs to [seerr](../media-stack/), so the protocol
goes out on **5056**. In the Traccar Client app, enter port 5056 alongside the
address.

O Traccar fala ~150 protocolos, cada um numa porta entre 5000 e 5150. A
the official image tells you to publish the whole range; here only the
OsmAnd one is published, which is what the official app uses. A dedicated
tracker from another brand
precisa da porta correspondente adicionada na unit.

## Files

```
traccar.container      # main unit
traccar.xml.example    # config — banco H2 e porta do protocolo
```

## Installation

```bash
python3 install.py traccar            # dry-run: shows what it will do
python3 install.py traccar --apply
```

For the local network only, `--access local`; on the tailnet and the LAN,
`--access both`. Adding `--href-local` points the dashboard link at the LAN.
The script creates the directories, writes the `.env`, generates the secrets,
fixes the volumes' ownership, starts the service and prints the address at the
end — see [Installing and operating](../../docs/installing.md).



<details>
<summary><b>Manual installation</b> (advanced) — the same steps, one at a time</summary>


```bash
# 1. Download the unit (no need to clone the repository)
mkdir -p ~/.config/containers/systemd
wget -P ~/.config/containers/systemd/ \
  https://raw.githubusercontent.com/wallacepnts/quadlet-homelab/main/apps/traccar/traccar.container

# 2. Directories, with the owner matching the unit's User=1000
mkdir -p ~/.config/containers/volumes/traccar/{data,logs,conf}

# 3. Config — it has to EXIST before the start (it is a file bind mount; if
#    it does not, Podman creates a directory instead and Traccar breaks)
wget -O ~/.config/containers/volumes/traccar/conf/traccar.xml \
  https://raw.githubusercontent.com/wallacepnts/quadlet-homelab/main/apps/traccar/traccar.xml.example

podman unshare chown -R 1000:1000 ~/.config/containers/volumes/traccar

# 4. Start it
systemctl --user daemon-reload
systemctl --user start traccar
```

</details>

## Creating the first user

**Traccar no longer has a default admin.** Old versions created
`admin`/`admin`; current ones create nobody, and the first user
cadastrado vira administrador.

And there is a trap: **`web.registration` is not a Traccar configuration
key.** It circulates in tutorials, but Traccar ignores it — the only key by
that name in `Keys.java` is `openid.allowRegistration`. The
flag de cadastro mora **no banco**, na linha da tabela `tc_servers`, e
starts off. Touching the XML after the first start changes nothing.

That is safe by default, and the bootstrap works like this (tested):

```bash
# With ZERO users, the POST is open and the first one becomes admin
curl -X POST http://127.0.0.1:8099/api/users \
  -H 'Content-Type: application/json' \
  -d '{"name":"Seu Nome","email":"voce@exemplo.com","password":"SUA-SENHA"}'
```

A partir do segundo, a mesma chamada responde `SecurityException:
Registration disabled`. To open signup deliberately, do it in the interface
itself, logged in as admin: Settings → Server → Registration.

Open `http://<host-ip>:8099` (ou via [tsdproxy](../tsdproxy/) em
`https://traccar.<your-tailnet>.ts.net`).

## Ligando o celular

App **Traccar Client** (Android/iOS):

| Campo | Valor |
| --- | --- |
| Address | `<host-ip>` or the tailnet name |
| Porta | `5056` |
| Identifier | the same one you register as the device's "identifier" in the web UI |

Register the device in the web interface first (the `+` button in the list
of
dispositivos), usando exatamente o identificador do app.

## Auto-update

No `AutoUpdate=` — an explicit tag (`6.14.5`), bumped by hand
(rule 9 of the [conventions](../../docs/conventions.md)). Position history is real data and H2 migrates its schema between versions:
back up first.

## Backup & recovery

```bash
systemctl --user stop traccar
tar -czf traccar-backup-$(date +%Y%m%d-%H%M%S).tar.gz \
  -C ~/.config/containers/volumes traccar
systemctl --user start traccar
```

`data/database.mv.db` is the whole database (users, devices, positions).
`logs/` is disposable.

## Useful commands

```bash
systemctl --user status traccar
podman logs -f traccar
curl -s http://127.0.0.1:8099/api/server | python3 -m json.tool
```

## Credits

Quadlet deploy based on [Traccar](https://github.com/traccar/traccar)
de [Anton Tananaev](https://github.com/tananaev) (Apache-2.0).
