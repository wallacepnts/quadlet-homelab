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

Apply without testing:

```ini
PidsLimit=256
NoNewPrivileges=true
```

Then test, in this order, stopping at the first one the app refuses:

1. `DropCapability=ALL` — the log names what is missing (`chown: Operation not
   permitted` → `AddCapability=CHOWN`). A port below 1024 inside the container
   needs `NET_BIND_SERVICE`.
2. `ReadOnly=true` + `Tmpfs=/tmp:size=64M` — breaks when the entrypoint
   rewrites config at start, or when init needs `/run`.
3. `User=<non-zero uid>` — the highest impact and the most likely to break.
   Requires `podman unshare chown -R <uid>:<uid> <volume>`, and does not work
   on images that `chown`/`usermod` at start.

**A running container is not the test.** Exercise the app:

```bash
podman run -d --name t --read-only --tmpfs /tmp --cap-drop=ALL <image> ...
sleep 14
podman exec t curl -sf -o /dev/null -w "%{http_code}" http://127.0.0.1:<port>/
podman rm -f t
```

Size the `Tmpfs`: without `size=` the kernel gives half the RAM. 64M is enough
for anything that only passes through `/tmp`; measure with
`podman exec <app> df -h /tmp` under real use before raising it.

A file-mounted `Secret=` does not coexist with `ReadOnly=true` — use
`type=env`.

`UserNS=` is not hardening. It only decides who owns bind-mounted files.

**Testing through systemd**: run `systemctl --user reset-failed <app>` before
each attempt. Five failures in a row hit the rate limit, and then every start
fails — including the one that works.

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
