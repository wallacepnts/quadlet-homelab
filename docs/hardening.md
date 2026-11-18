# Hardening, as measured

**[🇧🇷 Leia em português](./pt-BR/endurecimento.md)**

What each image actually accepted, container by container. Rule 20 of the
[conventions](./conventions.md) says never to copy another service's hardening
block blindly — what an image tolerates is only found by testing it. This is
where those tests are kept, so the next person does not pay for them twice.

The first table is generated from the units, and [`check.py`](../check.py)
verifies it: a row that stops matching its `.container` fails the check. The
rest is knowledge no file can be asked for — an error message, a uid, a reason —
and is maintained by hand.

## Measured state

| Container | `ReadOnly` | Capabilities |
| --- | --- | --- |
| `actual` | yes | **none** + `User=1000` |
| `adguardhome` | yes | 1 (`net_bind_service`) |
| `anki` | yes | **none** + `User=65532` |
| `any-sync-bundle` | no | 5 (`chown`, `dac_override`, `fowner`, `setgid`, `setuid`) |
| `audiobookshelf` | no | 4 (`chown`, `net_bind_service`, `setgid`, `setuid`) |
| `authentik` | yes | **none** + `User=1000` |
| `authentik-postgres` | yes | **none** + `User=70` |
| `authentik-worker` | yes | 5 (`chown`, `dac_override`, `fowner`, `setgid`, `setuid`) + `User=0` |
| `beaverhabits` | yes | **none** + `User=1000` |
| `beszel` | yes | **none** |
| `beszel-agent` | no | podman default |
| `calibre-web-automated` | yes | 4 (`chown`, `net_bind_service`, `setgid`, `setuid`) |
| `casa` | no | 6 (`chown`, `dac_override`, `fowner`, `kill`, `setgid`, `setuid`) |
| `changedetection` | yes | **none** + `User=1000` |
| `collabora` | no | 1 (`sys_chroot`) |
| `cookcli` | yes | **none** + `UserNS=keep-id` |
| `copyparty` | yes | **none** + `User=1000` |
| `docuseal` | yes | **none** + `User=1000` |
| `donetick` | yes | **none** + `User=1000` |
| `dozzle` | yes | **none** + `User=1000` |
| `excalidash` | no | 4 (`chown`, `net_bind_service`, `setgid`, `setuid`) |
| `excalidash-backend` | no | 5 (`chown`, `dac_override`, `fowner`, `setgid`, `setuid`) |
| `faved` | yes | 1 (`net_bind_service`) + `User=33` |
| `ferdium-server` | no | **none** |
| `filebrowser` | yes | **none** + `UserNS=keep-id` |
| `fmd-server` | yes | **none** + `User=1000` |
| `freshrss` | yes | 4 (`chown`, `net_bind_service`, `setgid`, `setuid`) |
| `frigate` | no | podman default |
| `ghost` | yes | **none** + `User=1000` |
| `gitea` | no | 4 (`chown`, `net_bind_service`, `setgid`, `setuid`) |
| `gitea-runner` | yes | **none** |
| `grafana` | yes | **none** + `User=472` |
| `headscale` | yes | **none** |
| `hermes-agent` | no | podman default |
| `home-assistant` | yes | **none** |
| `homebox` | yes | **none** + `User=1000` |
| `homepage` | yes | **none** |
| `instagram-monitor` | yes | **none** + `User=10001` |
| `immich` | yes | **none** + `UserNS=keep-id` |
| `immich-machine-learning` | yes | **none** + `UserNS=keep-id` |
| `immich-postgres` | no | **none** + `User=999` |
| `immich-redis` | yes | **none** + `UserNS=keep-id` |
| `invio` | no | **none** |
| `karakeep` | yes | **none** |
| `karakeep-chrome` | yes | **none** |
| `karakeep-meilisearch` | yes | **none** |
| `karaoke-eternal` | yes | **none** + `User=1000` |
| `kiwix` | yes | **none** + `User=1001` |
| `koffan` | yes | **none** + `User=1000` |
| `komga` | yes | **none** + `User=1000` |
| `lubelogger` | no | **none** |
| `mailpit` | yes | **none** + `User=1000` |
| `mdrop` | yes | **none** |
| `bazarr` | no | 4 (`chown`, `net_bind_service`, `setgid`, `setuid`) |
| `deluge` | no | 4 (`chown`, `net_bind_service`, `setgid`, `setuid`) |
| `dispatcharr` | no | podman default |
| `downtify` | no | podman default |
| `gluetun` | no | podman default |
| `jellyfin` | no | podman default + `UserNS=keep-id` |
| `lidarr` | no | 4 (`chown`, `net_bind_service`, `setgid`, `setuid`) |
| `navidrome` | yes | **none** + `User=1000` |
| `prowlarr` | no | 4 (`chown`, `net_bind_service`, `setgid`, `setuid`) |
| `radarr` | no | 4 (`chown`, `net_bind_service`, `setgid`, `setuid`) |
| `sabnzbd` | no | 4 (`chown`, `net_bind_service`, `setgid`, `setuid`) |
| `seerr` | yes | **none** + `UserNS=keep-id` |
| `sonarr` | no | 4 (`chown`, `net_bind_service`, `setgid`, `setuid`) |
| `memos` | yes | **none** + `User=1000` |
| `metube` | yes | **none** + `User=1000` |
| `monica` | no | podman default |
| `n8n` | no | **none** + `UserNS=keep-id` |
| `neko` | no | 3 (`chown`, `setgid`, `setuid`) |
| `netbootxyz` | no | 6 (`chown`, `dac_override`, `fowner`, `net_bind_service`, `setgid`, `setuid`) |
| `nginx` | no | 4 (`chown`, `net_bind_service`, `setgid`, `setuid`) |
| `node-red` | no | **none** + `UserNS=keep-id` |
| `ntfy` | yes | **none** + `User=1000` |
| `omni-tools` | no | 4 (`chown`, `net_bind_service`, `setgid`, `setuid`) |
| `openwa` | yes | 5 (`chown`, `dac_override`, `fowner`, `setgid`, `setuid`) |
| `openwebui` | no | **none** |
| `openwebui-ollama` | no | **none** |
| `owncloud` | no | 6 (`chown`, `dac_override`, `fowner`, `net_bind_service`, `setgid`, `setuid`) |
| `owntracks-frontend` | no | podman default |
| `owntracks-mosquitto` | yes | **none** + `User=1883` |
| `owntracks-recorder` | no | podman default |
| `paperless-ngx` | yes | **none** |
| `paperless-ngx-broker` | yes | **none** + `User=999` |
| `paperless-ngx-gotenberg` | yes | **none** |
| `paperless-ngx-postgres` | yes | **none** + `User=70` |
| `paperless-ngx-tika` | yes | **none** |
| `pkvault` | yes | 4 (`chown`, `dac_override`, `setgid`, `setuid`) |
| `postfix` | no | 6 (`chown`, `dac_override`, `fowner`, `net_bind_service`, `setgid`, `setuid`) |
| `postiz` | yes | **none** + `User=33` |
| `postiz-postgres` | yes | **none** + `User=70` |
| `postiz-redis` | yes | **none** + `User=999` |
| `postiz-temporal` | no | **none** |
| `postiz-temporal-postgres` | yes | **none** + `User=999` |
| `prometheus` | yes | **none** + `User=65534` |
| `proxmox` | no | podman default |
| `radicale` | yes | 4 (`chown`, `kill`, `setgid`, `setuid`) |
| `rclone` | yes | **none** + `UserNS=keep-id` |
| `retrom` | no | 3 (`chown`, `setgid`, `setuid`) |
| `searxng` | yes | **none** + `User=977` |
| `stirling-pdf` | no | 5 (`chown`, `dac_override`, `fowner`, `setgid`, `setuid`) |
| `syncthing` | yes | **none** + `User=1000` |
| `toolbx-arch` | no | podman default + `UserNS=keep-id` |
| `toolbx-fedora` | no | podman default + `UserNS=keep-id` |
| `toolbx-rhel` | no | podman default + `UserNS=keep-id` |
| `toolbx-ubuntu` | no | podman default + `UserNS=keep-id` |
| `traccar` | yes | **none** + `User=1000` |
| `tsdproxy` | no | **none** |
| `uptime-kuma` | yes | **none** + `User=1000` |
| `vaultwarden` | yes | 1 (`net_bind_service`) |
| `vaultzap` | yes | **none** + `UserNS=keep-id:uid=65532,gid=65532` |
| `vikunja` | yes | **none** + `User=1000` |
| `vm-chromeos` | no | podman default + 1 add |
| `vm-macos` | no | podman default + 1 add |
| `vm-qemu` | no | podman default + 1 add |
| `vm-windows` | no | podman default + 1 add |
| `vm-windows-arm` | no | podman default + 1 add |
| `vm-zima` | no | podman default + 1 add |
| `wger` | yes | **none** |
| `wud` | yes | **none** |
| `zabbix` | no | **none** + `User=1997` |
| `zabbix-postgres` | yes | **none** + `User=70` |
| `zabbix-server` | yes | **none** + `User=1997` |
| `zerobyte` | yes | 1 (`dac_read_search`) |
| `zigbee2mqtt` | yes | **none** |
| `zigbee2mqtt-mosquitto` | yes | **none** + `User=1883` |

## Zero capabilities: who accepted, who refused

`DropCapability=ALL` is the cheapest step and most images take it. These are the
ones that did not, and where the entrypoint insists on writing.

| Accepted (went to zero capabilities) | Refused, and where the entrypoint writes |
| --- | --- |
| memos, syncthing | nginx, omni-tools → `/etc/nginx/conf.d/default.conf` |
| | netbootxyz → `/var/lib/nginx/logs` |
| | owncloud → `/var/www/owncloud/custom` |
| | stirling-pdf → `/tmp/stirling-pdf` |
| | freshrss → `/etc/localtime` |
| | gitea, calibre-web-automated → the s6-overlay lock |
| | audiobookshelf, any-sync-bundle → an exception at start |

## Which uid the files end up owned by

`UserNS=keep-id` is not hardening — it only decides who owns the files in a bind
mount. `User=` is, and it changes the answer:

| config | uid on the host |
| --- | --- |
| default | 1000 (you) |
| `UserNS=keep-id` | 1000 (you) |
| `User=1000` | **100999** |

## Refusals on record

The error that showed up, so the attempt is not repeated. This is the half that
cannot be generated: a container that starts and answers proves the hardening
works, and only the message proves why it cannot go further.

| Container | Adjustment | What happened |
| --- | --- | --- |
| `ferdium-server` | `ReadOnly=true` | the entrypoint `git clone`s the recipes and writes `/home/node/.gitconfig` |
| `ferdium-server` | `User=1000` | `EACCES: mkdir '/usr/local/lib/node_modules/pnpm'` — it installs pnpm globally on every start |
| `filebrowser` | without `UserNS=keep-id` | `could not open database: open /home/filebrowser/data/database.db: permission denied` |
| `filebrowser` | internal port 80 | `Server error: listen tcp 0.0.0.0:80: bind: permission denied` under keep-id |
| `filebrowser` | `ReadOnly=true` with the default `cacheDir` | `cacheDir failed to create cache directory: mkdir tmp: read-only file system` — solved by pointing `cacheDir` at the volume |
| `authentik-worker` | `DropCapability=ALL` with nothing added | `chown: /data`, then `chmod: /data`, then `setpriv: setresuid failed` — the entrypoint adjusts the volumes as root and drops to the authentik user, so it takes five. The **server** role of the same image needs none of them, because `User=1000` makes the entrypoint skip that path entirely; the worker is `User=0` because the podman socket it mounts belongs to the host user, which maps to 0 |
| `vaultzap` | `Secret=` with `type=mount` | `make mountpoint: read-only file system` — use `type=env`. Not a general rule: on the same Podman 6.0.2, `owntracks-mosquitto` mounts a `type=mount` secret under `ReadOnly=true`, with and without `UserNS=keep-id` |
| `proxmox` | without `--privileged` | `ERROR: Please start the container with the --privileged flag!` |
| `toolbx` | installing a package under `UserNS=keep-id` | denied; use `podman exec --user root` |
| `pkvault` | `DropCapability=ALL` alone | the container stays `Up` with the app dead: supervisord keeps running while nginx exits on `mkdir() "/var/lib/nginx/tmp/client_body" failed (13: Permission denied)` — nginx runs as root over a directory owned by `nginx`. Without `CHOWN`: `chown("/var/lib/nginx/tmp/client_body", 100) failed`; without `DAC_OVERRIDE`: the same `mkdir` |
| `pkvault` | `Tmpfs=/var/lib/nginx/tmp` without `mode=1777` | uploading a save answers 500: `open() "/var/lib/nginx/tmp/client_body/0000000001" failed (13: Permission denied)` — nginx spools any body over 16 KB there, and the tmpfs comes up owned by root. Podman's `--tmpfs` has no `uid=`; the subfolders nginx creates inside are still `0700 nginx` |
| `pkvault` | `User=100` | `Error: Can't drop privilege as nonroot user` — the image's `supervisord.conf` declares `user=root` |
| `postiz-temporal` | `ReadOnly=true` | `unable to create open /etc/temporal/config/docker.yaml: read-only file system` — the entrypoint renders its configuration there on every start |
| `postiz` | `DropCapability=ALL` while root | the container stays `Up` with the app dead: nginx exits on `mkdir() "/var/lib/nginx/body" failed (13: Permission denied)`. Root needs four to run nginx, and each one missing fails differently: no `CHOWN` → `chown("/var/lib/nginx/body", 100) failed (1)`; no `DAC_OVERRIDE` → the same `mkdir`; no `SETGID` or `SETUID` → `worker process exited with fatal code 2`. `User=33` needs none of them |
| `postiz` | `User=1000` | `open() "/var/log/nginx/access.log" failed (13: Permission denied)` — a tmpfs over `/var/log/nginx` is filled with a copy of the image's `access.log`, owned by `www-data` with mode 0640. Use `User=33` |
| `postiz` | `HOME=/root` as a non-root user | `EACCES: permission denied, mkdir '/root/.pm2/logs'` — `/root` is 0700, so no tmpfs under it is reachable. The unit points `HOME` at its own tmpfs |
| `postiz` | `ReadOnly=true` with `/root/.cache` as a volume | the backend sometimes never opens port 3000, with no error in any log: 2 of 9 starts, against 0 of 18 with the cache on a tmpfs in the lab — and 1 of 4 in the installed unit, which has the tmpfs, so it is not the whole cause. `pm2 restart backend` brings it up. The cache is 244 MB that `pnpm dlx prisma` downloads on every start |
| `postiz` | `PidsLimit=256` | the repository's default is too tight here: 197 at rest, peak 202. The unit uses 512 |
| `zabbix` | `ReadOnly=true` | `/usr/lib/docker-entrypoint/nginx.sh: line 11: /etc/nginx/includes/access-log.conf: Read-only file system` — the entrypoint renders the nginx config into `/etc/nginx` on every start, and a tmpfs over it would hide the image's own files there. Everything else (no capabilities, `User=1997`) is accepted |
| `zabbix-server` | no `RunInit=true` | `StopSignal SIGTERM failed to stop container in 10 seconds, resorting to SIGKILL` — the entrypoint runs as PID 1 and does not pass the signal on. With `--init` the stop takes 1–2 s; the unit also gives it `StopTimeout=30`, the official compose's grace period |
| `postfix` | `ReadOnly=true` | exits 1 — `run.sh` rewrites `/etc/postfix/main.cf` on every start |
| `postfix` | `User=1000` | `chmod: changing permissions of '/scripts/common.sh': Operation not permitted` |
| `postfix` | `DropCapability=ALL` alone | the container stays `Up` with the app dead: `chown: /var/spool/postfix/private: Operation not permitted` |
| `tsdproxy` | a gradient icon in `dash.icon` | tsdproxy injects `fill="currentColor"` at the SVG root; a path with no `fill` of its own becomes a solid block. Use a monochrome one (`si/`, `mdi/`, or selfh.st's `-light`/`-dark` variant) |
| immich (all three) | `--cap-drop=NET_RAW` | does nothing: rootless, `podman info` declares 11 default capabilities and `NET_RAW` is not one of them. Measured: `CapEff` is identical with and without the flag. Only immich's three units tried it, out of 110 |
| anything mounting `podman.sock` | `:z` alone | under SELinux the process ends up `container_t` and the API refuses: `permission denied while trying to connect to the docker API`. The service comes up **healthy** and sees no containers at all. Use `SecurityLabelType=container_runtime_t`, not `SecurityLabelDisable` — eight units: authentik-worker, beszel-agent, casa, dozzle, gitea-runner, homepage, tsdproxy, wud |
| `collabora` | `ReadOnly=true` | `Access to file denied: /opt/cool/child-roots/...` — the tmpfs is born owned by root and coolwsd runs as uid 1001 |
| `collabora` | `DropCapability=ALL` alone | `chroot(...) failed (EPERM)` — each document runs in a jail of its own |
| `retrom` | `ReadOnly=true` | panic at `packages/telemetry/src/lib.rs:48` — the entrypoint chowns all three volumes on every start |
| `excalidash-backend` | `User=1000` | `Can't write to /app/node_modules/prisma` — Prisma writes inside the image |
| `excalidash-backend` | `ReadOnly=true` | `EROFS: read-only file system, utime '/root/.cache/prisma/...'` |
| `excalidash` | `ReadOnly=true` | the entrypoint generates `/etc/nginx/nginx.conf` from the template on every start |
| `neko` | `ReadOnly=true` | comes up but does not serve: supervisord writes its socket in `/var/run` |
| a folder of several units (`vm`, `toolbx`) | one backup job per unit | the hook stops the units by prefix in a single call; stopping many takes longer than the default 60s, hence `WEBHOOK_TIMEOUT=180` (the old media-stack, twelve units, was the case that showed it; its apps are independent now) |
| `vm-windows` | `DISK_TYPE=sata` on Windows XP | ignored — `writeState "type" "blk"` is hardcoded for `winxpx*`, and there is no virtio driver for XP |
| `casa` | `User=1000` | `Script must be executed with root privileges.` (exit 12) — the entrypoint refuses to run unprivileged, then drops to uid 1000 itself with `gosu` |
| `casa` | `ReadOnly=true` | `groupadd: cannot lock /etc/group` — the entrypoint creates the group and the user on every start, and also chowns `/var/lib/casaos`, where the UI lives, so a tmpfs over it would hide the UI |
| `casa` | `DropCapability=ALL` alone | exits 10 at `groupadd: failure while writing changes to /etc/gshadow`. All six are needed, each with its own error: `chown` (`groupadd`), `dac_override` and `fowner` (`install -d -o` on `/DATA/AppData`, exit 1), `setuid` and `setgid` (`gosu`: `failed switching to "1000:1000"`), and `kill` — without it the stop takes 11 s and ends in `SIGKILL` (exit 137), because the entrypoint's shutdown `pkill`s the uid-1000 processes |
| `casa` | no `--cgroupns=host` | `Failed to identify the current container!` — the entrypoint looks for its own id in `/proc/self/cgroup`, and a private cgroup namespace shows none. Its fallback, a `sed` over `mountinfo`, then returns `storage` (from `.../containers/storage/...`) instead of the id and never reaches the hostname lookup |
| `casa` | `SAMBA=N` | no effect measured: with the six capabilities `smbd` is not running either way, and its ports are not published |

## Per-app notes

The prose that used to live in each app's README: what an image refused, with the error.

### anki

Everything, measured on `26.08-distroless`: read-only root with no `/tmp`
(a 3 MB media file synced without one), no capabilities, `User=65532`. Tested
with a real client — login, a wrong password refused, a note and a media file
uploaded from one collection and downloaded into another.

`StopSignal=SIGINT` because the server has no handler for SIGTERM, podman's
default: every stop and restart waited the 10 seconds to SIGKILL. On SIGINT it
exits cleanly, with code 0.

### collabora

One capability, `SYS_CHROOT`. Collabora runs each document in its own chroot
jail, and with everything dropped the kit dies at start:

```
FTL  chroot("/opt/cool/child-roots/...") failed (EPERM: Operation not permitted)
```

`ReadOnly=true` was tried and refused — `Access to file denied:
/opt/cool/child-roots/...`, because a tmpfs over that path belongs to root
while coolwsd runs as uid 1001, which the image already sets.

There is no `HealthCmd`, and therefore no `Notify=healthy`: the image carries
no shell and no `curl` or `wget` — `coolwsd`, `coolmount`, `coolforkit` and
`openssl` are the whole of `/usr/bin`, so there is nothing to run inside it.

### docuseal

The whole ladder: `ReadOnly=true`, every capability dropped, `User=1000`.
Measured with the application serving — Puma listening and the interface
answering — not just with the container up.

### dozzle

The whole ladder: `ReadOnly=true`, every capability dropped, `User=1000`.
Measured with it connected — `Connected to Docker` in the log and the interface
answering — not just with the container up.

The health check is the binary's own subcommand, `/dozzle healthcheck`, in exec
form: the image ships no shell, so `CMD-SHELL` would fail.

### faved

The whole ladder, measured: `ReadOnly=true` with tmpfs on `/tmp`, `/var/run`
and `/var/log/apache2`, every capability dropped except `NET_BIND_SERVICE`, and
`User=33`.

The capability is there because Apache listens on port 80 **inside** the
container, which is privileged. The `User=33` is www-data, the user the image
itself drops to — without it the volume belongs to root and the app answers
with an empty page after silently failing to write: `touch: cannot touch
'/var/www/html/storage/...': Permission denied`. `qh` does the `podman unshare
chown` for you because the unit declares `User=`.

### ferdium-server

`DropCapability=ALL` as root. Two rungs above that were tried and refused:

- `ReadOnly=true` — the entrypoint clones the recipes with git and writes
  `/home/node/.gitconfig`: `could not create work tree dir 'recipes':
  Read-only file system`.
- `User=1000` — it installs pnpm globally on every start:
  `EACCES: permission denied, mkdir '/usr/local/lib/node_modules/pnpm'`.

### instagram-monitor

Everything, measured on `v4.0.2`: read-only root with `/tmp`, no capabilities,
`User=10001` (the image's built-in `instagram` user). `PodmanArgs=--init`
because the Python process spawns children (instaloader sessions) that need
proper zombie reaping — the upstream compose sets `init: true`.

### kiwix

The whole ladder: `ReadOnly=true`, every capability dropped, `User=1001` — the
`user` the image itself runs as. Measured with a real library downloaded and
served, not just with the container up.

`ReadOnly=true` does not stop the download: the volume is a bind mount, and
read-only applies to the container's own filesystem.

### komga

The whole ladder: `ReadOnly=true`, every capability dropped, `User=1000`.
Measured with the application actually up — `Started ApplicationKt` in the log
and `/actuator/health` answering 200 — not just with the container running.

`HealthStartPeriod=90s` is not padding: a JVM takes about eleven seconds to
boot here before the first scan, and a cold library takes longer.

### pkvault

Read-only root, four capabilities (`chown`, `dac_override`, `setgid`, `setuid`),
no `User=`. Tested by exercising the app — a save uploaded, a backup taken, a
Pokémon moved from a save into storage and the save written back.

The image runs supervisord as root, with nginx on 3000 in front of the .NET
backend on 5000. That is what bounds it: nginx, as root, writes into a folder
owned by the `nginx` user, which takes those four capabilities, and
`supervisord.conf` declares `user=root`, which refuses any other user. The
details are in [the refusals](./hardening.md#refusals-on-record).

Two things in the unit follow from that:

- `Tmpfs=/var/lib/nginx/tmp` carries `mode=1777`: nginx spools every upload
  over 16 KB there, and without it uploading a save answered 500.
- `HealthCmd` asks the API, not just the page: with nginx dead, supervisord
  kept the container `Up`, and `/api/settings` only answers when nginx and the
  backend both do.

### postiz

Everything but the Temporal container is read-only, with no capabilities, and every
one runs as a user other than root. Tested by exercising the app: sign-up, login,
a 9 MB image upload through the nginx buffer, a post scheduled on a channel and
run by the Temporal worker, on a fresh database and on one already in use.

- **Postiz runs as `www-data` (`User=33`)**, which needs no capability at all.
  As root it needs four (`CHOWN`, `DAC_OVERRIDE`, `SETGID`, `SETUID`) just for
  nginx to start.
- **`HOME` points at a tmpfs**, `/home/postiz`, which holds pm2's files and the
  pnpm cache. The image's own `/root` is `0700`.
- **`PidsLimit=512`.** 197 at rest, a peak of 202: the repository's 256 is too
  tight for this one.
- **Temporal is not read-only.** It renders its configuration into
  `/etc/temporal/config` on every start.

**Sometimes the page does not load after a start.** The backend can come up without ever opening
port 3000, with nothing in any log: the nginx answers `502`, the container stays
`starting`, and `pm2 list` shows `backend online`. Measured in the installed unit: 1 start
in 4 (and 2 in 9 in the lab with the cache on a volume). Without help, systemd gives up
at `TimeoutStartSec` (7 minutes) and starts it again; to skip the wait:

```bash
podman exec postiz pm2 restart backend      # opens :3000 in about 13 seconds
```

The cause is not found: the process is idle, with its Redis and Temporal connections open.

Every refusal, with its error, is in
[the refusals](./hardening.md#refusals-on-record). One of them is easy to
undo by accident: the pnpm cache must stay a tmpfs. Measured with it as a volume,
the backend never opened port 3000 in 2 of 9 starts, with nothing in any log.

### rclone

Measured on `1.75.2`: read-only root with a 64 MB `/tmp`, no capabilities, no
extra privileges. The process runs as your own uid through `UserNS=keep-id`,
which is not hardening — it is what lets it read and rewrite a `rclone.conf`
that is mode 600 and yours. Without it the file would belong to the container's
root and be unreadable to a non-root process.

Tested in a lab with the same flags: login (401 without it, 200 with it), the
GUI served from the cache after a restart, the health check, and creating a
remote through the API, which wrote `rclone.conf` as 600 and owned by the host
user. Not tested: a real cloud remote, or a browser session through tsdproxy.

### vikunja

The whole ladder: `ReadOnly=true`, every capability dropped, `User=1000` — the
uid the image itself declares. Measured with the migrations run and the API
answering, not just with the container up.

The health check is the binary's own subcommand, in exec form:

```ini
HealthCmd=["CMD", "/app/vikunja/vikunja", "healthcheck"]
```

The image is distroless — `/app/vikunja/vikunja` and a CA bundle are the whole
of it — so `CMD-SHELL` would have no shell to run in.

### zabbix

Measured on `alpine-7.4.16` with the same flags as the units: no capabilities
anywhere, `NoNewPrivileges`, and the server and Postgres read-only (the server
needs only a 64 MB `/tmp`). The web interface is **not** read-only: its
entrypoint writes the nginx configuration into `/etc/nginx` on every start.
Both Zabbix images already run as uid 1997.

`RunInit=true` on the server is required, not cosmetic: without it a stop waits
the 10 s and ends in SIGKILL. With it, 1–2 s.

Tested in a lab: schema created by the server, Postgres reachable from both, web
login (the default account redirects), dashboard served, and the port 10051
open. Not tested: a real agent, or the browser through tsdproxy.
