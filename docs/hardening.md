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
| `any-sync-bundle` | no | 5 (`chown`, `dac_override`, `fowner`, `setgid`, `setuid`) |
| `audiobookshelf` | no | 4 (`chown`, `net_bind_service`, `setgid`, `setuid`) |
| `authentik` | yes | **none** + `User=1000` |
| `authentik-postgres` | yes | **none** + `User=70` |
| `authentik-worker` | yes | 5 (`chown`, `dac_override`, `fowner`, `setgid`, `setuid`) + `User=0` |
| `beaverhabits` | yes | **none** + `User=1000` |
| `beszel` | yes | **none** |
| `beszel-agent` | no | podman default |
| `calibre-web-automated` | yes | 4 (`chown`, `net_bind_service`, `setgid`, `setuid`) |
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
| `freshrss` | yes | 4 (`chown`, `net_bind_service`, `setgid`, `setuid`) |
| `frigate` | no | podman default |
| `ghost` | yes | **none** + `User=1000` |
| `gitea` | no | 4 (`chown`, `net_bind_service`, `setgid`, `setuid`) |
| `grafana` | yes | **none** + `User=472` |
| `hermes-agent` | no | podman default |
| `home-assistant` | yes | **none** |
| `homebox` | yes | **none** + `User=1000` |
| `homepage` | yes | **none** |
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
| `media-stack-bazarr` | no | 4 (`chown`, `net_bind_service`, `setgid`, `setuid`) |
| `media-stack-deluge` | no | 4 (`chown`, `net_bind_service`, `setgid`, `setuid`) |
| `media-stack-dispatcharr` | no | podman default |
| `media-stack-downtify` | no | podman default |
| `media-stack-gluetun` | no | podman default |
| `media-stack-jellyfin` | no | podman default + `UserNS=keep-id` |
| `media-stack-lidarr` | no | 4 (`chown`, `net_bind_service`, `setgid`, `setuid`) |
| `media-stack-navidrome` | yes | **none** + `User=1000` |
| `media-stack-prowlarr` | no | 4 (`chown`, `net_bind_service`, `setgid`, `setuid`) |
| `media-stack-radarr` | no | 4 (`chown`, `net_bind_service`, `setgid`, `setuid`) |
| `media-stack-sabnzbd` | no | 4 (`chown`, `net_bind_service`, `setgid`, `setuid`) |
| `media-stack-seerr` | yes | **none** + `UserNS=keep-id` |
| `media-stack-sonarr` | no | 4 (`chown`, `net_bind_service`, `setgid`, `setuid`) |
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
| `paperless-ngx-tika` | yes | **none** |
| `postfix` | no | 6 (`chown`, `dac_override`, `fowner`, `net_bind_service`, `setgid`, `setuid`) |
| `prometheus` | yes | **none** + `User=65534` |
| `proxmox` | no | podman default |
| `radicale` | yes | 4 (`chown`, `kill`, `setgid`, `setuid`) |
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
| `postfix` | `ReadOnly=true` | exits 1 — `run.sh` rewrites `/etc/postfix/main.cf` on every start |
| `postfix` | `User=1000` | `chmod: changing permissions of '/scripts/common.sh': Operation not permitted` |
| `postfix` | `DropCapability=ALL` alone | the container stays `Up` with the app dead: `chown: /var/spool/postfix/private: Operation not permitted` |
| `tsdproxy` | a gradient icon in `dash.icon` | tsdproxy injects `fill="currentColor"` at the SVG root; a path with no `fill` of its own becomes a solid block. Use a monochrome one (`si/`, `mdi/`, or selfh.st's `-light`/`-dark` variant) |
| immich (all three) | `--cap-drop=NET_RAW` | does nothing: rootless, `podman info` declares 11 default capabilities and `NET_RAW` is not one of them. Measured: `CapEff` is identical with and without the flag. Only immich's three units tried it, out of 110 |
| anything mounting `podman.sock` | `:z` alone | under SELinux the process ends up `container_t` and the API refuses: `permission denied while trying to connect to the docker API`. The service comes up **healthy** and sees no containers at all. Use `SecurityLabelType=container_runtime_t`, not `SecurityLabelDisable` — six units: authentik-worker, beszel-agent, dozzle, homepage, tsdproxy, wud |
| `collabora` | `ReadOnly=true` | `Access to file denied: /opt/cool/child-roots/...` — the tmpfs is born owned by root and coolwsd runs as uid 1001 |
| `collabora` | `DropCapability=ALL` alone | `chroot(...) failed (EPERM)` — each document runs in a jail of its own |
| `retrom` | `ReadOnly=true` | panic at `packages/telemetry/src/lib.rs:48` — the entrypoint chowns all three volumes on every start |
| `excalidash-backend` | `User=1000` | `Can't write to /app/node_modules/prisma` — Prisma writes inside the image |
| `excalidash-backend` | `ReadOnly=true` | `EROFS: read-only file system, utime '/root/.cache/prisma/...'` |
| `excalidash` | `ReadOnly=true` | the entrypoint generates `/etc/nginx/nginx.conf` from the template on every start |
| `neko` | `ReadOnly=true` | comes up but does not serve: supervisord writes its socket in `/var/run` |
| media-stack | one backup job per unit | the hook stops the stack by prefix (`media-stack-*`) in a single call; stopping twelve takes longer than the default 60s, hence `WEBHOOK_TIMEOUT=180` |
| `vm-windows` | `DISK_TYPE=sata` on Windows XP | ignored — `writeState "type" "blk"` is hardcoded for `winxpx*`, and there is no virtio driver for XP |
