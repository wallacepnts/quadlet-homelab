# Proxmox VE — Podman Quadlet (rootless)

**[🇧🇷 Leia em português](./README.pt-BR.md)**

A [dockur/proxmox](https://github.com/dockur/proxmox) deploy via Podman
Quadlet, using the official `docker.io/dockurr/proxmox` image.

Proxmox VE — the hypervisor management platform — running as a container
instead of on bare metal. Somewhere to learn the interface, rehearse a cluster
change, or check whether a workflow fits before you commit a machine to it.

It is **not** a replacement for a real Proxmox install. Everything it manages
lives inside a container on a host that has its own opinions about storage and
networking; treat it as a lab, not as infrastructure.

## Why this one is not in [`apps/vm`](../vm/)

It looks like it belongs there — same author, same family, a web UI on 8006 —
but three things set it apart:

- **It runs privileged.** The other four get `/dev/kvm`, `/dev/net/tun` and
  `NET_ADMIN`; this one gets everything. That is upstream's requirement, not a
  choice (see below).
- **It runs systemd as PID 1** (`/sbin/init`), where the others run QEMU under
  `tini`. A whole init system, with the services Proxmox expects around it.
- **It is a platform, not a guest.** In `apps/vm` you pick which OS to install;
  here there is nothing to pick — you run Proxmox and create VMs inside it.

The ports also settle it: `apps/vm` publishes 8006 twice on purpose, because
`vm-windows` and `vm-windows-arm` can never run together. Proxmox and Windows
can, so it takes a port of its own.

## Privileged is mandatory, and measured

The unit carries `PodmanArgs=--privileged`. That was not copied from upstream's
compose — it was tested, because [rule 20](../../docs/conventions.md) says never
to take a hardening decision on faith. Without the flag the entrypoint stops
before it starts anything:

```
❯ ERROR: Please start the container with the --privileged flag!
```

With it, the interface answers `200` on 8006. There is no middle setting to
find: the check is upstream's own, at the top of the entrypoint.

**What that means for you.** A privileged container drops the usual isolation:
all capabilities, no seccomp filter, device access. Rootless Podman still wraps
it in your user namespace, so it is not root on the host — but it is as close
as anything in this repository gets. Nothing else here runs this way except
[media-stack](../media-stack/)'s Gluetun, and that one at least has a narrow
job.

Run it when you want Proxmox; do not leave it running when you do not.

## Requirements

- **KVM on the host**, if you intend to start VMs inside Proxmox:

  ```bash
  ls -l /dev/kvm                          # must exist
  [ -r /dev/kvm ] && [ -w /dev/kvm ] && echo ok
  ```

  The interface itself comes up without KVM; the VMs it manages will not.

- **At least 2 GB of RAM** for Proxmox itself, plus whatever the guests take.
- **32 GB of free disk**, per upstream. The storage pool is a volume here, so
  it grows inside your home directory.

## Architecture

A single container. Two volumes, which is what makes a restart survivable:

| Volume | Holds |
| --- | --- |
| `/var/lib/vz` | the storage pool — VM disks, ISOs, backups |
| `/var/lib/pve-cluster` | the configuration database |

The hostname is fixed to `pve` (`HostName=pve`), because Proxmox writes its own
hostname into the cluster config and a changing one confuses it.

The web interface is **HTTPS with a self-signed certificate**, on host port
**8010** mapped to 8006 inside. Plain HTTP on that port answers `301`, which is
why the healthcheck uses `curl -k https://` — an `http` check would pass the
redirect without ever proving the interface is up.

## Files

```
proxmox.container   # main unit
install.ini         # the root password recipe + the upstream override
```

## Installation

```bash
python3 install.py proxmox            # dry-run: shows what it will do
python3 install.py proxmox --apply
```

Then open `https://<host-ip>:8010` — accept the self-signed certificate, and
log in as `root` with:

```bash
podman secret inspect --showsecret proxmox-root-password
```

<details>
<summary><b>Manual installation</b> (advanced) — the same steps, one at a time</summary>


```bash
# 1. Download the unit (no need to clone the repository)
mkdir -p ~/.config/containers/systemd
wget -P ~/.config/containers/systemd/ \
  https://raw.githubusercontent.com/wallacepnts/quadlet-homelab/main/apps/proxmox/proxmox.container

# 2. Directories
mkdir -p ~/.config/containers/volumes/proxmox/{data,config}

# 3. Secret — the root password for the web interface
podman secret create proxmox-root-password - <<< "$(python3 -c 'import secrets,string;a=string.ascii_letters+string.digits;print("".join(secrets.choice(a) for _ in range(20)))')"

# 4. Start it
systemctl --user daemon-reload
systemctl --user start proxmox
```

</details>

## Security

Two things stack here, and they are worth reading together.

**The container is privileged**, as above — the widest posture in this
repository.

**The interface is on the tailnet by default**, following this repository's
convention. It does have a real login, unlike the viewers in
[`apps/vm`](../vm/), and `install.ini` replaces upstream's default `root`
password with a generated one. But a tailnet is not authentication: it narrows
who can knock, not who gets in.

If that trade is not what you want, install with `--access local` — the
tsdproxy labels are commented out rather than deleted, so changing your mind
later is an `--update` with another mode
([Installing and operating](../../docs/installing.md)).

## Hardening — what was not attempted

`--privileged` makes most of [rule 20](../../docs/conventions.md)'s ladder
meaningless: there is no point dropping capabilities in a container that was
just handed all of them.

| Setting | Status |
| --- | --- |
| `PodmanArgs=--privileged` | **required** — the entrypoint exits without it, measured |
| `PidsLimit=` | **not set** — systemd plus the Proxmox services, and no measurement to base a number on |
| `ReadOnly=true` | **not attempted** — systemd as PID 1 needs a writable `/run` and more |
| `User=` | **not attempted** — PID 1 here is `/sbin/init` |
| `DropCapability=ALL` | **pointless** — `--privileged` grants them back |

If you measure a working `PidsLimit`, record it here with the number and how
you arrived at it.

## Auto-update

No `AutoUpdate=` — an explicit tag (`9.2.9`), bumped by hand
([rule 9](../../docs/conventions.md)). Read the Proxmox release notes before
bumping a minor: the configuration database in `/var/lib/pve-cluster` is
migrated on start, and that is not a step to take blind.

`install.ini` carries an `[upstream]` override because the image is
`dockurr/proxmox` (two r's) and the repository is `dockur/proxmox` — without
that line `updates.py` derives the wrong name and reports no releases.

## Backup & recovery

```bash
systemctl --user stop proxmox
tar -czf proxmox-backup-$(date +%Y%m%d-%H%M%S).tar.gz \
  -C ~/.config/containers/volumes proxmox
systemctl --user start proxmox
```

Cold on purpose: `/var/lib/pve-cluster` is a live SQLite database, and copying
it while Proxmox writes gives you an archive that only reveals itself as
corrupt when you restore it. The storage pool goes in the same tarball, so the
size follows whatever VMs you created inside.

## Useful commands

```bash
systemctl --user status proxmox
podman logs -f proxmox
podman exec proxmox pvecm status          # cluster state, from inside
podman exec proxmox df -h /var/lib/vz     # how much the storage pool has grown
```

## Credits

Quadlet deploy based on [dockur/proxmox](https://github.com/dockur/proxmox)
(MIT). Proxmox VE is a product of Proxmox Server Solutions GmbH; this
repository is not affiliated with or endorsed by them.
