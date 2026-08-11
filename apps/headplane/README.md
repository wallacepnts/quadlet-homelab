# Headplane

<img src="https://cdn.jsdelivr.net/gh/homarr-labs/dashboard-icons/svg/headscale.svg" width="64" height="64" alt="">

**[🇧🇷 Leia em português](./README.pt-BR.md)**

The web interface [Headscale](../headscale) does not ship with. Nodes, users,
pre-auth keys and ACLs on a screen instead of a CLI inside a container.

It reads headscale's own configuration and talks to its API — so headscale has
to exist first, and this is useless without it.

## Install

```bash
qh headplane            # shows the plan
qh headplane --apply
```

Open `http://<host-ip>:8116/admin` — the interface lives under `/admin`, and
the root answers 404 by design.

Signing in needs an API key from headscale:

```bash
podman exec headscale headscale apikeys create --expiration 90d
```

<details>
<summary><b>Manual install (advanced)</b></summary>

```bash
mkdir -p ~/.config/containers/systemd
mkdir -p ~/.config/containers/volumes/headplane/{config,data}

wget -P ~/.config/containers/systemd/ \
  https://raw.githubusercontent.com/wallacepnts/quadlet-homelab/main/apps/headplane/headplane.container
wget -O ~/.config/containers/volumes/headplane/config/config.yaml \
  https://raw.githubusercontent.com/wallacepnts/quadlet-homelab/main/apps/headplane/config/config.yaml

openssl rand -hex 16 | tr -d '\n' | podman secret create headplane-cookie-secret -

# The container runs as uid 1000, which is not yours after the mapping
podman unshare chown -R 1000:1000 ~/.config/containers/volumes/headplane

systemctl --user daemon-reload
systemctl --user start headplane
```

</details>

## Files

```
headplane.container   unit
config/config.yaml    the configuration, into the volume
install.ini
```

`data/` holds `hp_persist.db`, which is sessions and interface state. Nothing
in it is the tailnet: lose it and you sign in again, that is all. The tailnet
itself is headscale's database.

## It mounts headscale's config

```ini
Volume=%h/.config/containers/volumes/headscale/config/config.yaml:/etc/headscale/config.yaml:ro,Z
```

Headplane reads it to know the shape of the tailnet — base domain, prefixes,
where the database is. It is mounted read-only and from headscale's own volume,
which means **headscale has to be installed first** or the unit will not start:
a bind mount of a file that does not exist fails, the same rule that applies to
directories.

## What it can and cannot change

By default it is a reader and an API client: it lists nodes, creates keys,
edits ACLs through headscale's API.

Restarting headscale when an ACL changes needs the `docker.enabled` integration
and the Podman socket mounted into this container. That is a real handover — a
container that can restart other containers — and it ships off. Turn it on only
if you want that trade, and add the socket to the unit yourself.

## Hardening

The whole ladder: `ReadOnly=true`, every capability dropped, `User=1000`.
Measured with the interface actually answering on `/admin/` and writing its
database to the volume.

The health check runs `node` rather than `curl` or `wget`: the image carries
neither, and Node is right there.

## Update

```bash
qh headplane --update --apply
```

Pinned to `0.7.0`.

## Backup

```bash
qh headplane --backup --apply --out ~/backups
```

Little to lose, as above. `qh headscale --backup` is the one that matters.

## Remove

```bash
qh headplane --remove --apply           # stops it, keeps the sessions
qh headplane --remove --purge --apply   # and deletes the volume and the secret
```

Removing it changes nothing about the tailnet: headscale goes on without an
interface.

## Commands

```bash
systemctl --user status headplane
podman logs -f headplane
```

## Credits

[tale/headplane](https://github.com/tale/headplane) — MIT.

[Official documentation](https://headplane.net/)
