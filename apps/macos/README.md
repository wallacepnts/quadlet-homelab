# macOS — Podman Quadlet (rootless)

**[🇧🇷 Leia em português](./README.pt-BR.md)**

A [dockur/macos](https://github.com/dockur/macos) deploy via Podman Quadlet,
using the official `docker.io/dockurr/macos` image.

A macOS VM under QEMU/KVM, wrapped in a container. It downloads Apple's
recovery image on first boot and you drive the installer in a browser on port
8008, or over VNC on 5900.

## Read this first: Apple hardware only

The project is open source and distributes no Apple code. What it installs is
not free of terms, though, and upstream states it plainly:

> *by installing Apple's macOS, you must accept their end-user license
> agreement, which does not permit installation on non-official hardware. So
> only run this container on hardware sold by Apple, as any other use will be a
> violation of their terms and conditions.*

This is a sharper constraint than the one on [Windows](../windows/): there you
buy a licence and you are done, here Apple's EULA offers no path for non-Apple
hardware at all. If this host is not a Mac, installing macOS on it breaches
those terms — the software will run, and that is a separate question from
whether you are permitted to run it.

The unit is here because the rest of this repository documents what it deploys.
Whether to deploy it is yours to decide.

## Requirements

Beyond the usual rootless Podman:

- **KVM on the host**, same as [Windows](../windows/) and [QEMU](../qemu/):

  ```bash
  ls -l /dev/kvm                          # must exist
  [ -r /dev/kvm ] && [ -w /dev/kvm ] && echo ok
  ```

- **AVX2 on the CPU** — this one is specific to macOS, and it is a hard
  requirement rather than a performance note. Intel Haswell (4th generation
  Core) or AMD Zen (Ryzen 1000) and newer:

  ```bash
  grep -qo avx2 /proc/cpuinfo && echo ok || echo "no AVX2 — it will not run"
  ```

- **`/dev/net/tun`**, for the VM's network.
- **Disk.** Upstream asks for 64 GB free, and the installer alone wants around
  40 GB. This is the heaviest guest in the repository.
- **RAM.** `RAM_SIZE` is reserved for the VM's whole lifetime. Upstream's floor
  is 4 GB, which is 4 GB the host no longer has.

## Architecture

A single container running QEMU. One volume, `/storage`, holding the virtual
disk and the downloaded recovery image. Two ways in:

| Port | What |
| --- | --- |
| `8008` | the web viewer — the screen in a browser (8006 inside the container) |
| `5900/tcp`, `5900/udp` | VNC, for a real client |

8006 and 8007 are already taken by [Windows](../windows/) and [QEMU](../qemu/),
which are the same engine underneath — hence 8008 here.

## Files

```
macos.container     # main unit
.env.example        # version, RAM, cores, disk size
install.ini         # the version question + the upstream override
```

## Installation

```bash
python3 install.py macos            # dry-run: shows what it will do
python3 install.py macos --apply
```

It asks which macOS to install, then downloads the image with podman's progress
on screen — see [Installing and operating](../../docs/installing.md).

Then open `http://<host-ip>:8008`. Unlike Windows, **the install is not
unattended**: you drive it. Upstream's own walkthrough is the reference, and
the two steps people miss are

1. In `Disk Utility`, erase the largest `Apple Inc. VirtIO Block Media` disk
   before the installer will accept it as a target.
2. On the `Apple ID` screen, choose `Set Up Later` and then `Skip`.

<details>
<summary><b>Manual installation</b> (advanced) — the same steps, one at a time</summary>


```bash
# 1. Download the unit (no need to clone the repository)
mkdir -p ~/.config/containers/systemd
wget -P ~/.config/containers/systemd/ \
  https://raw.githubusercontent.com/wallacepnts/quadlet-homelab/main/apps/macos/macos.container

# 2. Directories
mkdir -p ~/.config/containers/volumes/macos/storage
mkdir -p ~/.config/containers/env

# 3. Environment — edit VERSION if you do not want Sequoia
wget -O ~/.config/containers/env/macos.env \
  https://raw.githubusercontent.com/wallacepnts/quadlet-homelab/main/apps/macos/.env.example

# 4. Start it
systemctl --user daemon-reload
systemctl --user start macos
```

</details>

## Choosing the version

`install.py` asks on the first install. It only matters then — after that the
recovery image is downloaded and the value is never read again.

| Value | Version | Name |
| --- | --- | --- |
| `15` | macOS 15 | Sequoia |
| `14` | macOS 14 | Sonoma |
| `13` | macOS 13 | Ventura |
| `12` | macOS 12 | Monterey |
| `11` | macOS 11 | Big Sur |
| `26` | macOS 26 | Tahoe |

`26` is accepted but upstream advises against it — it runs very slowly, for
reasons they say they have not identified.

## Security — read this before putting it on the tailnet

**The viewer on 8008 has no login**, and neither does VNC on 5900 by default.
Whoever opens that URL has the VM's screen, keyboard and mouse. The unit ships
with the tsdproxy labels on, following this repository's default, which means
every device on your tailnet — and anything running on those devices — can
reach it.

If that trade is not what you want, install with `--access local` — the
tsdproxy labels are commented out rather than deleted, so changing your mind
later is an `--update` with another mode
([Installing and operating](../../docs/installing.md)).

Worth stating plainly: this container gets `/dev/kvm`, `/dev/net/tun` and
`NET_ADMIN`, and runs a full operating system. It is a large trust surface by
construction, not by oversight.

## Hardening — what was not attempted

Only `PidsLimit=512` beyond the defaults, for the same reasons as
[Windows](../windows/) and [QEMU](../qemu/):

| Setting | Status |
| --- | --- |
| `PidsLimit=512` | on — QEMU plus the entrypoint's helper processes |
| `AddCapability=NET_ADMIN` | required by upstream, for the VM's tun networking |
| `ReadOnly=true` | **not attempted** — the entrypoint writes to `/run` and unpacks media |
| `User=` | **not attempted** — QEMU is started as root by the entrypoint |
| `DropCapability=ALL` | **not attempted** — untested, and a wrong list shows up as a VM that boots without networking rather than as a clear error |

Testing any of these means a full macOS install per attempt, which is the most
expensive test in this repository. None were measured.

Memory is not capped in the unit. A ceiling has to exceed `RAM_SIZE` with room
for QEMU itself — `Memory=6G` for the default `RAM_SIZE=4G`.

## Auto-update

No `AutoUpdate=` — an explicit tag (`3.09`), bumped by hand
([rule 9](../../docs/conventions.md)). The tag is the container's version, not
macOS': bumping it updates QEMU and the helper scripts and leaves the installed
system alone.

`install.ini` carries an `[upstream]` override because the image is
`dockurr/macos` (two r's) and the repository is `dockur/macos` — without that
line `updates.py` derives the wrong name and finds nothing.

## Backup & recovery

```bash
systemctl --user stop macos
tar -czf macos-backup-$(date +%Y%m%d-%H%M%S).tar.gz \
  -C ~/.config/containers/volumes macos
systemctl --user start macos
```

Cold on purpose — copying a running VM's disk gives you an archive that only
reveals itself as corrupt when you restore it. This is the largest backup in
the repository: the whole virtual disk, tens of gigabytes.

## Useful commands

```bash
systemctl --user status macos
podman logs -f macos                 # the download progress is here
podman exec macos df -h /storage     # how much the disk has actually grown
```

## Credits

Quadlet deploy based on [dockur/macos](https://github.com/dockur/macos) (MIT),
which builds on [qemus/qemu](https://github.com/qemus/qemu) — the same base as
[QEMU](../qemu/) and [Windows](../windows/) here. Not affiliated with, endorsed
by, or sponsored by Apple Inc.
