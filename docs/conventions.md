# Conventions

This repository's 22 rules, each with the real case that produced it. They are
what [`check.py`](../check.py) verifies automatically where it can.

Rules to follow for any new service in this repository (Podman 5.8.3).

### 1. A unique file name across the whole repository

Quadlet names the generated unit after the file's *basename*, even across
different subfolders of `~/.config/containers/systemd/`. Prefix every file
with the app's name: `any-sync-bundle-net.network`.

### 2. Secrets are imperative

Extensions Quadlet recognises: `.container .volume .network .build .pod .kube
.artifact .image`. The secret flow:

```bash
mkdir -p ~/.config/containers/secrets/<app>
echo -n "secret-value" > ~/.config/containers/secrets/<app>/password.txt
chmod 600 ~/.config/containers/secrets/<app>/password.txt
podman secret create <app>-password ~/.config/containers/secrets/<app>/password.txt
```

```ini
Secret=<app>-password,target=/run/secrets/password
```

### 3. `.network`: the key is `NetworkName=`

```ini
[Network]
NetworkName=<app>-net
```

`Driver=bridge` is Podman's default; only declare it if you want it explicit.

### 4. Quadlet-generated units: only `start`/`stop`/`restart`/`status`

`[Install]` is already applied at generation time.

```bash
systemctl --user daemon-reload
systemctl --user start|stop|restart|status <name>   # .service is optional here
```

### 5. `Network=`/`Volume=` pointing at another Quadlet file already injects the dependency

```ini
Network=my-app.network
```

adds `Requires=my-app-network.service` + `After=` to the generated service
automatically — do not declare it again in `[Unit]`.

### 6. Bind mount directories have to exist before the first start

`mkdir -p` every path used in `Volume=` before starting the service.

### 7. `$` in `HealthCmd` needs a double escape

```ini
HealthCmd=CMD-SHELL test $$(command) -eq 1
```

### 8. `Requires=` propagates a stop

Stopping or restarting a dependency also stops whoever requires it. If the
dependency fails in that window, whatever depended on it does not come back on
its own — start it by hand afterwards.

### 9. A floating tag requires a real `HealthCmd`

`AutoUpdate=registry` only has automatic rollback on containers with a
`HealthCmd` — which in turn requires a shell or a utility inside the image.
This repository's default: an explicit tag plus a manual bump; auto-update is
opt-in, only for images with a genuine `HealthCmd` and no critical user state.

### 10. `PublishPort=` does not open the firewall

Opening the port in the host's firewall (`firewalld`/`ufw`/`iptables`) is a
separate step.

### 11. Credit the original project

Every service folder based on another project has a "Credits" section in its
own README, linking the original repository and author.

### 12. `Label=` values with a space need quotes

```ini
Label=homepage.description="Publishes containers on the tailnet automatically"
```

Without the quotes, Quadlet truncates the value at the first space (it becomes
just `Publishes`) — with no error and no warning.

### 13. `HealthCmd` with `localhost`: use `127.0.0.1`

In the container's `/etc/hosts`, `localhost` resolves to IPv4 (`127.0.0.1`)
**and** IPv6 (`::1`). If the process only listens on IPv4, a client that
prefers IPv6 (`wget`, or `curl` without `-4`) gets "Connection refused" even
with the service up — testing with the explicit IP avoids the problem.

```ini
HealthCmd=CMD-SHELL wget -q --spider http://127.0.0.1:3000/ || exit 1
```

### 14. `Notify=healthy` requires a `HealthCmd` in the Quadlet, even with a HEALTHCHECK in the image

An image already having a `HEALTHCHECK` in its Dockerfile is not enough —
`Notify=healthy` without a `HealthCmd=` declared in the `.container` always
fails with `sdnotify policy "healthy" requires a healthcheck to be set`.
Repeating the image's own command in `HealthCmd=` fixes it.

### 15. `Secret=name,type=env,target=VAR` — a secret as an env var, not a file

```ini
Secret=my-app-password,type=env,target=POSTGRES_PASSWORD
```

An alternative to `target=/path` (which mounts a file) for when the app
expects the environment variable directly rather than a file in
`/run/secrets/`. It follows the same rule 2 — the secret has to exist
beforehand, via `podman secret create`.

### 16. A container that needs to read other containers' volumes: `SecurityLabelDisable=true`

```ini
SecurityLabelDisable=true
```

Every volume in this repository uses `:Z` (a **private** SELinux label,
exclusive to the owning container). A third container trying to read those
paths — even with `:ro` alone — gets `Permission denied`, because `:Z` is
exclusive by design. Tools that need to see several containers' data at once
(a backup, for instance — see [zerobyte](../apps/zerobyte/)) have to turn
SELinux confinement off for that specific container. A deliberate trade-off,
not something to use by default.

### 17. Touching a container-created file by hand: `podman unshare`, not `sudo`

Rootless Podman maps the container's internal uids to a range of "phantom"
uids on the host (via the user namespace, configured in
`/etc/subuid`/`/etc/subgid`). A file created by the container in a bind mount
belongs to that mapped uid (`100100`, say), not to your user (`1000`) — a
plain `cp`/`mv`/`rm` gives `Permission denied`, because as far as the
filesystem is concerned you are completely different users. `sudo` does not
help (it switches to real root, who is not the owner either). The right
command runs inside the same namespace Podman uses:

```bash
podman unshare mv source destination
podman unshare rm path/file
podman unshare ls -la path/
```

Any file manipulation command (`mv`, `cp`, `chown`, `rm`…) can be prefixed
with `podman unshare` when the target is inside `volumes/` and belongs to the
container rather than to you.

**Copying a new file *in*** (not just moving one that already exists) needs an
extra step — tested in practice: `podman unshare cp` copies correctly (it
grants write access to the folder), but the new file ends up with **your** uid,
different from its neighbours. Fix the owner afterwards, using `--reference` so
you do not have to guess the mapped uid (it varies per service):

```bash
podman unshare cp /source/file.txt ~/.config/containers/volumes/<app>/<folder>/
podman unshare chown --reference="$HOME/.config/containers/volumes/<app>/<folder>/some-existing-file" \
  ~/.config/containers/volumes/<app>/<folder>/file.txt
```

### 18. `Label=` does not accept a backslash in the value

Unlike the `$$` of rule 7 (which is about systemd expanding `$`), here it is
**Quadlet's own parser** that refuses: any `\` inside a `Label=` value (a
regex with `\d` or `\.`, say) makes the entire line be discarded —
`quadlet-generator: unsupported escape char` in the journal, with no visible
error in `systemctl cat` or in `podman inspect` (the label simply does not
exist on the container, as if the line had never been written). No escaping
helps — neither `\\` nor quoting the value. Rewrite it without the backslash:
`[0-9]` in place of `\d`, and an unescaped `.` (acceptable in a filter regex,
which is not critical). Real case in
[`wud/`](../apps/wud/#wudtagincludewudtagtransform-no-backslash-in-the-value).

### 19. One variable, several units: `~/.config/environment.d/*.conf`

When several different `.container` files need to point at the **same**
variable path (a media root shared between several services, say — see
[media-stack](../apps/media-stack/)), you can avoid editing each file with a
hardcoded path by using a systemd environment variable rather than an ordinary
`EnvironmentFile=`: `EnvironmentFile=` only injects env vars *inside the
container*, far too late to affect how Quadlet resolves `Volume=`. The right
mechanism is systemd's own `environment.d(5)` — `~/.config/environment.d/*.conf`
defines variables for the whole `systemd --user` *manager's* environment, and
those variables become available for `${VAR}` expansion in `Volume=` and
`Environment=` in any of that user's units:

```bash
mkdir -p ~/.config/environment.d
cat > ~/.config/environment.d/my-app.conf <<EOF
MY_PATH=/real/path
EOF
systemctl --user daemon-reload   # mandatory — without it the new variable
                                  # does not exist for the manager yet
```

```ini
Volume=${MY_PATH}:/something:Z
```

Tested in practice: `systemctl cat` shows a literal `${MY_PATH}` (it is just
the file's text, with no substitution) — which is confusing and looks like it
did not work — but `podman inspect` on the container already reflects the
genuinely resolved path, because the expansion happens in the generated
`ExecStart=`, at the moment systemd actually starts the process, not when the
file is generated. Test with `podman inspect <container> --format
'{{json .Mounts}}'`, do not trust `systemctl cat` alone.

**It works in `Label=` too, not only in `Volume=`** — every `homepage.href` in
this repository uses `${TAILNET}` for that reason:

```ini
Label=homepage.href=https://my-app.${TAILNET}.ts.net
```

```bash
echo "TAILNET=my-tailnet" > ~/.config/environment.d/tailnet.conf
systemctl --user daemon-reload
```

It keeps the repo publishable without exposing the tailnet's name, and it
survives a `wget` of an updated unit — unlike editing the value directly in
the file, which the next download overwrites. **An undefined variable expands
to an empty string, silently** (`https://my-app..ts.net`) — check with `podman
inspect` after setting it, see
[homepage](../apps/homepage/#marking-a-service-to-appear-on-the-dashboard).

### 20. Hardening (`ReadOnly`/`DropCapability`): test the app, not the container

`ReadOnly=true` + `DropCapability=ALL` are cheap and worth it on any service
that accepts them — but which ones accept is only discovered by testing. The
measured state of this repository's services:

| Container | `ReadOnly` | Capabilities |
| --- | --- | --- |
| `actual` | yes | **none** + `User=1000` |
| `adguardhome` | yes | 1 (`net_bind_service`) |
| `any-sync-bundle` | no | 5 (`chown`, `dac_override`, `fowner`, `setgid`, `setuid`) |
| `audiobookshelf` | no | 4 (`chown`, `net_bind_service`, `setgid`, `setuid`) |
| `authentik-postgres` | no | 5 (`chown`, `dac_override`, `fowner`, `setgid`, `setuid`) |
| `authentik-worker` | no | podman default + `User=0` |
| `authentik` | yes | **none** + `User=1000` |
| `beszel-agent` | no | podman default |
| `beszel` | yes | **none** |
| `calibre-web-automated` | yes | 4 (`chown`, `net_bind_service`, `setgid`, `setuid`) |
| `cookcli` | yes | **none** |
| `copyparty` | yes | **none** + `User=1000` |
| `donetick` | yes | **none** + `User=1000` |
| `freshrss` | yes | 4 (`chown`, `net_bind_service`, `setgid`, `setuid`) |
| `frigate` | no | podman default |
| `ghost` | yes | **none** + `User=1000` |
| `gitea` | no | 4 (`chown`, `net_bind_service`, `setgid`, `setuid`) |
| `home-assistant` | yes | **none** |
| `homebox` | yes | **none** + `User=1000` |
| `homepage` | yes | **none** |
| `immich-machine-learning` | yes | **none** |
| `immich-postgres` | no | **none** + `User=999` |
| `immich-redis` | no | podman default |
| `immich` | yes | **none** |
| `invio` | no | **none** |
| `karakeep-chrome` | yes | **none** |
| `karakeep-meilisearch` | yes | **none** |
| `karakeep` | yes | **none** |
| `lubelogger` | no | **none** |
| `mdrop` | yes | **none** |
| `media-stack-bazarr` | no | 4 (`chown`, `net_bind_service`, `setgid`, `setuid`) |
| `media-stack-deluge` | no | 4 (`chown`, `net_bind_service`, `setgid`, `setuid`) |
| `media-stack-dispatcharr` | no | podman default |
| `media-stack-downtify` | no | podman default |
| `media-stack-gluetun` | no | podman default |
| `media-stack-jellyfin` | no | podman default |
| `media-stack-lidarr` | no | 4 (`chown`, `net_bind_service`, `setgid`, `setuid`) |
| `media-stack-prowlarr` | no | 4 (`chown`, `net_bind_service`, `setgid`, `setuid`) |
| `media-stack-radarr` | no | 4 (`chown`, `net_bind_service`, `setgid`, `setuid`) |
| `media-stack-sabnzbd` | no | 4 (`chown`, `net_bind_service`, `setgid`, `setuid`) |
| `media-stack-seerr` | yes | **none** |
| `media-stack-sonarr` | no | 4 (`chown`, `net_bind_service`, `setgid`, `setuid`) |
| `memos` | yes | **none** + `User=1000` |
| `metube` | yes | **none** + `User=1000` |
| `monica` | no | podman default |
| `n8n` | no | **none** |
| `netbootxyz` | no | 6 (`chown`, `dac_override`, `fowner`, `net_bind_service`, `setgid`, `setuid`) |
| `nginx` | no | 4 (`chown`, `net_bind_service`, `setgid`, `setuid`) |
| `node-red` | no | **none** |
| `ntfy` | yes | **none** + `User=1000` |
| `omni-tools` | no | 4 (`chown`, `net_bind_service`, `setgid`, `setuid`) |
| `openwebui-ollama` | no | **none** |
| `openwebui` | no | **none** |
| `owncloud` | no | 6 (`chown`, `dac_override`, `fowner`, `net_bind_service`, `setgid`, `setuid`) |
| `owntracks-frontend` | no | podman default |
| `owntracks-mosquitto` | no | podman default |
| `owntracks-recorder` | no | podman default |
| `paperless-ngx-broker` | yes | **none** + `User=999` |
| `paperless-ngx-gotenberg` | yes | **none** |
| `paperless-ngx-tika` | yes | **none** |
| `paperless-ngx` | yes | **none** |
| `radicale` | yes | podman default |
| `stirling-pdf` | no | 5 (`chown`, `dac_override`, `fowner`, `setgid`, `setuid`) |
| `syncthing` | yes | **none** + `User=1000` |
| `traccar` | yes | **none** + `User=1000` |
| `tsdproxy` | no | **none** |
| `uptime-kuma` | yes | **none** + `User=1000` |
| `vaultwarden` | yes | 1 (`net_bind_service`) |
| `vaultzap` | yes | **none** |
| `wger` | yes | **none** |
| `wud` | yes | **none** |
| `zerobyte` | yes | **none** |
| `zigbee2mqtt-mosquitto` | yes | **none** + `User=1883` |
| `zigbee2mqtt` | yes | **none** |

The table is generated from the units themselves — it is the measured state of
every container, not a summary. `podman default` means `DropCapability=ALL` was
refused and Podman's 11 defaults remain.

**How each row was measured** — the table says *what* is set, not how far it
was verified:

- **Exercised for real** (the app answered over HTTP, the database was written,
  a file was converted) — most of the single-container services.
- **Measured with the image in isolation** (empty volumes, no real env): the
  strongest level that still came up, but it does NOT exercise the app —
  `audiobookshelf`, `beszel`, `calibre-web-automated`, `freshrss`, `gitea`, `immich-machine-learning`, `lubelogger`, `n8n`, `nginx`, `node-red`, `openwebui-ollama`, `openwebui`, `paperless-ngx`. Confirm for real when installing.
- **Not measured**: `owntracks-frontend` (it does not come up in isolation — it
  exits without a reachable recorder, so the ladder cannot tell a hardening
  refusal from a missing dependency; with ReadOnly it fails at "can't create
  /etc/nginx/nginx.conf") and `beszel-agent` (it exists to read the host, so
  testing it in isolation says nothing — measure it with beszel up and the
  metrics still arriving).
- **Measured only up to a point**: `zigbee2mqtt` reaches the coordinator's
  opening with no permission error, but there is no Zigbee coordinator on this
  machine; `home-assistant` was measured on a clean installation — enabling an
  integration that talks straight to hardware (Bluetooth, Zigbee over USB,
  mDNS) means measuring again.

Cases the table cannot show:

- `authentik-postgres` does **not** accept `User=999`, unlike immich's
  Postgres: its entrypoint insists on adjusting the owner and permissions of
  `/var/lib/postgresql/data` and `/var/run/postgresql`, and with only 3
  capabilities it still fails at "chmod: /var/run/postgresql".
- `paperless-ngx-broker` is the opposite: `DropCapability=ALL` alone is refused
  ("setpriv: setresuid failed") because Redis's entrypoint switches user, but
  with `User=999` it takes the full package.
- `karakeep-chrome` has the **largest attack surface** here — it opens any URL
  you save and runs with `--no-sandbox`, so Chrome's own internal sandbox is
  off and the container's hardening is the only remaining layer. Stateless, so
  ReadOnly costs nothing.

Three things the table hides, from the last nine measurements:

- **A file-mounted `Secret=` does not coexist with `ReadOnly=true`.** Podman
  does not create the mountpoint in `/run/secrets` with a read-only root, and
  not even a `Tmpfs=/run` fixes it — the creation happens before the tmpfs
  takes effect. This is what blocks tsdproxy. On
  [vaultzap](../apps/vaultzap/) the way out was switching the secret to
  `type=env`.
- **Measuring with a proxy instead of the app misleads.** any-sync-bundle
  "passed" a first measurement that counted keywords in the log: the AIO
  mode's Mongo came up, printed its boot lines and died right after with `exit
  status 14` — and the service sat `failed` on the host until I reverted it.
  With `Notify=healthy` as the judge, it refuses `ReadOnly` **and**
  `DropCapability=ALL` on its own.
- **The highest rung can pass where the middle one fails.** Ghost repeated
  metube's inversion: `DropCapability=ALL` alone dies at `failed switching to
  'node'`, but with `User=` the entrypoint has nothing to switch to and
  everything works.

### Before granting a capability, test the rung above

The four capabilities most often requested here — `CHOWN`, `SETUID`, `SETGID`
and `NET_BIND_SERVICE` — almost always appear together, and for the same
reason: the image's entrypoint does its setup as root and then becomes the
application's user. **With `User=`, it has nothing to adjust and nobody to
switch to**, and the need disappears.

A sweep across the 14 services that asked for that kit, testing `User=1000` +
`DropCapability=ALL`:

| Passes (went to zero capabilities) | Refuses, and where the entrypoint writes |
| --- | --- |
| memos, syncthing | nginx, omni-tools → `/etc/nginx/conf.d/default.conf` |
| | netbootxyz → `/var/lib/nginx/logs` |
| | owncloud → `/var/www/owncloud/custom` |
| | stirling-pdf → `/tmp/stirling-pdf` |
| | freshrss → `/etc/localtime` |
| | gitea, calibre-web-automated → the s6-overlay lock |
| | audiobookshelf, any-sync-bundle → an exception at start |

**The rule that comes out of it:** `User=` works when the entrypoint only
writes to the mounted volumes. When it writes to `/etc`, `/var/lib` or a `/tmp`
of its own — or when the image uses s6-overlay, which insists on being root —
there is no way around it, and the kit really is the minimum.

A fourth observation, from **zigbee2mqtt**: it is about method. `podman diff`
after a start showed the app only writes to the `/app/data` bind, which
answers "does ReadOnly fit?" without exercising anything. Worth doing before
moving on to the expensive test.

Another, more general one: when the image's entrypoint switches user
(`gosu`/`usermod`/`setpriv`), **turning that mechanism off** is sometimes
cheaper than granting the three capabilities it asks for — as long as running
as uid 0 inside the container is acceptable (under rootless that is your own
uid on the host, not real root).

**The trap: "the container came up" is not the test.** The case that taught
this here was a PHP+nginx service that used to be in the repository: with
`CHOWN,SETUID,SETGID,NET_BIND_SERVICE` it goes `running` and nginx answers —
but php-fpm dies silently and every page becomes a 502. It only surfaced once
the test started genuinely exercising the app:

```bash
podman run -d --name t --cap-drop=ALL --cap-add=... <image>
sleep 14
podman exec t curl -sf -o /dev/null -w "%{http_code}" http://127.0.0.1:80/
```

`DAC_OVERRIDE`+`FOWNER` were what was missing. Without exercising the app, the
hardening would have gone into the repository breaking the service.

**An error at `exec` = a capability recorded in the binary.** If the container
dies with `exec /path/to/binary: operation not permitted` — failing *to
execute*, not during execution — the cause is not the program requesting the
capability at runtime: it is the **file** carrying a *file capability*. Linux
refuses to execute a binary with a capability that is not in the bounding set.
That was adguardhome's case, whose binary has `cap_net_bind_service=eip`
(confirmed with `getcap`). Giving the capability back fixes it; hunting for
the request in the code does not.

**Patterns that repeat:**

- **A port <1024 inside the container** requires `NET_BIND_SERVICE` — this
  holds under rootless too, and it is the case for any image serving on the
  internal port 80 (vaultwarden, nginx). **Before granting it, see whether the
  app lets you change the port**: ntfy listens on 80 by default, and
  `NTFY_LISTEN_HTTP=:2586` made the need disappear — zero capabilities instead
  of one. The same question applies to the entrypoint's `gosu`/`usermod` and
  to `setpriv`: turning the mechanism off is sometimes cheaper than satisfying
  what it asks for.
- **An image that does a `chown`/`usermod` in its entrypoint**
  (LinuxServer.io and the like) needs `CHOWN`+`SETUID`+`SETGID` at minimum —
  **or `User=`**. metube showed the ladder is not monotonic:
  `DropCapability=ALL` on its own is refused (`chown: ... Operation not
  permitted`), but with `User=1000` the entrypoint has nothing to adjust (the
  image's `PUID` is already 1000), the `chown` disappears, and the **highest**
  rung passes. Do not give up at the first `chown` in the log: test the next
  rung before granting the capability.
- **`ReadOnly` breaks** when the entrypoint rewrites config at start (nginx is
  the classic case) or when the app writes outside the volumes. `Tmpfs=/tmp`
  covers most `/tmp` cases.

**Careful when testing with `systemctl restart` in sequence**: 5 failures in a
row hit systemd's rate limit (`start-limit-hit`) and from then on *any* start
fails, including the good configuration's — which gives the impression that
the hardening broke something that in fact works. Run `systemctl --user
reset-failed <app>` before each attempt.

**`UserNS=` is not hardening.** Under rootless the user namespace always
exists already; `keep-id` only decides which uid appears on the volumes' files
(rule 17). Adding it where the image does an internal `usermod` **breaks** it
— use it only where the image runs with a fixed uid and does not adjust
ownership itself (immich, node-red, jellyfin, seerr).

**`User=` is** — and it is the highest-impact one, because it is the only one
that changes who the process is **outside** the container. Measured here: uid
0 inside maps to **your** uid (1000) on the host, so an escape reaches your
home, your SSH keys and the Podman socket. A uid != 0 lands in the subuid
range (`100999`), which owns nothing:

| config | uid on the host |
| --- | --- |
| default | 1000 (you) |
| `UserNS=keep-id` | 1000 (you) |
| `User=1000` | **100999** |

The cost: the volume needs the same owner — `podman unshare chown -R 1000:1000
<volume>` (the uid as seen from *inside* the namespace, not the host's 100999)
— and touching it then requires `podman unshare` (rule 17). That is why it is
**not** worth it where the folder is an exchange point with you:
[vaultzap](../apps/vaultzap/)'s `inbox` would become unusable in daily use,
which is exactly why it uses `keep-id`.

**It only works on an image that does no setup as root.** Tested: uptime-kuma
accepts it (it runs as `100999` today); karakeep does not — the s6-overlay
asks for `setgid`, then `chown`, then more, and every capability given back
cancels the gain. A capability requested in a cascade is a sign to stop, not
to push on. Since `ReadOnly` and `User=` also exclude each other on some
images, and an escape is the worse scenario, `User=` wins when you can only
have one.

**`PidsLimit=`** — it works here (the `pids` controller is the only delegated
one on this host, see rule 19) and it contains a fork bomb: a compromised
process does not exhaust the host's process table. Size it by real idle usage,
which is *threads*, not processes — `cat /sys/fs/cgroup/.../pids.current`, not
`podman top`. The difference is large: a typical Node service here shows 6
processes and 65 threads. 4x headroom is enough.

**`Tmpfs=/tmp` without `size=` uses half the RAM** — the kernel's default.
Measured here: `df -h /tmp` inside the container shows a `7.8G` limit on a
16GB host, per container. With several services, a `/tmp` that fills up
through a bug or abuse turns into an OOM for the whole host. Always size it:
`Tmpfs=/tmp:size=64M`. Anything that only passes through `/tmp` (wud,
homepage, vaultwarden — 0 at idle) is comfortable at 64M; anything that
processes files needs more (karakeep archives whole pages, 256M; vaultzap
extracts `.zip` files, 128M). A special case: Chrome with
`--disable-dev-shm-usage` starts using `/tmp` in place of `/dev/shm`, and 64M
there is the classic cause of a rendering crash — `karakeep-chrome` sits at
512M.

**A `:ro` volume where the app only reads** — the cheapest of all, and the most
forgotten. homepage was mounting `config/` and `icons/` as `rw` with no need;
with `:ro` it comes up just the same and loses the ability to rewrite its own
configuration if it is compromised.

**What is not worth it here:** `Memory=` (the `memory` controller is not
delegated on this host — the same reason radicale has no RAM limit),
`SeccompProfile=` (Podman's default profile already covers the dangerous
syscalls; a custom one breaks easily for marginal gain) and `Mask=` (the
runtime already masks `/proc/kcore` and the like).

Where hardening matters least, regardless of all of this: whoever mounts the
Podman socket (homepage, wud, tsdproxy). Compromise those and you create a new,
privileged container — the current container's capabilities do not enter into
it. Closing that calls for a read-only socket proxy, not container hardening.

### 21. Not everything becomes a Quadlet: software that needs to *be* the host on the network uses `transactional-update`

This repository runs on top of immutable distros (openSUSE MicroOS) — but
"immutable" does not mean "everything in a container". The deciding question
is: **does this software need its own isolated identity (its own port, data
and network), or does it need to be indistinguishable from the host on the
network (the same hostname, the same routing table, integrated with the DNS
the host's other processes also use)?** In the first case, Quadlet as usual.
In the second, `transactional-update pkg install <package>` — MicroOS's native
mechanism for this, which is still reproducible and reversible (it applies to
a new Btrfs snapshot on the next boot, and `transactional-update rollback`
undoes it), only without the isolation layers that get in the way of exactly
what that kind of software needs to do.

A concrete case: **Tailscale as the host's identity** (not an app behind
[tsdproxy](../apps/tsdproxy/), which is a different thing — that remains the
standard for publishing services). Running `tailscaled` in a container with
`--network=host` shares the network interface with the host (SSH over the
tailnet works), but it does **not** share the D-Bus/mount namespace — the
container cannot integrate with the host's `systemd-resolved`, and MagicDNS
ends up broken for the host's own processes (other tailnet peers still resolve
this host's name normally; what breaks is resolution *leaving* this host).
Confirmed by research: even guides dedicated to running Tailscale on immutable
distros (openSUSE Kalpa) run into the same limitation and do not recommend
that route for the host's primary identity. `transactional-update pkg install
tailscale` avoids the whole problem — it gets native integration with
`systemd-resolved` and the routes, at the cost of needing a reboot to apply
(normal for that kind of package, unlike an app that only needs a `systemctl
--user restart`).

### 22. A service with a database: SQLite whenever the app supports it

When the project offers **both** (SQLite and Postgres/MySQL/MariaDB), SQLite
is what is used here — even if the official `docker-compose.yml` only shows
Postgres, which is common because the reference compose is written with a
large, multi-user installation in mind.

What that gains at this scale (one user, one machine): **one container fewer**
(sometimes two, when the database drags a Redis along with it), one secret
fewer, and the backup becomes a `tar` of the volume instead of a `pg_dump`
with the service up. And it removes the repo's worst recurring maintenance —
**a database major is not a tag bump**: going from Postgres 15 to 16 requires
a `pg_dump`/restore, whereas the SQLite file just follows the app.

Services here that already do this: [Ghost](../apps/ghost/),
[wger](../apps/wger/), [Vaultwarden](../apps/vaultwarden/),
[Uptime Kuma](../apps/uptime-kuma/) and [Paperless-ngx](../apps/paperless-ngx/) —
the last one through the compose **variant** (`sqlite-tika.yml`, not
`postgres-tika.yml`), which is where the choice shows up when a project
publishes more than one file.

The counterexample is [Immich](../apps/immich/), which only speaks Postgres —
and with a vector extension that ties the database's version to the app's. Not
every project lets you choose: the signal is usually in the schema or in the
installation docs (a hardcoded `provider = "postgresql"` in Prisma, for
example). **Check before assuming**, and record why in the service's README,
so nobody reopens the discussion later.
