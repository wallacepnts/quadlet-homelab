# VM — Podman Quadlet (rootless)

**[🇧🇷 Leia em português](./README.pt-BR.md)**

Full operating systems in VMs, each in its own container, with the screen
served in a browser. Three guests, one engine.

| Unit | Guest | Image | Viewer | Also |
| --- | --- | --- | --- | --- |
| `vm-qemu` | any Linux, or your own ISO | [qemus/qemu](https://github.com/qemus/qemu) | 8007 | — |
| `vm-windows` | Windows 11 down to 2000 | [dockur/windows](https://github.com/dockur/windows) | 8006 | RDP 3389 |
| `vm-macos` | macOS 11 to 26 | [dockur/macos](https://github.com/dockur/macos) | 8008 | VNC 5900 |
| `vm-windows-arm` | ARM64 Windows, on an ARM host | [dockur/windows-arm](https://github.com/dockur/windows-arm) | 8006 | RDP 3389 |
| `vm-zima` | ZimaOS, a NAS interface | [dockur/zima](https://github.com/dockur/zima) | 8012 | web UI 8011 |
| `vm-chromeos` | ChromeOS Flex | [dockur/chromeos](https://github.com/dockur/chromeos) | 8013 | VNC 5901 |

The three are the same engine: `dockur/windows` and `dockur/macos` are both
built `FROM qemux/qemu` with an installer bolted on. That is why they all want
port 8006 inside, and why they are one folder here rather than three.

Take the ones you want — nothing here requires anything else:

```bash
python3 install.py vm-qemu --apply          # just the Linux one
python3 install.py vm --apply               # all three
```

## Requirements

**Pick the unit that matches the host.** KVM only accelerates a guest of the
same architecture as the host, so the guest — not the container image — is what
decides. All four images are multi-arch, and that multi-arch is about which
*host* they run on, not which Windows they install:

| Host | Windows | Linux | macOS |
| --- | --- | --- | --- |
| x86_64 | `vm-windows` | `vm-qemu` | `vm-macos` |
| ARM64 | `vm-windows-arm` | [qemus/qemu-arm](https://github.com/qemus/qemu-arm/), not packaged here | — |

`vm-windows` and `vm-windows-arm` are genuinely different images — same tag,
different digests — and they publish the same ports on purpose, because a host
is one architecture or the other and the two never run together. That is what
the `# check: ignore ports` line in the ARM unit is for.

macOS has no ARM path at all: `dockurr/macos` is `amd64` only, and it emulates
an Intel Mac, which is a different machine from Apple Silicon.

**None of the ARM side is tested here** — this repository's host is x86_64, so
`vm-windows-arm` is written from upstream's documentation rather than measured.
Treat it as a starting point, and record what you find.

Shared by all three, beyond the usual rootless Podman:

- **KVM on the host.** `/dev/kvm` must exist and be readable and writable by
  the user running Podman. Without it a VM either refuses to start or falls
  back to software emulation, which is unusably slow.

  ```bash
  ls -l /dev/kvm                          # must exist
  [ -r /dev/kvm ] && [ -w /dev/kvm ] && echo ok
  ```

  `/dev/kvm` existing at all is the better test: the device is created by the
  kernel module, so its presence proves virtualisation is really enabled rather
  than merely present on the CPU. If it is `crw-rw----` and owned by
  `root:kvm`, add yourself to the `kvm` group and log back in.

- **`/dev/net/tun`**, for the VMs' networking.
- **RAM.** `RAM_SIZE` is reserved for a VM's whole lifetime, not borrowed on
  demand. Whatever you give it is RAM the host no longer has.
- **Disk.** The images grow on demand but live in the volume, under your home
  directory. Windows lands around 20 GB, macOS wants about 40.

**macOS needs one more: AVX2 on the CPU.** It is a hard requirement, not a
performance note — Intel Haswell (4th generation Core) or AMD Zen (Ryzen 1000)
and newer:

```bash
grep -qo avx2 /proc/cpuinfo && echo ok || echo "no AVX2 — macOS will not run"
```

## Architecture

Each unit runs QEMU with one volume at `/storage`, holding that guest's virtual
disk and its downloaded installation media. The volumes do not overlap:
`volumes/vm/{qemu,windows,macos}`.

There is no `Requires=` between them — they are alternatives, not a stack.
Running two at once is fine if the host has the RAM.

The first start of any of them downloads several GB and runs an installer,
which is why they carry `TimeoutStartSec=600` and long `HealthStartPeriod`s.
`install.py` follows the container log while systemd waits, so that wait is
visible rather than a hung-looking terminal.

## Files

```
vm-qemu.container       vm-qemu.env.example
vm-windows.container    vm-windows.env.example
vm-macos.container      vm-macos.env.example
vm-windows-arm.container  vm-windows-arm.env.example
vm-zima.container       vm-zima.env.example
vm-chromeos.container   vm-chromeos.env.example
install.ini             # per-unit questions, the Windows secret, upstream overrides
```

## Installation

```bash
python3 install.py vm            # dry-run: shows what it will do
python3 install.py vm --apply    # all three
```

Installing the folder writes all three units and stops without starting
anything — with no single main unit it will not guess which guest you want:

```bash
systemctl --user start vm-qemu        # or vm-windows, or vm-macos
```

Naming a unit instead installs and starts just that one. Either way the units
land in `systemd/vm/`, so adding another later is the same command again.

<details>
<summary><b>Manual installation</b> (advanced) — the same steps, one at a time</summary>


```bash
# 1. Download the unit you want (no need to clone the repository)
mkdir -p ~/.config/containers/systemd/vm
wget -P ~/.config/containers/systemd/vm/ \
  https://raw.githubusercontent.com/wallacepnts/quadlet-homelab/main/apps/vm/vm-qemu.container

# 2. Directories
mkdir -p ~/.config/containers/volumes/vm/qemu/storage
mkdir -p ~/.config/containers/env

# 3. Environment
wget -O ~/.config/containers/env/vm-qemu.env \
  https://raw.githubusercontent.com/wallacepnts/quadlet-homelab/main/apps/vm/vm-qemu.env.example

# 4. Windows only — the RDP password for the `Docker` account
podman secret create vm-windows-password - <<< "$(python3 -c 'import secrets,string;a=string.ascii_letters+string.digits;print("".join(secrets.choice(a) for _ in range(20)))')"

# 5. Start it
systemctl --user daemon-reload
systemctl --user start vm-qemu
```

</details>

## Choosing the guest

`install.py` asks once per unit, on the first install. It only matters then —
after that the OS is downloaded and installed, and the value is never read
again. Changing your mind means wiping that guest's volume.

### `vm-qemu` — `BOOT`

23 Linux distributions, from Alpine at 60 MB to CentOS at 7 GB:

`alpine` · `suse` · `arch` · `zima` · `tails` · `rocky` · `alma` · `mx` ·
`fedora` · `nixos` · `cachy` · `mint` · `ubuntus` · `debian` · `gentoo` ·
`slack` · `kali` · `zorin` · `xubuntu` · `manjaro` · `kubuntu` · `ubuntu` ·
`centos`

**`alpine` is the default here**, where upstream uses `mint`. At 60 MB it
proves the whole path — KVM, tun, disk, viewer — in about a minute, instead of
a 2.8 GB download before you learn whether anything works.

`BOOT` also takes the URL of any ISO, which is why an answer that is not on the
list is taken as given rather than rejected.

### `vm-windows` — `VERSION` and `LANGUAGE`

| Value | Edition | Download |
| --- | --- | --- |
| `11` | Windows 11 Pro | 7.9 GB |
| `11l` | Windows 11 LTSC | 4.7 GB |
| `11e` | Windows 11 Enterprise | 6.6 GB |
| `10` | Windows 10 Pro | 5.7 GB |
| `10l` | Windows 10 LTSC | 4.6 GB |
| `10e` | Windows 10 Enterprise | 5.2 GB |
| `2025` `2022` `2019` `2016` `2012` `2008` `2003` | Windows Server | 3.0–7.6 GB |
| `tiny11` | Tiny11 | 5.3 GB |
| `core11` | Tiny11 Core | 3.0 GB |
| `tiny10` | Tiny10 | 3.6 GB |
| `8e` | Windows 8.1 Enterprise | 3.7 GB |
| `7u` | Windows 7 Ultimate | 3.1 GB |
| `vu` | Windows Vista Ultimate | 3.0 GB |
| `xp` | Windows XP Professional | 0.6 GB |
| `2k` | Windows 2000 Professional | 0.4 GB |
| `reactos` | ReactOS | 0.1 GB |

`LANGUAGE` takes any of 33 names in English (`German`, `Portuguese`, …). For
Brazilian Portuguese, pick `Portuguese` and set `REGION=pt-BR` and
`KEYBOARD=pt-BR` in the `.env`.

**`xp` and `2003` do not currently work.** Upstream hardcodes a virtio-blk
controller for them:

```bash
# dockur/windows, src/install.sh
"winxpx"* | "win2003"* )
  writeState "type" "blk"
```

while `getDriverFolder()` in `src/define.sh` has no entry below Vista — so
there is no virtio driver to install. Setup completes, then the installed
system stops at **STOP 0x7B INACCESSIBLE_BOOT_DEVICE**, because it has no
driver for the disk it was installed on. Setting `DISK_TYPE` does not help: the
hardcoded write runs on every start and overwrites it. Vista and newer are
fine.

### `vm-windows-arm` — `VERSION` and `LANGUAGE`

A shorter list than x64's, because those are the only Windows editions that
ever shipped an ARM64 build — no XP, Vista, 7, or Server:

| Value | Edition | Download |
| --- | --- | --- |
| `11` | Windows 11 Pro | 7.5 GB |
| `11l` | Windows 11 LTSC | 4.7 GB |
| `11e` | Windows 11 Enterprise | 4.3 GB |
| `10` | Windows 10 Pro | 3.5 GB |
| `10l` | Windows 10 LTSC | 4.1 GB |
| `10e` | Windows 10 Enterprise | 3.4 GB |
| `tiny11` | Tiny11 | 5.1 GB |
| `core11` | Tiny11 Core | 3.0 GB |

`LANGUAGE` works the same as on the x64 unit.

### `vm-macos` — `VERSION`

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

**macOS is Apple hardware only.** Upstream states it plainly:

> *by installing Apple's macOS, you must accept their end-user license
> agreement, which does not permit installation on non-official hardware. So
> only run this container on hardware sold by Apple, as any other use will be a
> violation of their terms and conditions.*

That is sharper than the Windows case: there you buy a licence and you are
done, here Apple's EULA offers no path for non-Apple hardware at all. The
software will run; whether you are permitted to run it is a separate question,
and yours to answer.

Unlike Windows, the macOS install is **not** unattended — you drive it. The two
steps people miss: erase the largest `Apple Inc. VirtIO Block Media` disk in
`Disk Utility` before the installer accepts it, and choose `Set Up Later` then
`Skip` on the `Apple ID` screen.

### `vm-zima` — nothing to choose

ZimaOS is the guest, and there is no version to pick: the image installs the
release it ships with. Unlike the others, what you reach for day to day is not
the viewer but **ZimaOS's own web interface**, forwarded from the guest:

| Host port | What |
| --- | --- |
| `8011` | the ZimaOS interface — the one you actually use |
| `8012` | the QEMU viewer, for the first boot and for when the guest will not come up |

That forwarding is the reason this unit exists at all: `vm-qemu` can install
ZimaOS too (`BOOT=zima`), but it only gives you a screen. This one publishes
the services the guest runs.

The image also exposes **445** for SMB, which is not published here: rootless
Podman cannot bind a port below 1024 without lowering
`net.ipv4.ip_unprivileged_port_start`, and upstream's own compose leaves it
unpublished as well. [netbootxyz](../netbootxyz/) documents that sysctl change
if you decide you want it.

### `vm-chromeos` — `VERSION`, and the two things only this one has

ChromeOS Flex tracks a channel rather than a version:

| Value | Channel | Cadence |
| --- | --- | --- |
| `stable` | Stable | ~4 weeks |
| `ltc` | Long-Term Channel | ~6 months |
| `ltr` | Long-Term Release | ~18 months |
| `beta` | Beta | ~weekly |

**It is the only unit here with a login on the viewer.** `PROTECT=Y` puts HTTP
basic auth in front of port 8006, with the password generated by `install.py`:

```bash
podman secret inspect --showsecret vm-chromeos-password
```

Upstream's default is `Docker` / `admin`; the `.env` sets the user and the
secret sets the password. The other units in this folder have no such option —
their viewers are open to whoever reaches them.

**It is also the only one that uses the GPU.** The unit bind-mounts
`/dev/dri` and adds a cgroup rule for DRM's major number, which is what
upstream requires for QEMU's VirGL backend:

```ini
Volume=/dev/dri:/dev/dri:rw
PodmanArgs=--device-cgroup-rule=c 226:* rwm
```

No `:Z` on that mount, deliberately — relabelling the host's device nodes is
not something a container should do. Check that your user can reach the render
node before expecting acceleration:

```bash
[ -r /dev/dri/renderD128 ] && [ -w /dev/dri/renderD128 ] && echo ok
```

If it cannot, join the `render` and `video` groups. Without a usable node the
container falls back to software rendering, which upstream measures at 3–15
fps — it still works, it is just miserable.

**x86_64 only.** `dockurr/chromeos` publishes no `arm64` image, the second unit
here in that position after `vm-macos`.

## Windows apps on the Linux desktop (WinApps)

[WinApps](https://github.com/winapps-org/winapps) renders individual Windows
programs as ordinary windows next to your Linux ones, using this VM as the
backend and FreeRDP as the renderer. It splits in two, and only one half lives
here.

**The container half is `vm-windows`, already.** Same `dockur/windows` image,
RDP published on 3389 over TCP and UDP, the Windows password already a podman
secret. Comparing upstream's `compose.yaml` with this unit, two mounts were
what it lacked, and both are in place now:

| mount | what it does |
| --- | --- |
| `oem/` → `/oem` | dockur runs `/oem/install.bat` once, after Windows installs. It imports `RDPApps.reg` — the registry change that turns RDP into per-application windows instead of a full desktop. Without it there is no WinApps. |
| `shared/` → `/shared` | shows up inside Windows as `\\host.lan\Data`, for moving files between the two |

The `oem/` files are **not** kept in this repository — they are fetched from
WinApps directly, once, before the first boot:

```bash
mkdir -p ~/.config/containers/volumes/vm/windows/oem
for f in install.bat RDPApps.reg Container.reg NetProfileCleanup.ps1 TimeSync.ps1; do
  wget -O ~/.config/containers/volumes/vm/windows/oem/$f https://raw.githubusercontent.com/winapps-org/winapps/main/oem/$f
done
```

They are not vendored on purpose. WinApps' `LICENSE.md` says the parts
inherited from the original project are "not free software […] All Rights
Reserved by the original author", that most of the rest is AGPLv3, and to
"refer to a specific file for its respective license" — and none of these five
files carries a notice. Fetching them from their own repository leaves that
question where it belongs.

**It has to be there before the first boot.** dockur runs the `/oem` hook once,
as part of the Windows install; putting the files in afterwards does nothing,
and the fix is to delete the storage volume and install Windows again.

### One deliberate difference from upstream

Upstream mounts your **entire home directory** as `/shared`. This unit mounts a
dedicated `shared/` folder instead, because on this host the home holds
`~/.config/containers/secrets/` — every service's password, in the clear. A
Windows VM runs arbitrary Windows software; handing it read-write access to
that directory is not a trade this repository makes by default.

If you want the wider mount anyway, it is one line in the unit:
`Volume=%h:/shared:z`.

### The host half is not a Quadlet

WinApps itself is a shell script, a set of `.desktop` files and FreeRDP 3+,
installed on the host by upstream's `installer.sh` with its configuration in
`~/.config/winapps/winapps.conf`. It is the same category as Tailscale
([rule 21](../../docs/conventions.md)): it has to be *on* the desktop session,
not in a container.

On openSUSE MicroOS that means FreeRDP comes in through
`transactional-update`, which needs a reboot — so it is a decision to take
deliberately, not a step to run mid-install.

## Security — read this before putting any of them on the tailnet

**Most of the viewers have no login.** Whoever opens the URL has that VM's
screen, keyboard and mouse, already signed in. They all ship with the tsdproxy
labels on, following this repository's default, which means every device on
your tailnet — and anything running on those devices — can reach them.

`vm-chromeos` is the exception: it supports `PROTECT=Y`, and the unit turns it
on. The other five have no equivalent — the option does not exist in their
images.

Windows has a second door with a password: RDP on 3389, where upstream's
default is the user `Docker` with the literal password `admin` and `install.ini`
replaces it with a generated one:

```bash
podman secret inspect --showsecret vm-windows-password
```

That protects 3389. It does nothing for the viewer.

If that trade is not what you want, install with `--access local` — the
tsdproxy labels are commented out rather than deleted, so changing your mind
later is an `--update` with another mode
([Installing and operating](../../docs/installing.md)).

Worth stating plainly: these containers get `/dev/kvm`, `/dev/net/tun` and
`NET_ADMIN`, and run full operating systems you did not audit. That is a large
trust surface by construction, not by oversight.

## Hardening — what was not attempted

Only `PidsLimit=512` beyond the defaults, on all three:

| Setting | Status |
| --- | --- |
| `PidsLimit=512` | on — QEMU plus the entrypoint's helper processes |
| `AddCapability=NET_ADMIN` | required by upstream, for the VMs' tun networking |
| `ReadOnly=true` | **not attempted** — the entrypoint writes to `/run` and unpacks media |
| `User=` | **not attempted** — QEMU is started as root by the entrypoint |
| `DropCapability=ALL` | **not attempted** — untested, and a wrong list shows up as a VM that boots without networking rather than as a clear error |

Testing any of these means a full OS install per attempt. `vm-qemu` with
`alpine` makes that far cheaper than the other two — if you do measure one,
record it here with the error.

Memory is not capped. A ceiling has to exceed `RAM_SIZE` with room for QEMU
itself.

## Auto-update

No `AutoUpdate=` — explicit tags, bumped by hand
([rule 9](../../docs/conventions.md)). Each tag is the *container's* version,
not the guest's: bumping it updates QEMU and the helper scripts and leaves the
installed OS alone.

`install.ini` carries `[upstream]` overrides for two of the three, because the
image names do not match their repositories — `dockurr` has two r's, and the
QEMU org is `qemus` with an s. Without those lines `updates.py` derives the
wrong names and finds nothing.

## Backup & recovery

Per guest, and cold on purpose — copying a running VM's disk gives you an
archive that only reveals itself as corrupt when you restore it:

```bash
systemctl --user stop vm-windows
tar -czf vm-windows-backup-$(date +%Y%m%d-%H%M%S).tar.gz \
  -C ~/.config/containers/volumes/vm windows
systemctl --user start vm-windows
```

Mind the size: these are whole virtual disks, tens of gigabytes each — a
different proposition from every other backup in this repository.

## Useful commands

```bash
podman ps --filter "name=vm-"
systemctl --user status vm-qemu
podman logs -f vm-windows                 # install progress is here
podman exec vm-macos df -h /storage       # how much the disk has actually grown
```

## Credits

Quadlet deploy based on [qemus/qemu](https://github.com/qemus/qemu),
[dockur/windows](https://github.com/dockur/windows) and
[dockur/macos](https://github.com/dockur/macos), all MIT. Not affiliated with,
endorsed by, or sponsored by Microsoft or Apple.

The WinApps integration follows
[winapps-org/winapps](https://github.com/winapps-org/winapps); its `oem/` files
are fetched from that repository rather than copied into this one, for the
licensing reason explained above.
