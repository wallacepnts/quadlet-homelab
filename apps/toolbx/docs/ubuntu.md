# Toolbx Ubuntu

<img src="https://cdn.simpleicons.org/ubuntu" width="64" height="64" alt="">

**[🇧🇷 Leia em português](./pt-BR/ubuntu.md)**

[< Toolbx](../README.md)

An Ubuntu shell with `apt`, on the official Toolbx image.

Unit `toolbx-ubuntu`, image `quay.io/toolbx/ubuntu-toolbox:26.04`.

The one to use when a tool only ships a `.deb`, or when the instructions you are following assume Ubuntu.

The tag is the Ubuntu release. Bumping it is a different distribution version, not a patch — the packages installed inside the old one do not come across.

The container runs `sleep infinity` and does nothing on its own — the point is
the shell you open in it. `/work` is the only directory that survives a
restart; anything installed with the package manager is lost when the
container is recreated, which is what makes it disposable.

```bash
podman exec -it toolbx-ubuntu bash
podman exec -it --user root toolbx-ubuntu bash   # to install a package
```

`UserNS=keep-id` keeps your uid inside, so files written to `/work` come out
owned by you. It is also why installing a package needs `--user root`
explicitly.

## Install

```bash
qh toolbx-ubuntu
qh toolbx-ubuntu --apply
```

Installing the folder — `qh toolbx --apply` — brings this one along with the
other three.

## Files

```
toolbx-ubuntu.container   unit
```

Data in `~/.config/containers/volumes/toolbx/ubuntu`. No `.env`, no secret and
no port: this one is not a service.

## Update

```bash
qh toolbx-ubuntu --update --apply
```

Pinned to `26.04`. Nothing updates on its own — a new version is applied
when you run the command above.

## Backup

```bash
qh toolbx-ubuntu --backup --apply --out ~/backups
```

It packs `/work` and nothing else — this unit shares no directory with the
other three. Restoring is `qh toolbx-ubuntu --restore <file> --apply`.

## Remove

```bash
qh toolbx-ubuntu --remove --apply
qh toolbx-ubuntu --remove --purge --apply   # and deletes /work
```

Only this unit. The other three keep their directories.

## Commands

```bash
systemctl --user status toolbx-ubuntu
podman exec -it toolbx-ubuntu bash
qh toolbx-ubuntu --update --apply
```

## Credits

[Toolbx](https://containertoolbx.org/) — Apache-2.0

[Official documentation](https://containertoolbx.org/)
