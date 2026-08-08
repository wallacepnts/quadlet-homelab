# tsdproxy — Podman Quadlet (rootless)

**[🇧🇷 Leia em português](./README.pt-BR.md)**

A [tsdproxy](https://github.com/almeidapaulopt/tsdproxy) (v2.3.4) deploy via
Podman Quadlet — it publishes containers on your tailnet automatically, one
Tailscale node per container, through label-based discovery. Migrated from an
original `docker-compose.yml` (Swarm mode). Tested on rootless Podman +
systemd `--user` (openSUSE Tumbleweed, uid 1000), but the `.container` file
and the port conflict are universal to any Linux with rootless Podman +
systemd — the SELinux section only applies to distros with SELinux enforcing
by default (Fedora, RHEL/CentOS, openSUSE Tumbleweed/MicroOS); under AppArmor
(Ubuntu/Debian) or with no MAC at all, that particular step is unnecessary.

## Architecture

tsdproxy speaks Docker's API, not Podman's — but Podman's socket is
compatible, so it is enough to expose `podman.sock` as `docker.sock` inside
the container (no need to install Docker). It watches that socket, and for
every container with `Label=tsdproxy.enable=true` it creates a Tailscale node
of its own (`tsdproxy.name=<name>`) and proxies the tailnet's traffic to the
container — raw TCP/UDP, not just HTTP (see the real use in
[`any-sync-bundle`](../any-sync-bundle/)).

## Files

```
tsdproxy.container      # main unit

config/
└── tsdproxy.yaml         # tsdproxy's config (a bind mount) — it has to exist BEFORE the first start
```

## Prerequisites

- **Tailscale installed and connected on the host** — not as a container, via
  `transactional-update` (see "Step zero" in the root README, and
  [rule 21](../../docs/conventions.md)). It is the real prerequisite: with no
  tailnet, tsdproxy has nowhere to publish.
- Rootless Podman with systemd `--user` working
- `podman.socket` enabled (a Docker-compatible API)
- A Tailscale authkey: https://login.tailscale.com/admin/settings/keys

## Installation

```bash
python3 install.py tsdproxy            # dry-run: shows what it will do
python3 install.py tsdproxy --apply
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
  https://raw.githubusercontent.com/wallacepnts/quadlet-homelab/main/apps/tsdproxy/tsdproxy.container

# 2. Data directories — a bind mount requires them to exist before the start.
#    tsdproxy does not generate a default config by itself, so
#    config/tsdproxy.yaml also has to come from somewhere before the first
#    start.
mkdir -p ~/.config/containers/volumes/tsdproxy/{data,config}
wget -O ~/.config/containers/volumes/tsdproxy/config/tsdproxy.yaml \
  https://raw.githubusercontent.com/wallacepnts/quadlet-homelab/main/apps/tsdproxy/config/tsdproxy.yaml

# 3. A secret with the Tailscale authkey
mkdir -p ~/.config/containers/secrets/tsdproxy
echo -n "YOUR_AUTHKEY" > ~/.config/containers/secrets/tsdproxy/authkey.txt
chmod 600 ~/.config/containers/secrets/tsdproxy/authkey.txt
podman secret create authkey ~/.config/containers/secrets/tsdproxy/authkey.txt

# 4. The Podman socket
systemctl --user enable --now podman.socket

# 5. Start it
systemctl --user daemon-reload
systemctl --user start tsdproxy
```

> **Start order:** Quadlet does not natively know that `tsdproxy` depends on
> `podman.socket` — without declaring it, nothing guarantees on a reboot that
> the socket already exists when `default.target` brings the container up (a
> silent, non-deterministic race). That is why `tsdproxy.container`'s `[Unit]`
> has `Requires=podman.socket` + `After=podman.socket`.

In `tsdproxy.container`, Quadlet's `%t` resolves to `$XDG_RUNTIME_DIR` —
`Volume=%t/podman/podman.sock:/var/run/docker.sock:z` on this machine (uid
1000) is equivalent to mounting `/run/user/1000/podman/podman.sock`.

</details>

## Publishing a container on the tailnet

In any `.container` (from this repo or not), add the labels and make sure the
port is published on the host (`PublishPort=`) — tsdproxy resolves the target
through it; it does not need to be on the same Podman network.

**A corollary: `PublishPort=` cannot be restricted to `127.0.0.1`.** tsdproxy
dials `host.docker.internal` (`169.254.1.2` with pasta), not loopback — tested
in practice, `PublishPort=127.0.0.1:8082:80` on vaultwarden takes the node down
to a 502 (`connect: connection refused` in tsdproxy's log). A port published
on every interface is a requirement of this architecture, so every service here
is also reachable at `http://<host-ip>:<port>` over the LAN, without TLS.
Closing that would require `tryDockerInternalNetwork: true` in tsdproxy's
config **and** tsdproxy on each target's own Podman network — which would break
karakeep and immich, which have networks of their own.

```ini
Label=tsdproxy.enable=true
Label=tsdproxy.name=my-app
Label=tsdproxy.port.web=443/https:8080/http
```

A real example of raw TCP/UDP (non-HTTP) proxying in
[`any-sync-bundle.container`](../any-sync-bundle/any-sync-bundle.container).

## Troubleshooting

**`yaml: unmarshal errors: field dashboard/proxyAccessLog not found`**
The official documentation
(https://almeidapaulopt.github.io/tsdproxy/docs/getting-started/) shows
`adminAllowLocalhost` nested under `dashboard:` and `proxyAccessLog` nested
under `log:`. This is not a schema difference between v2 and v3: checking
`config.go` for `v2.3.4` and for `v3.0.0-beta.3` (the most recent published
v3) on the project's GitHub, both fields are at the yaml's **root** in both
versions — the site's docs are out of date and wrong relative to the actual
code, in both. This repo's `config/tsdproxy.yaml` uses the root format (the
one that actually works). When changing version, test against the
corresponding tag's `config.go` before trusting the site's docs.

**`permission denied while trying to connect to the docker API`**
Only relevant on systems with SELinux enforcing. The cause: for Unix sockets,
SELinux validates the context of the *process that created the socket* (here
`podman system service`, labelled `container_runtime_t`), not the file's own
label — relabelling the bind mount with `:z`/`:Z` does not help.

Diagnosis (in this order, if you need to redo it on another machine):
```bash
getenforce                                    # or: cat /sys/fs/selinux/enforce
sudo ausearch -m avc -ts recent               # look for a "connectto" AVC
# if nothing shows up (the policy silences it via "dontaudit"):
sudo semodule -DB                             # temporarily disable dontaudit
# reproduce the error (restart the container)
sudo ausearch -m avc -ts recent -c tsdproxyd  # the connectto AVC should appear
sudo semodule -B                              # restore dontaudit
```

The relevant AVC:
```
avc: denied { connectto } comm="tsdproxyd" path="/run/user/1000/podman/podman.sock"
scontext=...:container_t tcontext=...:container_runtime_t tclass=unix_stream_socket
```

`container_connect_any` (an SELinux boolean) does not fix this particular
case under openSUSE's policy. The fix: a custom module.
```bash
sudo ausearch -m avc -ts recent -c tsdproxyd | audit2allow -M tsdproxy_dockersock
sudo semodule -i tsdproxy_dockersock.pp
```
Check it with `semodule -l | grep tsdproxy`. Remove it with
`sudo semodule -r tsdproxy_dockersock`.

**`NeedsLogin` with no auth URL after starting**
The `tsnet` state was corrupted by repeated restarts during an earlier crash
loop (containers coming up and dying repeatedly before the socket worked). The
log itself says so: "Restart tsdproxy to auto-recover, or manually delete the
proxy data directory." It usually resolves itself on the next restart, with
the socket now reachable (`systemctl --user restart tsdproxy`). If it does
not, delete `~/.config/containers/volumes/tsdproxy/data/default/` and restart.

## Nodes disappearing from the tailnet by themselves (an ephemeral auth key)

By default, deleting a container does **not** remove its node from Tailscale's
admin console (see "Two traps specific to this repository" in
[Installing and operating](../../docs/installing.md)) — it is left orphaned
until somebody removes it by hand. That can be automated by generating the
authkey as **ephemeral**: a node registered with an ephemeral key disappears
from the tailnet by itself some 30–60 minutes after going offline, with no
manual intervention.

**Where that is decided**: in the authkey itself alone, generated with the
**Ephemeral** option ticked at
https://login.tailscale.com/admin/settings/keys — it is not a label and not a
tsdproxy setting. Tested by a user and confirmed by the maintainer: the
`tsdproxy.ephemeral=true` label does **not** enable it
([discussion #71](https://github.com/almeidapaulopt/tsdproxy/discussions/71)).

```bash
# 1. Generate the new authkey at https://login.tailscale.com/admin/settings/keys
#    with both "Reusable" AND "Ephemeral" ticked (Reusable was already
#    mandatory — a single key registers every service this tsdproxy proxies)

# 2. Replace the secret
podman secret rm authkey
echo -n "NEW_AUTHKEY" > ~/.config/containers/secrets/tsdproxy/authkey.txt
podman secret create authkey ~/.config/containers/secrets/tsdproxy/authkey.txt

# 3. Restart tsdproxy (and any-sync-bundle, which creates its own node
#    directly, without going through tsdproxy)
systemctl --user restart tsdproxy any-sync-bundle
```

**Two important caveats**:
- It only applies to nodes **registered after the change** — the key used at
  registration decides that node's ephemerality; it is not retroactive.
  Existing nodes stay exactly as they are until they are re-registered (a
  logout plus a fresh login with the new key).
- It does not clean up the duplicate orphans that already exist today
  (`dash`/`dash-1` and the like) — those need removing by hand once, as
  already documented.

## Deploying on another server

**Do not copy** `volumes/tsdproxy/data/` — it holds each created Tailscale
node's `tsnet` state and identity; copying it would make the nodes collide
with each other. Every server needs its own authkey (generated on the
destination tailnet) and brings its nodes up from scratch.

## Useful commands

```bash
systemctl --user status tsdproxy
podman logs -f tsdproxy
podman secret ls
semodule -l | grep tsdproxy   # only under SELinux enforcing
```

## Credits

Quadlet deploy based on [tsdproxy](https://github.com/almeidapaulopt/tsdproxy),
by [Paulo Almeida (@almeidapaulopt)](https://github.com/almeidapaulopt).
Original licence: MIT.
