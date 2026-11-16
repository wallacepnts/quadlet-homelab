# Toolbx

<img src="https://cdn.jsdelivr.net/gh/containers/containertoolbx.org@main/apple-touch-icon.png" width="64" height="64" alt="">

**[🇧🇷 Leia em português](./README.pt-BR.md)**

Disposable Arch, Fedora, RHEL and Ubuntu shells, on the official Toolbx images — somewhere to install a one-off tool that is not the host.

These are containers, not VMs: they share the host's kernel, which is why they start instantly. When you need a real one, see [vm](../vm).

## First run

## Files

```
toolbx-<distro>.container   one unit per shell, four of them
install.ini                 where updates.py should look for each
docs/                       a page per shell
```

Data in `~/.config/containers/volumes/toolbx/<distro>`, mounted at `/work`. No
`.env`, no secrets and no ports: these are shells, not services.

| | Shell | What it is | Version |
| --- | --- | --- | --- |
| <img src="https://cdn.simpleicons.org/fedora" width="28" height="28" alt=""> | [Fedora](./docs/fedora.md) | A Fedora shell with `dnf`, on Fedora's own image | `digest` |
| <img src="https://cdn.simpleicons.org/ubuntu" width="28" height="28" alt=""> | [Ubuntu](./docs/ubuntu.md) | An Ubuntu shell with `apt`, for anything that ships a `.deb` | `26.04` |
| <img src="https://cdn.simpleicons.org/archlinux" width="28" height="28" alt=""> | [Arch Linux](./docs/arch.md) | An Arch shell with `pacman` and the AUR. Pinned by digest, not by tag | `digest` |
| <img src="https://cdn.simpleicons.org/redhat" width="28" height="28" alt=""> | [RHEL](./docs/rhel.md) | A Red Hat Enterprise Linux shell, on the subscription-free UBI image | `10.2` |

They are independent — installing the folder brings all four, and you start the
one you need. Nothing is lost by leaving the others stopped.

## Update

Each shell carries its own tag — the table above lists them. Arch is the
exception, pinned by digest because its only tag is `latest`.

## Backup

It stops the four, packs the four `/work` directories and starts them again.
There is no `.env` and no secret here to pack. A single shell can be backed up
on its own — `qh toolbx-fedora --backup --apply` — because none of them shares
a directory with the others.

## Remove

`--purge` asks for the typed name too, and deletes the `/work` of all four.
There is no tailnet node to deregister: none of these is published.

## Credits

[containers/toolbox](https://containertoolbx.org/) — Apache-2.0

[Official documentation](https://containertoolbx.org/)
