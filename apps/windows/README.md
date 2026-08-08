# Windows — Podman Quadlet (rootless)

**[🇧🇷 Leia em português](./README.pt-BR.md)**

A [dockur/windows](https://github.com/dockur/windows) deploy via Podman
Quadlet, using the official `docker.io/dockurr/windows` image.

A real Windows VM under QEMU/KVM, wrapped in a container. It installs itself
on first boot — the image downloads the chosen edition from Microsoft's own
servers — and afterwards you reach the desktop in a browser on port 8006 or
over RDP on 3389. Useful for the one program that has no Linux build, and for
testing something you would rather not run on the host.

**You still need a Windows licence.** The image fetches official Microsoft
media, which is free to download; activating what it installs is between you
and Microsoft, and this repository does not change that.

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

  If the device is `crw-rw----` and owned by `root:kvm`, add yourself to the
  `kvm` group and log back in.

- **`/dev/net/tun`**, which the container uses for the VM's network.
- **Disk.** Upstream asks for 32 GB free; a Windows 11 install lands around
  20 GB and grows. It goes in the volume, under your home directory — see
  "Where the disk lives" below.
- **RAM.** `RAM_SIZE` is reserved for the VM's whole lifetime, not borrowed on
  demand. The default 4 GB is 4 GB the host no longer has.

## Architecture

A single container running QEMU. One volume, `/storage`, holding the virtual
disk and the downloaded installation media. Three published ports:

| Port | What |
| --- | --- |
| `8006` | the web viewer — the desktop in a browser, no client to install |
| `3389/tcp`, `3389/udp` | RDP, for a real client with sound and clipboard |

The first start is not like the others: it downloads several GB and runs the
whole Windows installer unattended. `TimeoutStartSec=600` and a five-minute
`HealthStartPeriod` exist for that. Watch it happen at `http://<host-ip>:8006`.

## Files

```
windows.container   # main unit
.env.example        # edition, RAM, cores, disk size, language
install.ini         # secret recipe + the upstream override
```

## Installation

```bash
python3 install.py windows            # dry-run: shows what it will do
python3 install.py windows --apply
```

For the local network only, `--access local`; on the tailnet and the LAN,
`--access both`. The script creates the directory, writes the `.env`, generates
the password, starts the service and prints the address at the end — see
[Installing and operating](../../docs/installing.md).

Then open `http://<host-ip>:8006` and watch the install. It takes a while.

<details>
<summary><b>Manual installation</b> (advanced) — the same steps, one at a time</summary>


```bash
# 1. Download the unit (no need to clone the repository)
mkdir -p ~/.config/containers/systemd
wget -P ~/.config/containers/systemd/ \
  https://raw.githubusercontent.com/wallacepnts/quadlet-homelab/main/apps/windows/windows.container

# 2. Directories
mkdir -p ~/.config/containers/volumes/windows/storage
mkdir -p ~/.config/containers/env

# 3. Environment
wget -O ~/.config/containers/env/windows.env \
  https://raw.githubusercontent.com/wallacepnts/quadlet-homelab/main/apps/windows/.env.example

# 4. Secret — the RDP password for the `Docker` account
podman secret create windows-password - <<< "$(python3 -c 'import secrets,string;a=string.ascii_letters+string.digits;print("".join(secrets.choice(a) for _ in range(20)))')"

# 5. Start it
systemctl --user daemon-reload
systemctl --user start windows
```

</details>

## Choosing the edition and language

`install.py` asks, on the first install:

```
  Which Windows to install (downloaded on first boot)
    1) 11        Windows 11 Pro — 7.9 GB  (default)
    2) 11l       Windows 11 LTSC — 4.7 GB, no Store, long-term servicing
   ...
  number or value [11]:
```

Answer with the number, with the value itself, or press Enter for the default.
Both settings only matter on the **first** start — the edition and its language
are downloaded then and never looked at again. Changing your mind later means
deleting the volume and starting over.

Without a terminal (`--prefix`, a script, CI) it does not ask: the defaults are
kept and a warning tells you which file to edit before the first start.

### Editions

| Value | Edition | Download |
| --- | --- | --- |
| `11` | Windows 11 Pro | 7.9 GB |
| `11l` | Windows 11 LTSC | 4.7 GB |
| `11e` | Windows 11 Enterprise | 6.6 GB |
| `10` | Windows 10 Pro | 5.7 GB |
| `10l` | Windows 10 LTSC | 4.6 GB |
| `10e` | Windows 10 Enterprise | 5.2 GB |
| `2025` | Windows Server 2025 | 7.6 GB |
| `2022` | Windows Server 2022 | 6.0 GB |
| `2019` | Windows Server 2019 | 5.3 GB |
| `2016` | Windows Server 2016 | 6.5 GB |
| `2012` | Windows Server 2012 | 4.3 GB |
| `2008` | Windows Server 2008 | 3.0 GB |
| `2003` | Windows Server 2003 | 0.6 GB |
| `tiny11` | Tiny11 | 5.3 GB |
| `core11` | Tiny11 Core | 3.0 GB |
| `tiny10` | Tiny10 | 3.6 GB |
| `8e` | Windows 8.1 Enterprise | 3.7 GB |
| `7u` | Windows 7 Ultimate | 3.1 GB |
| `vu` | Windows Vista Ultimate | 3.0 GB |
| `xp` | Windows XP Professional | 0.6 GB |
| `2k` | Windows 2000 Professional | 0.4 GB |
| `reactos` | ReactOS | 0.1 GB |

`VERSION` also accepts a URL to your own ISO, which is why an unlisted answer is
taken as given rather than rejected. The Tiny builds are community remixes, not
Microsoft media. ReactOS is not Windows at all and needs no licence. ARM64 hosts
want [dockur/windows-arm](https://github.com/dockur/windows-arm/) instead.

### Languages

Arabic, Bulgarian, Chinese, Croatian, Czech, Danish, Dutch, English, Estonian,
Finnish, French, German, Greek, Hebrew, Hungarian, Italian, Japanese, Korean,
Latvian, Lithuanian, Norwegian, Polish, Portuguese, Romanian, Russian, Serbian,
Slovak, Slovenian, Spanish, Swedish, Thai, Turkish, Ukrainian.

The prompt lists the common ones; typing any of the names above works. For
Brazilian Portuguese, pick `Portuguese` and then set the variant in the `.env`:

```bash
REGION=pt-BR
KEYBOARD=pt-BR
```

## Security — read this before putting it on the tailnet

**The web viewer on 8006 has no login.** Whoever opens that URL is sitting at
the Windows desktop, already signed in. The unit ships with the tsdproxy labels
on, following this repository's default, which means every device on your
tailnet — and anything running on those devices — can reach it.

The RDP account is the piece that does have a password: upstream's default is
the user `Docker` with the literal password `admin`, and `install.ini` replaces
it with a generated one:

```bash
podman secret inspect --showsecret windows-password
```

That protects 3389. It does nothing for 8006.

If that trade is not what you want, install with `--access local` — the
tsdproxy labels are commented out rather than deleted, so changing your mind
later is an `--update` with another mode
([Installing and operating](../../docs/installing.md)).

Worth stating plainly: this container gets `/dev/kvm`, `/dev/net/tun` and
`NET_ADMIN`, and runs a full operating system you did not audit. It is a large
trust surface by construction, not by oversight.

## Where the disk lives

`DISK_SIZE` defaults to 64 GB. The image is sparse — it grows as Windows writes
rather than being allocated up front — but it still ends up in
`~/.config/containers/volumes/windows/storage`, which is probably on the same
filesystem as everything else you own.

To put it somewhere with more room, point the volume at that path instead:

```ini
Volume=/mnt/big-disk/windows:/storage:Z
```

Change it **before** the first start. Moving it afterwards means stopping the
service and moving the directory by hand.

## Hardening — what was not attempted

Only `PidsLimit=512` beyond the defaults. The [rule 20](../../docs/conventions.md)
ladder does not really apply here, and the reasons are worth writing down
rather than leaving as an omission:

| Setting | Status |
| --- | --- |
| `PidsLimit=512` | on — QEMU plus the entrypoint's helper processes |
| `AddCapability=NET_ADMIN` | required by upstream, for the VM's tun networking |
| `ReadOnly=true` | **not attempted** — the entrypoint writes to `/run` and unpacks media into the image's own layers |
| `User=` | **not attempted** — QEMU is started as root by `tini`/`entry.sh` |
| `DropCapability=ALL` | **not attempted** — untested, and a wrong list here shows up as a VM that boots without networking rather than as a clear error |

Testing any of these properly means a full Windows install per attempt, which
is why none of them were measured. If you do measure one, record it here with
the error.

Memory is not capped in the unit. If you want a ceiling, it has to exceed
`RAM_SIZE` with room for QEMU itself — `Memory=6G` for the default `RAM_SIZE=4G`.

## Auto-update

No `AutoUpdate=` — an explicit tag (`6.04`), bumped by hand
([rule 9](../../docs/conventions.md)). The tag is the *container's* version, not
Windows': bumping it updates QEMU and the installer scripts and leaves the
installed Windows alone, which keeps updating itself from the inside as any
Windows does.

`install.ini` carries an `[upstream]` override because the image is
`dockurr/windows` (two r's) and the repository is `dockur/windows` — without
that line `updates.py` derives the wrong name and finds nothing.

## Backup & recovery

```bash
systemctl --user stop windows
tar -czf windows-backup-$(date +%Y%m%d-%H%M%S).tar.gz \
  -C ~/.config/containers/volumes windows
systemctl --user start windows
```

Cold on purpose — copying a running VM's disk gives you an archive that only
reveals itself as corrupt when you restore it. Note the size: this is the
whole virtual disk, tens of gigabytes, which is a different proposition from
every other backup in this repository.

## Useful commands

```bash
systemctl --user status windows
podman logs -f windows                 # the install progress is here
podman exec windows df -h /storage     # how much the disk has actually grown
```

## Credits

Quadlet deploy based on [dockur/windows](https://github.com/dockur/windows)
(MIT), which builds on [qemus/qemu](https://github.com/qemus/qemu).
