Open `http://<host-ip>:8080` or `https://dash.<your-tailnet>.ts.net`.

### Publishing something that is not a container

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
