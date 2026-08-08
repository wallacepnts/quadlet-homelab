# QEMU — Podman Quadlet (rootless)

**[🇧🇷 Leia em português](./README.pt-BR.md)**

A [qemus/qemu](https://github.com/qemus/qemu) deploy via Podman Quadlet, using
the official `docker.io/qemux/qemu` image.

A VM under QEMU/KVM wrapped in a container, with the screen served in a
browser. Pick an OS from a list of 23, or point it at any ISO you like, and it
installs itself on first boot. Somewhere to try a distro, reproduce a bug on
another kernel, or keep a machine you can throw away.

This is the same engine [Windows](../windows/) runs on — that image is this one
with a Windows installer bolted on. Use this when the guest is not Windows.

## Requirements

Beyond the usual rootless Podman:

- **KVM on the host.** `/dev/kvm` must exist and be readable and writable by
  the user running Podman. Without it the VM either refuses to start or falls
  back to software emulation, which is unusably slow.

  ```bash
  ls -l /dev/kvm                          # must exist
  [ -r /dev/kvm ] && [ -w /dev/kvm ] && echo ok
  grep -oE 'vmx|svm' /proc/cpuinfo | head -1   # VT-x or AMD-V, enabled in firmware
  ```

  `/dev/kvm` existing at all is the better test: the device is created by the
  kernel module, so its presence proves virtualisation is really enabled rather
  than merely present on the CPU. If it is `crw-rw----` and owned by
  `root:kvm`, add yourself to the `kvm` group and log back in.

- **`/dev/net/tun`**, which the container uses for the VM's network.
- **Disk.** `DISK_SIZE` defaults to 32 GB here (upstream uses 64). The image
  grows on demand, but it lives in the volume, under your home directory.
- **RAM.** `RAM_SIZE` is reserved for the VM's whole lifetime, not borrowed on
  demand. The default 2 GB is 2 GB the host no longer has.

## Architecture

A single container running QEMU. One volume, `/storage`, holding the virtual
disk and the downloaded installation media. The screen is on **8007** on the
host, mapped to 8006 inside — 8006 is already taken by
[Windows](../windows/), which is the same image underneath.

The first start downloads the chosen OS and boots its installer, which is why
`TimeoutStartSec=600` and a three-minute `HealthStartPeriod` are here.

## Files

```
qemu.container      # main unit
.env.example        # OS, RAM, cores, disk size
install.ini         # the BOOT question + the upstream override
```

## Installation

```bash
python3 install.py qemu            # dry-run: shows what it will do
python3 install.py qemu --apply
```

It asks which OS to install, then downloads the image with podman's progress
on screen — see [Installing and operating](../../docs/installing.md).

Then open `http://<host-ip>:8007` and drive the installer.

<details>
<summary><b>Manual installation</b> (advanced) — the same steps, one at a time</summary>


```bash
# 1. Download the unit (no need to clone the repository)
mkdir -p ~/.config/containers/systemd
wget -P ~/.config/containers/systemd/ \
  https://raw.githubusercontent.com/wallacepnts/quadlet-homelab/main/apps/qemu/qemu.container

# 2. Directories
mkdir -p ~/.config/containers/volumes/qemu/storage
mkdir -p ~/.config/containers/env

# 3. Environment — edit BOOT to the OS you want
wget -O ~/.config/containers/env/qemu.env \
  https://raw.githubusercontent.com/wallacepnts/quadlet-homelab/main/apps/qemu/.env.example

# 4. Start it
systemctl --user daemon-reload
systemctl --user start qemu
```

</details>

## Choosing the OS

`install.py` asks on the first install. Answer with the number, the value
itself, or Enter for the default. It only matters on the **first** start —
after that the OS is installed and the value is never read again; changing your
mind means wiping the volume.

| Value | OS | Download |
| --- | --- | --- |
| `alpine` | Alpine Linux | 60 MB |
| `suse` | openSUSE | 1.0 GB |
| `arch` | Arch Linux | 1.2 GB |
| `zima` | ZimaOS | 1.4 GB |
| `tails` | Tails | 1.5 GB |
| `rocky` | Rocky Linux | 2.1 GB |
| `alma` | Alma Linux | 2.2 GB |
| `mx` | MX Linux | 2.2 GB |
| `fedora` | Fedora | 2.3 GB |
| `nixos` | NixOS | 2.4 GB |
| `cachy` | CachyOS | 2.6 GB |
| `mint` | Linux Mint | 2.8 GB |
| `ubuntus` | Ubuntu Server | 3.0 GB |
| `debian` | Debian | 3.3 GB |
| `gentoo` | Gentoo | 3.6 GB |
| `slack` | Slackware | 3.7 GB |
| `kali` | Kali Linux | 3.8 GB |
| `zorin` | Zorin OS | 3.8 GB |
| `xubuntu` | Xubuntu | 4.0 GB |
| `manjaro` | Manjaro | 4.1 GB |
| `kubuntu` | Kubuntu | 4.4 GB |
| `ubuntu` | Ubuntu Desktop | 6.0 GB |
| `centos` | CentOS | 7.0 GB |

**`alpine` is the default here**, where upstream uses `mint`. At 60 MB it
proves the whole path — KVM, tun, disk, viewer — in about a minute, instead of
a 2.8 GB download before you learn whether anything works.

`BOOT` also accepts the URL of any ISO, which is why an answer that is not on
the list is taken as given rather than rejected:

```bash
BOOT=https://dl-cdn.alpinelinux.org/alpine/v3.19/releases/x86_64/alpine-virt-3.19.1-x86_64.iso
```

## Security — read this before putting it on the tailnet

**The viewer on 8007 has no login.** Whoever opens that URL has the VM's
console, keyboard and mouse. The unit ships with the tsdproxy labels on,
following this repository's default, which means every device on your tailnet —
and anything running on those devices — can reach it.

Unlike [Windows](../windows/) there is no second door with a password here:
there is no RDP, and no account to protect. The console is the whole surface.

If that trade is not what you want, install with `--access local` — the
tsdproxy labels are commented out rather than deleted, so changing your mind
later is an `--update` with another mode
([Installing and operating](../../docs/installing.md)).

Worth stating plainly: this container gets `/dev/kvm`, `/dev/net/tun` and
`NET_ADMIN`, and runs whatever OS you pointed it at. It is a large trust
surface by construction, not by oversight.

## Hardening — what was not attempted

Only `PidsLimit=512` beyond the defaults, for the same reasons as
[Windows](../windows/):

| Setting | Status |
| --- | --- |
| `PidsLimit=512` | on — QEMU plus the entrypoint's helper processes |
| `AddCapability=NET_ADMIN` | required by upstream, for the VM's tun networking |
| `ReadOnly=true` | **not attempted** — the entrypoint writes to `/run` and unpacks media |
| `User=` | **not attempted** — QEMU is started as root by the entrypoint |
| `DropCapability=ALL` | **not attempted** — untested, and a wrong list shows up as a VM that boots without networking rather than as a clear error |

Testing any of these means a full OS install per attempt. `alpine` makes that
cheaper than it is for Windows, so if you do measure one, record it here with
the error.

Memory is not capped in the unit. A ceiling has to exceed `RAM_SIZE` with room
for QEMU itself — `Memory=4G` for the default `RAM_SIZE=2G`.

## Auto-update

No `AutoUpdate=` — an explicit tag (`7.44`), bumped by hand
([rule 9](../../docs/conventions.md)). The tag is QEMU's wrapper, not the
guest: bumping it updates the emulator and the viewer and leaves the installed
OS alone.

`install.ini` carries an `[upstream]` override because the Docker Hub user is
`qemux` (with an x) and the GitHub org is `qemus` (with an s) — without that
line `updates.py` derives the wrong name and reports no releases.

## Backup & recovery

```bash
systemctl --user stop qemu
tar -czf qemu-backup-$(date +%Y%m%d-%H%M%S).tar.gz \
  -C ~/.config/containers/volumes qemu
systemctl --user start qemu
```

Cold on purpose — copying a running VM's disk gives you an archive that only
reveals itself as corrupt when you restore it. The archive is the whole virtual
disk, so mind the size.

## Useful commands

```bash
systemctl --user status qemu
podman logs -f qemu                 # the install progress is here
podman exec qemu df -h /storage     # how much the disk has actually grown
```

## Credits

Quadlet deploy based on [qemus/qemu](https://github.com/qemus/qemu) (MIT).
