# any-sync-bundle — Podman Quadlet (rootless)

**[🇧🇷 Leia em português](./README.pt-BR.md)**

An [any-sync-bundle](https://github.com/grishy/any-sync-bundle) (Anytype's
self-hosted backend) deploy via Podman Quadlet, in **AIO** mode (all-in-one —
migrated from the official `compose.aio.yml`: MongoDB and Redis embedded in
the same image and container, no longer external). Tested on rootless Podman +
systemd --user (openSUSE Tumbleweed, uid 1000), but the `.container` files are
portable to any Linux with rootless Podman + systemd.

Out of scope here (they exist in the original project but are not ported): S3
storage (`compose.s3.yml`, MinIO) and a Traefik reverse proxy
(`compose.traefik.yml`) — this setup exposes it through Tailscale/tsdproxy
instead of Traefik (see the dedicated section).

## Architecture

A single container. The AIO image (**without** the modular variant's
`-minimal` suffix) already embeds MongoDB 8.0 and Redis Stack — any-sync-bundle's
own Go binary starts both as child processes (`start-all-in-one` rather than
`start-bundle`), all listening only on `127.0.0.1` inside the container. It
exposes `33010/tcp` (yamux) and `33020/udp` (QUIC) to the outside world;
Mongo and Redis never leave the container.

A single `/data:Z` volume holds everything — the image organises the
subdirectories itself:

```
/data/
├── bundle-config.yml   # the node's identity (peerId/peerKey/signingKey)
├── client-config.yml   # regenerated on every start, needs no backup
├── storage/            # the bundle's data (badger)
├── mongo/               # the embedded MongoDB's dbpath
└── redis/               # the embedded Redis's dir
```

**Unlike the modular mode** (originally used here: no Postgres, Mongo and
Redis in separate containers, a dedicated Podman network, `Requires=`/`After=`
between units) — switched at the user's request. Fewer moving parts (1
container instead of 3 plus a network), but it **still requires AVX** on the
CPU (the embedded Mongo is also 5.0+) and **does not allow pinning Mongo's
version separately** — that comes fixed inside any-sync-bundle's own image.
See the "Variants" section for when that matters.

## Files

```
any-sync-bundle.container   # AIO — the server plus embedded Mongo and Redis
```

## Prerequisites

- Rootless Podman with systemd `--user` working (`systemctl --user status`)
- `loginctl enable-linger <user>` — essential on a server, otherwise the
  services disappear when the login session ends
- Check the CPU's AVX support (Mongo 5.0+ requires it, embedded included):
  `grep -m1 avx /proc/cpuinfo` — without AVX, this AIO deploy does not work
  (there is no non-AVX variant for the embedded Mongo; see the Variants
  section)
- The firewall allowing TCP 33010 and UDP 33020 (`firewall-cmd`, `ufw`,
  `iptables` depending on the distro) — without that, clients outside the host
  cannot connect even with the container running correctly

## Installation

```bash
python3 install.py any-sync-bundle            # dry-run: shows what it will do
python3 install.py any-sync-bundle --apply
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
mkdir -p ~/.config/containers/systemd/any-sync
wget -P ~/.config/containers/systemd/any-sync/ \
  https://raw.githubusercontent.com/wallacepnts/quadlet-homelab/main/apps/any-sync-bundle/any-sync-bundle.container

# 2. Data directory — a Podman bind mount does not create the host's
#    directory by itself (unlike docker compose); without it the container
#    goes into a crash loop with "statfs: no such file or directory"
mkdir -p ~/.config/containers/volumes/any-sync-bundle/data

# 3. The container's env vars — download the example and edit it
mkdir -p ~/.config/containers/env
wget -O ~/.config/containers/env/any-sync-bundle.env \
  https://raw.githubusercontent.com/wallacepnts/quadlet-homelab/main/apps/any-sync-bundle/.env.example
# edit ~/.config/containers/env/any-sync-bundle.env: ANY_SYNC_BUNDLE_INIT_EXTERNAL_ADDRS

# 4. Start it
systemctl --user daemon-reload
systemctl --user start any-sync-bundle
loginctl enable-linger $(whoami)

# 5. Check
systemctl --user is-active any-sync-bundle
podman logs any-sync-bundle --tail 20   # look for "AnySync Bundle is ready!"
```

After the first run, the Anytype client imports
`~/.config/containers/volumes/any-sync-bundle/data/client-config.yml`.

</details>

## Exposure through Tailscale (tsdproxy) — optional

If the server already runs
[tsdproxy](https://github.com/almeidapaulopt/tsdproxy) to publish containers
on the tailnet, any-sync-bundle can be exposed the same way. tsdproxy v2.3.4
supports **raw TCP/UDP** proxying (not only HTTP), through labels in
`[Container]`:

```ini
Label=tsdproxy.enable=true
Label=tsdproxy.name=any-sync
Label=tsdproxy.port.sync=33010/tcp:33010/tcp
Label=tsdproxy.port.quic=33020/udp:33020/udp
```

(already included in this repo's `any-sync-bundle.container`). tsdproxy
discovers the container through the Podman socket and resolves the target by
the port published on the host (`PublishPort=`, already present in the unit) —
it does not need to be on the same Podman network.

Once the node shows up on the tailnet (`tailscale status | grep any-sync`),
add the MagicDNS hostname to `externalAddr` (see Troubleshooting) so that
`client-config.yml` includes an address reachable from any network:

```yaml
externalAddr:
    - localhost
    - any-sync.<your-tailnet>.ts.net
```

## Updating the image

An explicit tag, like the original `compose.aio.yml` — no `AutoUpdate=`,
bumped by hand whenever you want ([rule 9](../../docs/conventions.md)).
`wud.watch=true` is on for passive visibility (see [wud](../wud/)).

**`wud.tag.include` is required**: ghcr publishes a `-minimal` for every
release (the same version and date, the variant without embedded Mongo/Redis —
it is the modular mode's image) — WUD treats that suffix as a "higher" version
and produces a false update (`1.5.0-2026-07-17-minimal` marked as available
even while already on the latest suffixless tag). The same kind of problem as
vaultwarden's, with a regex restricting it to the `X.Y.Z-YYYY-MM-DD` format
with no suffix:
```ini
Label=wud.tag.include=^[0-9]+.[0-9]+.[0-9]+-[0-9]+-[0-9]+-[0-9]+$
```

Why manual even with a real `HealthCmd` (unlike the old `-minimal` image,
which never had one)? Not because of the embedded Mongo's version in itself —
the binary already detects it and fails cleanly if Mongo does not come up (a
SIGILL from missing AVX on the host, say; see Troubleshooting), so Podman's
rollback on a `:latest` tag would catch that. The reason is the generic one
for any service with real data and no way to test beforehand (gitea, immich):
`HealthCmd` guarantees the process answered, not that the update did not
silently break something (a schema migration, a protocol change). Before this
migration, the embedded Mongo's version was tested separately with disposable
data before touching the real data (see Migrating data, under Troubleshooting)
— going automatic would lose that check on every future bump.

```ini
Image=ghcr.io/grishy/any-sync-bundle:1.5.0-2026-07-17
```

```bash
# Take a backup first (see the dedicated section). Edit Image= in the
# .container, then:
systemctl --user daemon-reload
systemctl --user restart any-sync-bundle
```

The tag follows the format
`v[semver-version]-[any-sync-compatibility-date]` (`1.5.0-2026-07-17`, say —
the date suffix is the any-sync compatibility version the Anytype apps use,
not the release's date). Check the running version with:

```bash
podman inspect any-sync-bundle --format '{{index .Config.Labels "org.opencontainers.image.version"}}'
```

**The embedded Mongo's version comes fixed inside the image** — unlike the
modular mode, it cannot be pinned or changed separately. Recent Mongo 8.0.x
builds (`8.0.26`, for example) refuse to start on Linux kernel 6.19+ (Mongo's
own internal guard,
[SERVER-121912](https://jira.mongodb.org/browse/SERVER-121912)) — if an
any-sync-bundle tag change brings a new embedded Mongo version that hits that
bug, the only way out is going back to the modular mode (the Variants
section), where Mongo can be pinned (`mongo:8.0.4`, already tested working on
this kernel).

## Backup & recovery

A single volume (`data/`) — simpler than the modular mode's three. What
actually matters is `bundle-config.yml`, which holds the node's private keys
(`peerId`/`peerKey`/`signingKey`); losing that file without a backup means the
server cannot be restored as the same node, only recreated from scratch.
`client-config.yml`, by contrast, is regenerated on every start and needs no
backup.

```bash
# Stop it before the backup (it avoids capturing the embedded Mongo/Redis mid-write)
systemctl --user stop any-sync-bundle

tar -czf any-sync-backup-$(date +%Y%m%d-%H%M%S).tar.gz \
  -C ~/.config/containers/volumes any-sync-bundle

systemctl --user start any-sync-bundle
```

**Restoring:**

```bash
systemctl --user stop any-sync-bundle
podman unshare rm -rf ~/.config/containers/volumes/any-sync-bundle
tar -xzf any-sync-backup-YYYYMMDD-HHMMSS.tar.gz -C ~/.config/containers/volumes
systemctl --user start any-sync-bundle
```

(`podman unshare rm` — not a plain `rm` — because the embedded Mongo's files
are created with a uid remapped by rootless,
[rule 17](../../docs/conventions.md).)

Take a backup before any manual upgrade (changing any-sync-bundle's tag) — the
embedded Mongo's version changes along with it, and the kernel incident
documented above is exactly the scenario where that would avoid downtime.

**Automated backup through [Zerobyte](../zerobyte/):** copying Mongo's (`.wt`)
or badger's (`storage/`) raw files while the process is writing is the classic
recipe for a corrupt, unrestorable backup. The webhook in `backup-webhook/`
stops the whole container before Restic actually runs and brings it back
afterwards — since it is a single container now, that became simpler than in
the modular mode (there is no longer a three-service shutdown to coordinate).
Details and installation in
[zerobyte/README.md](../zerobyte/README.md#creating-the-backup-jobs).

## Deploying on another server / another tailnet

The `.container` unit is portable and can be copied straight over. **Do not
copy** the data in `volumes/any-sync-bundle/` — each server has to generate
its own identity (`peerId`/`peerKey`/`signingKey` in `bundle-config.yml`,
generated on the first run); copying it would make the two servers collide as
"the same node".

What changes per server/tailnet:

1. **CPU/AVX** — check it again (`grep avx /proc/cpuinfo`); without AVX, only
   the modular mode works (the Variants section).
2. **`ANY_SYNC_BUNDLE_INIT_EXTERNAL_ADDRS`** — an IP or hostname reachable for
   that specific server.
3. **tsdproxy (if used)** — an authkey **from the new tailnet** (that
   account's https://login.tailscale.com/admin/settings/keys), a new Podman
   secret (`podman secret create authkey ...`); `Label=tsdproxy.name=` can stay
   `any-sync` without conflict, since it is a different tailnet. The MagicDNS
   suffix changes too (`tailscale status --json` on the new server).
4. **Ports already in use** — check `ss -tlnp | grep -E '33010|33020'` before
   starting, in case the host already has another service on those ports.

## Variants

**Modular mode** (Mongo and Redis in separate, external containers) — it no
longer exists in this repository (removed after the migration to AIO, which
has been tested and works on this host). Use that mode instead of AIO if you
need:

- **A CPU without AVX** — the modular mode allows swapping Mongo for a 4.4
  version (with no AVX requirement); AIO has no such option, its embedded
  Mongo is always 5.0+.
- **Manual control of Mongo's version** — pinning a specific version rather
  than accepting whatever comes embedded in any-sync-bundle's image (relevant
  if a new kernel hits the SERVER-121912 bug documented above and the AIO image
  has not yet fixed it upstream).

If either scenario applies, recreate the modular mode from the official
[`compose.external.yml`](https://github.com/grishy/any-sync-bundle/blob/main/compose.external.yml)
(external Mongo + Redis, `start-bundle` instead of `start-all-in-one`) — or
recover the earlier version of this README and `.container` from the git
history (`git log -- any-sync-bundle/`) as a reference for how this repository
used to do it.

## Troubleshooting

**Containers in a crash loop with `statfs: ... no such file or directory`**
A Podman bind mount requires the directory to already exist on the host —
unlike docker compose, which creates it itself. Run step 2 of the installation
(`mkdir -p ~/.config/containers/volumes/any-sync-bundle/data`) before starting.
If it has already gone into a crash loop and hit systemd's rate limit:
`systemctl --user reset-failed any-sync-bundle` after creating the directory.

**I changed `ANY_SYNC_BUNDLE_INIT_EXTERNAL_ADDRS` and nothing happened**
That env var is only read on the first start (while `bundle-config.yml` does
not yet exist). After that, edit
`volumes/any-sync-bundle/data/bundle-config.yml` directly, the `externalAddr:`
field (a YAML list, which accepts several addresses), then `systemctl --user
restart any-sync-bundle` — that regenerates `client-config.yml`.

**The embedded MongoDB dies with "illegal instruction" (SIGILL/AVX)**
A CPU without AVX — Mongo 5.0+ requires it, embedded included in AIO mode.
There is no non-AVX variant for AIO — you have to go back to the modular mode
with Mongo 4.4 (the Variants section).

**Migrating data from modular mode to AIO: the replica hangs at "Our replica
set config is invalid or we are not a member of it"**
Tested in practice while migrating this very deploy: copying Mongo's raw files
(`mongo/db/` → `data/mongo/`) is not enough — the replica set's configuration
(`local.system.replset`) is recorded **inside** the data files themselves,
referencing the old hostname (`mongo:27017`, the modular mode's
`NetworkAlias`). AIO's embedded Mongo identifies itself as `127.0.0.1:27017`,
so the container gets stuck in a retry loop ("failed to initialize mongo
replica set, retrying...") until it hangs for good. The fix: start an isolated
temporary Mongo pointing at the same data directory, and reconfigure the
replica set's member:

```bash
systemctl --user stop any-sync-bundle

podman run --rm -d --name mongo-repair \
  -v ~/.config/containers/volumes/any-sync-bundle/data/mongo:/data/db:Z \
  -p 27018:27017 \
  docker.io/library/mongo:8.0.4 mongod --replSet rs0 --port 27017 --bind_ip_all

podman exec mongo-repair mongosh --quiet --port 27017 --eval '
var cfg = rs.conf();
cfg.members[0].host = "127.0.0.1:27017";
cfg.version += 1;
rs.reconfig(cfg, {force: true});
'

podman stop mongo-repair
systemctl --user start any-sync-bundle
```

The AIO image has no `mongosh` (only `mongod`, to keep the image smaller,
and Mongo's apt repository is removed after installation) — which is why the
repair uses the `mongo:8.0.4` image already known to this repo (it has
`mongosh`), in a separate container mounting the same `dbpath`, rather than
any-sync-bundle's image.

**A name collision with another any-sync Quadlet deploy on the same host**
Quadlet names units after the file's *basename* — two `any-sync.network` files
in different subdirectories collide silently (one overwrites the other on
`daemon-reload`, with no error). That is why this setup uses names prefixed
with `bundle` (`any-sync-bundle.container`) instead of the official example's
generic names — it avoids colliding with other any-sync deploys (the official
multi-node stack, for instance).

**The client will not connect**
- Check that `ANY_SYNC_BUNDLE_INIT_EXTERNAL_ADDRS` (or the `externalAddr`
  already persisted in `bundle-config.yml`) matches an address genuinely
  reachable from the client
- Check the host's firewall: TCP 33010 and UDP 33020 have to be open
  (`PublishPort=` in Quadlet only exposes the port to the host — it does not
  open the firewall on its own)

## Useful commands

```bash
systemctl --user status any-sync-bundle
journalctl --user -u any-sync-bundle -f
podman logs -f any-sync-bundle
```

There is no `mongosh` inside the container (see Troubleshooting) — to
inspect the embedded Mongo directly, use the same trick as the repair
container (mount `data/mongo` in a separate `mongo:8.0.4`, with
`any-sync-bundle` **stopped**, to avoid two processes writing to the same
`dbpath` at once).

## Credits

Quadlet deploy based on [any-sync-bundle](https://github.com/grishy/any-sync-bundle),
by [Sergei G. (@grishy)](https://github.com/grishy). Original licence: MIT.
