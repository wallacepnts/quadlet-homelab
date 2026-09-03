# tsdproxy

<img src="https://cdn.jsdelivr.net/gh/selfhst/icons/svg/tsdproxy.svg" width="64" height="64" alt="">

**[🇧🇷 Leia em português](./README.pt-BR.md)**

Publishes containers on the tailnet automatically, from labels alone — no per-service proxy configuration.

## Install

```bash
qh tsdproxy            # shows the plan
qh tsdproxy --apply
```

Open `http://<host-ip>:8080` or `https://dash.<your-tailnet>.ts.net`.

<details>
<summary><b>Manual install</b></summary>

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
wget -O ~/.config/containers/volumes/tsdproxy/config/lists.yaml \
  https://raw.githubusercontent.com/wallacepnts/quadlet-homelab/main/apps/tsdproxy/config/lists.yaml
# lists.yaml only if you run Cockpit: uncomment it, replace <host-ip>

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

</details>

## Files

```
tsdproxy.container
config/tsdproxy.yaml   the proxy's own configuration
config/lists.yaml      services that are not containers
install.ini
```

## Publishing something that is not a container

A container is discovered by its labels. The host's own daemons have none, so
they go in `config/lists.yaml` instead — one entry per name, and tsdproxy
rereads that file without a restart.

The file carries **Cockpit**, the web console openSUSE already carries
(`cockpit.socket` on 9090, plus `cockpit-podman` if you want the containers
listed there too), commented out. Uncomment it, replace `<host-ip>` with this
machine's address, and it answers on `https://cockpit.<your-tailnet>.ts.net`:

```yaml
cockpit:
  ports:
    443/https:
      targets:
        - https://<host-ip>:9090
```

Two details that are not obvious:

- The address has to be a **real** one. `host.containers.internal` only
  answers on Podman's default network, and tsdproxy lives on `tsdproxy-net` —
  from there it times out. The tailscale address is the steadier choice, since
  it does not move with DHCP.
- The target is `https://`, not `http://` — Cockpit serves TLS itself on 9090.
  With the scheme right, its origin check passes as-is and no
  `/etc/cockpit/cockpit.conf` is needed; get it wrong and the login page loads
  but the session never opens.

Cockpit is the one host service worth this: disks, network, journal and the
system's own updates, none of which a container can show you. Creating
containers *through* it is another matter — a unit that is `--replace --rm`
comes back as soon as Cockpit stops it, and anything created by hand is
invisible to this repository. Read, do not write.

That is why the entry ships commented out: pointing at a closed port, it
publishes a name that answers 502 — and most hosts do not run Cockpit.

## Update

```bash
qh tsdproxy --update --apply
```

Pinned to `2`. Nothing updates on its own — a new version is applied
when you run the command above.

## Backup

```bash
qh tsdproxy --backup --apply --out ~/backups
```

It stops the service, packs the data, the `.env` and the secrets, and starts
it again. Cold on purpose: copying a live database gives an archive that only
fails when you restore it.

To restore, over the current data:

```bash
qh tsdproxy --restore ~/backups/tsdproxy-20260809-1200.tar.gz --apply
```

It asks you to type `tsdproxy` to confirm, because the current data is deleted
before the archive is unpacked.

## Remove

```bash
qh tsdproxy --remove --apply           # stops it, keeps the data
qh tsdproxy --remove --purge --apply   # and deletes volumes, secrets and .env
```

`--purge` asks for the typed name too. The tailnet node is not deregistered by
this — that is done in the Tailscale admin.

## Commands

```bash
systemctl --user status tsdproxy
podman logs -f tsdproxy
```

## Credits

[almeidapaulopt/tsdproxy](https://github.com/almeidapaulopt/tsdproxy) — MIT

[Official documentation](https://almeidapaulopt.github.io/tsdproxy/)
