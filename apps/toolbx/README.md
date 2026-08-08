# Toolbx — Podman Quadlet (rootless)

**[🇧🇷 Leia em português](./README.pt-BR.md)**

Disposable distro shells. `dnf`, `apt` and `pacman` all live in here, so a
one-off tool, a quick compile or an unfamiliar binary runs in a container
instead of on the host. Four boxes, sitting idle until you step into one.

```bash
podman exec -it toolbx-fedora bash
```

That is the whole interface. Install what you need, use it, and when the box
gets messy delete the volume and start clean — the host never changed.

## The four

The images are the ones the [Toolbx](https://containertoolbx.org/) project
publishes, and the four distros are the ones it supports officially. They are
built for interactive use — `bash`, `git` and the usual shell tooling are
already in them, which a distro base image does not give you.

| Unit | Image | Package manager |
| --- | --- | --- |
| `toolbx-arch` | `quay.io/toolbx/arch-toolbox` (by digest) | `pacman -S` |
| `toolbx-fedora` | `registry.fedoraproject.org/fedora-toolbox:45` | `dnf install` |
| `toolbx-rhel` | `registry.access.redhat.com/ubi10/toolbox:10.2` | `dnf install` |
| `toolbx-ubuntu` | `quay.io/toolbx/ubuntu-toolbox:26.04` | `apt install` |

**Not the `toolbox` CLI.** These borrow the project's images and its distro
list, not its tooling: there is no `toolbox` command here and no `toolbox
enter` — just Quadlet units and `podman exec`. The trade is that these are
declared in this repository and survive a reboot, where `toolbox create` is
imperative and local to the machine you ran it on.

The images document `toolbox init-container` as their entry point, and these
units run `sleep infinity` instead. That command's job is to create a matching
user inside the container and bind-mount host paths — `/run/libvirt`,
`/run/systemd/journal`, `/var/log/journal` — to dissolve the boundary between
container and host. The host integration is the part worth skipping here; the
user it would create, `UserNS=keep-id` already provides, which is why `whoami`
and `$HOME` work inside. The images carry no entry point of their own
(the project requires that), so `Exec=` is free to use.

## Architecture

Each unit runs `sleep infinity` and nothing else. No ports, no healthcheck, no
tsdproxy or homepage labels — there is no service here to reach, only a shell
to enter. They start at boot so `podman exec` always works, and an idle
`sleep` costs nothing.

Two decisions worth knowing:

- **`UserNS=keep-id`.** Files you create in `/work` land on the host owned by
  *you*, not by a mapped subuid you would need `podman unshare` to touch. This
  is not hardening ([rule 20](../../docs/conventions.md)) — it is purely about
  who owns the files. It is also why installing packages needs one extra flag,
  below.
- **One volume per box**, at `/work`, which is also `HOME` and the working
  directory. A binary built in the Arch box does not belong in the Fedora one,
  so they do not share. `HOME=/work` is what points the shell at the volume:
  Podman synthesises the `/etc/passwd` entry from it, so shell history, `npm`
  config and anything else that follows `$HOME` land somewhere that survives a
  restart instead of in the container's throwaway layer.

## Files

```
toolbx-arch.container
toolbx-fedora.container
toolbx-rhel.container
toolbx-ubuntu.container
install.ini               # [upstream] = "-" for all four
```

## Installation

```bash
python3 install.py toolbx            # dry-run: shows what it will do
python3 install.py toolbx --apply
```

The script writes the units and creates the four volume directories, then
stops: with no single main unit it will not guess which box you want, so start
them yourself — see [Installing and operating](../../docs/installing.md).

```bash
systemctl --user start toolbx-arch toolbx-fedora toolbx-rhel toolbx-ubuntu
```

## Just one box

Name the unit instead of the folder:

```bash
python3 install.py toolbx-ubuntu --apply
```

That writes one unit file, creates one volume directory, and starts it. By hand
it is the same four lines with a single `wget`:

```bash
mkdir -p ~/.config/containers/systemd/toolbx ~/.config/containers/volumes/toolbx/ubuntu
wget -P ~/.config/containers/systemd/toolbx/ \
  https://raw.githubusercontent.com/wallacepnts/quadlet-homelab/main/apps/toolbx/toolbx-ubuntu.container
systemctl --user daemon-reload
systemctl --user start toolbx-ubuntu
```

**If you already ran `install.py toolbx`**, all four files are on disk, and
[rule 4](../../docs/conventions.md) means their `[Install]` was applied at
generation — so the other three come up on their own at the next boot, and a
Quadlet-generated unit cannot be `disable`d. Deleting the file is the only way
to not have the box:

```bash
rm ~/.config/containers/systemd/toolbx/toolbx-{arch,fedora,rhel}.container
systemctl --user daemon-reload
```

Before their first start they cost nothing — the image is only pulled when the
unit comes up. It is the boot after that gets you.

## Using one

```bash
podman exec -it toolbx-fedora bash
```

That drops you in as **your own user**, which is what keeps `/work` files
yours. Installing packages needs root, so it takes `--user root`:

```bash
podman exec -it --user root toolbx-fedora dnf install -y ripgrep
podman exec -it toolbx-fedora rg --version
```

Forget the flag and you get a permission error from the package manager, not a
missing-command error — that is the tell. `sudo` is installed but will not help:
the images ship the `%wheel NOPASSWD` rule commented out, and the thing that
normally uncomments it is `toolbox init-container`, which these units skip.

Installed packages live in the container's writable layer, so they survive a
`restart` but **not** a `podman rm` or an image bump. Anything you want to keep
goes in `/work`.

To start over on one box:

```bash
systemctl --user stop toolbx-fedora
rm -rf ~/.config/containers/volumes/toolbx/fedora   # only if you want the data gone too
systemctl --user restart toolbx-fedora
```

### The RHEL box installs from a smaller set

`ubi10/toolbox` is Red Hat's freely redistributable image, and on a host with
no Red Hat subscription its `dnf` reaches the **UBI repositories only** — a
subset of RHEL. Packages inside it install normally; anything outside comes
back as a missing package rather than a permission problem:

```
$ podman exec --user root toolbx-rhel dnf install -y wget    # in UBI  -> installs
$ podman exec --user root toolbx-rhel dnf install -y tree    # not in UBI
No match for argument: tree
Error: Unable to find a match: tree
```

Use it to check behaviour on the RHEL userland. For "install an arbitrary
tool", reach for the Fedora or Arch box.

## Running Claude Code in one

This needs three things the bare boxes do not have.

**Node, first.** None of the four ship it:

```bash
podman exec -it --user root toolbx-ubuntu bash
apt update && apt install -y curl ca-certificates
curl -fsSL https://deb.nodesource.com/setup_22.x | bash - && apt install -y nodejs
npm install -g @anthropic-ai/claude-code
```

**Credentials, second.** Either export `ANTHROPIC_API_KEY`, or log in
interactively — the OAuth profile lands under `HOME`, which is `/work` here, so
it survives restarts instead of forcing a re-login every time.

**Your project, third — and this is the part that decides whether any of it was
worth doing.** Mount the repository you are working on, and *only* that:

```ini
Volume=%h/HD/Projetos/meu-projeto:/work/meu-projeto:Z
```

Mounting `%h` instead gives the agent back everything the container was there to
keep it away from.

**What the container does not do**, in Anthropic's own words: a dev container
*"does not prevent a malicious project from exfiltrating anything accessible
inside the container, including the Claude Code credentials stored in
`~/.claude`"*. A narrow mount limits what can be **damaged**; it does not limit
what can be **read and sent out**, because the container isolates the filesystem
and not the network. Anything inside reaches whatever the host reaches.

That warning bites harder here than in the reference setup: `HOME=/work` puts the
OAuth token in the same volume as the project. Treat these boxes as
trusted-repository-only, and prefer repository-scoped or short-lived tokens over
mounting anything from the host.

**The missing piece is egress filtering.** The reference devcontainer solves it
with an [`init-firewall.sh`](https://github.com/anthropics/claude-code/blob/main/.devcontainer/init-firewall.sh)
that denies all outbound traffic except an allowlist. Running it needs
`AddCapability=NET_ADMIN` and `AddCapability=NET_RAW` on the unit plus the script
at start — not wired up here yet.

**Lighter options exist.** If the goal is only "fewer prompts", `auto` mode runs
a classifier over actions instead of disabling the checks. And Claude Code ships
a built-in Bash sandbox that may cover the case without any of this — see
[Sandbox environments](https://code.claude.com/docs/en/sandbox-environments).

## Auto-update

No `AutoUpdate=` — explicit tags, bumped by hand
([rule 9](../../docs/conventions.md)). Arch is the exception: `arch-toolbox`
publishes only `latest`, so it is pinned **by digest** instead, the same way
[mdrop](../mdrop/) handles its image. Bumping it means reading the new digest:

```bash
podman pull quay.io/toolbx/arch-toolbox:latest
podman inspect quay.io/toolbx/arch-toolbox:latest --format '{{index .RepoDigests 0}}'
```

`updates.py` cannot help with any of the four: none come from a GitHub release,
which is why `install.ini` declares `[upstream] = "-"` for all of them. They
still show up under *"cannot compare"* — `-` tells `updates.py` not to try, but
it prints the same "declare it in [upstream]" line either way. Watch each
distro's own release notes instead.

## Backup & recovery

The containers themselves are disposable — reinstall and you are back. Only
`/work` holds anything worth keeping:

```bash
tar -czf toolbx-backup-$(date +%Y%m%d-%H%M%S).tar.gz \
  -C ~/.config/containers/volumes toolbx
```

## Useful commands

```bash
podman ps --filter "name=toolbx-"
podman exec -it toolbx-fedora bash                    # as you
podman exec -it --user root toolbx-fedora bash        # to install packages
systemctl --user restart toolbx-fedora
```

## Credits

The images come from [Toolbx](https://containertoolbx.org/)
([containers/toolbox](https://github.com/containers/toolbox), Apache-2.0), whose
official distro list this folder follows.
