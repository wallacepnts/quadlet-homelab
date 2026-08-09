# Toolbx Arch Linux

<img src="https://cdn.simpleicons.org/archlinux" width="64" height="64" alt="">

**[🇧🇷 Leia em português](./pt-BR/arch.md)**

[< Toolbx](../README.md)

An Arch shell with `pacman` and access to the AUR.

Unit `toolbx-arch`, image `quay.io/toolbx/arch-toolbox@sha256:38d89c…`.

Pinned by digest, not by tag. Arch is a rolling release: its only tag is `latest`, which moves whenever the image is rebuilt, and a tag that moves is not a version this repository can pin.

Updating means replacing the digest by hand — `podman pull quay.io/toolbx/arch-toolbox:latest` and reading the new one from `podman inspect`. `qh-updates` cannot compare it, and `install.ini` marks it `-` for that reason.

The container runs `sleep infinity` and does nothing on its own — the point is
the shell you open in it. `/work` is the only directory that survives a
restart; anything installed with the package manager is lost when the
container is recreated, which is what makes it disposable.

```bash
podman exec -it toolbx-arch bash
podman exec -it --user root toolbx-arch bash   # to install a package
```

`UserNS=keep-id` keeps your uid inside, so files written to `/work` come out
owned by you. It is also why installing a package needs `--user root`
explicitly.

## Install

```bash
qh toolbx-arch
qh toolbx-arch --apply
```

Installing the folder — `qh toolbx --apply` — brings this one along with the
other three.

## Files

```
toolbx-arch.container   unit
```

Data in `~/.config/containers/volumes/toolbx/arch`. No `.env`, no secret and
no port: this one is not a service.

## Update

```bash
qh toolbx-arch --update --apply
```

Pinned by digest, so the command above re-applies the same image until the
digest in the unit is changed.

## Backup

```bash
qh toolbx-arch --backup --apply --out ~/backups
```

It packs `/work` and nothing else — this unit shares no directory with the
other three. Restoring is `qh toolbx-arch --restore <file> --apply`.

## Remove

```bash
qh toolbx-arch --remove --apply
qh toolbx-arch --remove --purge --apply   # and deletes /work
```

Only this unit. The other three keep their directories.

## Commands

```bash
systemctl --user status toolbx-arch
podman exec -it toolbx-arch bash
qh toolbx-arch --update --apply
```

## Credits

[Toolbx](https://containertoolbx.org/) — Apache-2.0

[Official documentation](https://wiki.archlinux.org/title/Toolbx)
