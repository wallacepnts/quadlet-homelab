# any-sync-bundle

<img src="https://cdn.jsdelivr.net/gh/homarr-labs/dashboard-icons/svg/anytype.svg" width="64" height="64" alt="">

**[🇧🇷 Leia em português](./README.pt-BR.md)**

The Any-Sync protocol backend, which syncs Anytype's data across devices without relying on the company's cloud.

## Install

```bash
qh any-sync-bundle            # shows the plan
qh any-sync-bundle --apply
```

Open `http://<host-ip>:33010` or `https://any-sync.<your-tailnet>.ts.net`.

<details>
<summary><b>Manual install</b></summary>

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

</details>

## Files

```
any-sync-bundle.container   unit
.env.example                environment
```

## Connecting the Anytype app

The first start writes `client-config.yml` into the data volume. That file is
what points an Anytype client at this server instead of the company's cloud:

```bash
cat ~/.config/containers/volumes/any-sync-bundle/data/client-config.yml
```

Import it in the app, following [Anytype's own
instructions](https://doc.anytype.io/anytype-docs/advanced/data-and-security/self-hosting/self-hosted#how-to-switch-to-a-self-hosted-network).

It is regenerated on every start and holds no key, so it does not need backing
up — `bundle-config.yml`, next to it, is the opposite: it carries the private
keys and losing it means losing the network.

## Compared to the official stack

[anyproto's compose](https://github.com/anyproto/any-sync-dockercompose) runs
eleven containers: MongoDB, Redis, MinIO and a bucket job, the coordinator,
the filenode, three sync nodes, the consensus node and a netcheck tool. This
bundle is the same protocol in one container, with Mongo and Redis embedded
and two ports open instead of a dozen.

What the official stack has that this does not: three sync nodes, so a node
can fail without the network stopping, and MinIO for the files. Neither buys
anything on a single host — three replicas of a service on one disk is one
disk.

Files go to the embedded BadgerDB by default, which is limited by the disk. If
that ever becomes the constraint, the bundle speaks S3 — set
`ANY_SYNC_BUNDLE_INIT_S3_ENDPOINT`, `_S3_BUCKET`, `_S3_REGION` and
`_S3_FORCE_PATH_STYLE` in the `.env`, and the files move out without the other
ten containers coming in.

## Update

```bash
qh any-sync-bundle --update --apply
```

Pinned to `1.5.0-2026-07-17`. Nothing updates on its own — a new version is applied
when you run the command above.

## Backup

```bash
qh any-sync-bundle --backup --apply --out ~/backups
```

It stops the service, packs the data, the `.env` and the secrets, and starts
it again. Cold on purpose: copying a live database gives an archive that only
fails when you restore it.

For the scheduled copy, Zerobyte has to find this service stopped too — its
[backup hook](../zerobyte/README.md#backup-hook) does that, with
`any-sync-bundle` in the allowlist.

To restore, over the current data:

```bash
qh any-sync-bundle --restore ~/backups/any-sync-bundle-20260809-1200.tar.gz --apply
```

It asks you to type `any-sync-bundle` to confirm, because the current data is deleted
before the archive is unpacked.

## Remove

```bash
qh any-sync-bundle --remove --apply           # stops it, keeps the data
qh any-sync-bundle --remove --purge --apply   # and deletes volumes, secrets and .env
```

`--purge` asks for the typed name too. The tailnet node is not deregistered by
this — that is done in the Tailscale admin.

## Commands

```bash
systemctl --user status any-sync-bundle
podman logs -f any-sync-bundle
```

## Credits

[grishy/any-sync-bundle](https://github.com/grishy/any-sync-bundle) — MIT

[Official documentation](https://github.com/grishy/any-sync-bundle#readme)
