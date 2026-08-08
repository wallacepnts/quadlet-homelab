# FileBrowser Quantum — Podman Quadlet (rootless)

**[🇧🇷 Leia em português](./README.pt-BR.md)**

A [gtsteffaniak/filebrowser](https://github.com/gtsteffaniak/filebrowser)
deploy via Podman Quadlet, using the official
`ghcr.io/gtsteffaniak/filebrowser` image.

A web file manager over a directory you choose: browse, search, preview,
rename, upload, download, share by link, and edit text in place. Quantum is a
rewrite of the original filebrowser/filebrowser with a real search index,
media previews and per-source configuration.

## What it is for, next to [copyparty](../copyparty/)

Both put a directory in a browser, and they are not the same tool:

- **copyparty** is the *transfer* endpoint — resumable uploads, dedup, a
  file-drop for people who are not you.
- **FileBrowser** is the *manager* — an indexed search across the tree,
  thumbnails, an editor, WebDAV, and shares.

Running both is reasonable. Pointing both at the same directory is also
reasonable — they do not fight over it — but only one of them should be the
one you hand out to other people.

## Architecture

A single container, two volumes:

| Volume | Holds |
| --- | --- |
| `/home/filebrowser/data` | `config.yaml`, `database.db`, the thumbnail cache |
| `/srv` | the files it manages — put yours here |

Host port **8014** maps to **8080** inside. That inside port is not upstream's
default, and the reason matters — see below.

## Three things that were measured, and why the unit looks like this

None of these are visible in upstream's compose. Each one came from a failed
start.

**`UserNS=keep-id` is required.** The image runs as a fixed uid 1000 and never
chowns anything. Without keep-id the bind mounts belong to a subuid, and the
app cannot open the database it just created:

```
[FATAL] could not open database: open /home/filebrowser/data/database.db: permission denied
```

**The internal port had to move off 80.** Upstream listens on 80. Under
keep-id the process runs as your unprivileged uid inside the namespace too, so
it cannot bind a port below 1024:

```
[FATAL] Server error: listen tcp 0.0.0.0:80: bind: permission denied
```

`server.port` in the shipped config is `8080` for that reason, and the
healthcheck, the tsdproxy label and `PublishPort` all follow it. Changing one
means changing all four.

**A missing `config.yaml` is fatal, not a warning.** The app reads its config
from *inside* the data directory, not from where the image leaves its template:

```
[FATAL] config file /home/filebrowser/data/config.yaml does not exist, please
create it or set the FILEBROWSER_CONFIG environment variable to a valid config
file path
```

That is why `install.ini` copies `config.yaml.example` into the volume. The
path cannot be derived from the unit, so it is stated there explicitly.

## Logging in

The username is **`admin`** and is not configurable by environment variable —
only through `auth.adminUsername` in `config.yaml`. The password comes from the
`filebrowser-admin-password` secret:

```bash
podman secret inspect --showsecret filebrowser-admin-password
```

The second secret, `filebrowser-jwt-secret`, signs the session cookie. It is
load-bearing rather than decorative, and that was measured: with it, a session
survives `systemctl --user restart filebrowser`; without it the app generates a
new key at every start and everyone is logged out.

Rotating it on purpose is the way to force every session out at once.

<details>
<summary><b>If you script against the API</b> — the login call is not what you would guess</summary>


The login endpoint takes the username in the query string and the password in
an **`X-Password` header**, URL-encoded. A JSON body is silently rejected with
`401`, which reads exactly like a wrong password:

```bash
curl -c jar -X POST 'http://127.0.0.1:8014/api/auth/login?username=admin' \
  -H "X-Password: $(podman secret inspect --showsecret --format '{{.SecretData}}' filebrowser-admin-password)"
curl -b jar 'http://127.0.0.1:8014/api/users?id=self'
```

The session cookie is `_quantum_jwt`.

</details>

## Files

```
filebrowser.container   # main unit
config.yaml.example     # upstream's config, with two lines changed
.env.example            # where the app looks for that config
install.ini             # the two secret recipes + the upstream override
```

`config.yaml.example` is upstream's shipped default with exactly two edits:
`server.port` `80` → `8080`, and a `server.cacheDir` pointing into the data
volume. Both are explained above and under Hardening. Everything else — the
`/srv` source, the auth methods, the user defaults — is upstream's, so
diffing it against a new release is worth doing on a version bump.

## Installation

```bash
python3 install.py filebrowser            # dry-run: shows what it will do
python3 install.py filebrowser --apply
```

Then put files in `~/.config/containers/volumes/filebrowser/files/` and open
`https://filebrowser.<your-tailnet>.ts.net`.

<details>
<summary><b>Manual installation</b> (advanced) — the same steps, one at a time</summary>


```bash
# 1. Download the unit (no need to clone the repository)
mkdir -p ~/.config/containers/systemd
wget -P ~/.config/containers/systemd/ \
  https://raw.githubusercontent.com/wallacepnts/quadlet-homelab/main/apps/filebrowser/filebrowser.container

# 2. Directories
mkdir -p ~/.config/containers/volumes/filebrowser/{data,files}
mkdir -p ~/.config/containers/env

# 3. The config — the app will not start without it
wget -O ~/.config/containers/volumes/filebrowser/data/config.yaml \
  https://raw.githubusercontent.com/wallacepnts/quadlet-homelab/main/apps/filebrowser/config.yaml.example

# 4. Environment
wget -O ~/.config/containers/env/filebrowser.env \
  https://raw.githubusercontent.com/wallacepnts/quadlet-homelab/main/apps/filebrowser/.env.example

# 5. Secrets
podman secret create filebrowser-admin-password - <<< "$(python3 -c 'import secrets,string;a=string.ascii_letters+string.digits;print("".join(secrets.choice(a) for _ in range(20)))')"
podman secret create filebrowser-jwt-secret - <<< "$(python3 -c 'import secrets;print(secrets.token_hex(32))')"

# 6. Start it
systemctl --user daemon-reload
systemctl --user start filebrowser
```

</details>

## Adding more directories

The shipped config declares one source, `/srv`. To expose another directory,
add a `Volume=` to the unit and a matching entry under `server.sources`:

```ini
Volume=%h/Documents:/docs:Z
```

```yaml
server:
  sources:
    - path: "/srv"
    - path: "/docs"
```

Each source gets its own index, so a large tree costs memory and a first-run
scan. Check `podman logs filebrowser` for `initializing index` to see when it
finishes.

## Security

**It is on the tailnet by default**, and unlike most things here it also has a
real login of its own. That is the right shape for this service: it hands out
read *and write* access to a directory tree, and shares generate links that
work for whoever holds them.

If that trade is not what you want, install with `--access local` — the
tsdproxy labels are commented out rather than deleted, so changing your mind
later is an `--update` with another mode
([Installing and operating](../../docs/installing.md)).

Worth knowing: `/srv` is the app's whole world, and it is a bind mount of a
directory in your home. It cannot escape that mount, but everything inside it
is fully writable, including deletion. Point it at a directory you are willing
to lose, or keep it backed up.

## Hardening

The full [rule 20](../../docs/conventions.md) ladder holds here, which is
uncommon — most images give out one rung earlier.

| Setting | Status |
| --- | --- |
| `NoNewPrivileges=true`, `PidsLimit=256` | applied, no measurement needed |
| `DropCapability=ALL` | **works** — measured: `200` on `/health`, login and upload both fine |
| `ReadOnly=true` + `Tmpfs=/tmp:size=64M` | **works, after moving `cacheDir`** — see below |
| `UserNS=keep-id` | **required**, and not hardening — it is what makes the volumes writable at all |
| `User=` | **not needed** — the image already runs as a non-root uid |

`ReadOnly=true` fails on the shipped config, because upstream's `cacheDir` is
the *relative* path `tmp`, which resolves inside the read-only image:

```
[FATAL] cacheDir failed to create cache directory: mkdir tmp: read-only file system
```

Pointing it at `/home/filebrowser/data/cache` fixes it and is better anyway:
thumbnails survive a restart instead of being regenerated. That is the second
of the two edits in `config.yaml.example`.

`Tmpfs=/tmp` is kept even though the cache no longer lives there — preview
generation writes transient files through Go's default temp dir. 64M is
enough for that; if you preview large video, measure with
`podman exec filebrowser df -h /tmp` before raising it.

**The test that matters is exercising the app, not seeing the container run.**
Each rung above was checked with a login, a directory listing and an upload —
`/health` alone answers `200` from a container whose file operations are all
failing.

## Auto-update

No `AutoUpdate=` — an explicit tag (`1.5.1-stable`), bumped by hand
([rule 9](../../docs/conventions.md)). Two reasons to keep it manual here:
`config.yaml` is versioned in this repository, so an upstream schema change
needs a diff rather than a restart, and the search index is rebuilt when its
format changes.

The `wud.tag.include` label filters to `-stable` tags, because the registry
also carries `-beta` and per-commit builds that sort as newer.

`install.ini` carries an `[upstream]` override: the image is
`gtsteffaniak/filebrowser`, and without that line `updates.py` would look for
releases under the wrong name.

## Backup & recovery

```bash
systemctl --user stop filebrowser
tar -czf filebrowser-backup-$(date +%Y%m%d-%H%M%S).tar.gz \
  -C ~/.config/containers/volumes filebrowser
systemctl --user start filebrowser
```

Cold on purpose: `database.db` is a live database holding users, shares and
settings, and copying it while the app writes gives an archive that only
reveals itself as corrupt when you restore it.

To back up only the metadata and not the files themselves — usually much
smaller, and the files are probably already backed up elsewhere:

```bash
tar -czf filebrowser-data-$(date +%Y%m%d-%H%M%S).tar.gz \
  -C ~/.config/containers/volumes/filebrowser data
```

The thumbnail cache is in there and is regenerable; excluding it with
`--exclude=data/cache` is fine.

## Useful commands

```bash
systemctl --user status filebrowser
podman logs -f filebrowser
podman exec filebrowser df -h /tmp                    # sizing the tmpfs
du -sh ~/.config/containers/volumes/filebrowser/data/cache   # thumbnail cache
```

## Credits

Quadlet deploy based on
[gtsteffaniak/filebrowser](https://github.com/gtsteffaniak/filebrowser)
(Apache-2.0), itself a rewrite of
[filebrowser/filebrowser](https://github.com/filebrowser/filebrowser). This
repository is not affiliated with either project.
