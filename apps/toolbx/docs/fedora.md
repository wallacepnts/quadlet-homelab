# Toolbx Fedora

<img src="https://cdn.simpleicons.org/fedora" width="64" height="64" alt="">

**[🇧🇷 Leia em português](./pt-BR/fedora.md)**

[< Toolbx](../README.md)

A Fedora shell with `dnf`, on the image Fedora publishes for exactly this.

Unit `toolbx-fedora`, image `registry.fedoraproject.org/fedora-toolbox:45`.

The image comes from Fedora's own registry, not Docker Hub, and the tag is the release number.

The natural one to reach for on an rpm-based host: the packages match what the host would have installed.

The container runs `sleep infinity` and does nothing on its own — the point is
the shell you open in it. `/work` is the only directory that survives a
restart; anything installed with the package manager is lost when the
container is recreated, which is what makes it disposable.

```bash
podman exec -it toolbx-fedora bash
podman exec -it --user root toolbx-fedora bash   # to install a package
```

`UserNS=keep-id` keeps your uid inside, so files written to `/work` come out
owned by you. It is also why installing a package needs `--user root`
explicitly.

## Install

```bash
qh toolbx-fedora
qh toolbx-fedora --apply
```

Installing the folder — `qh toolbx --apply` — brings this one along with the
other three.

## Files

```
toolbx-fedora.container   unit
```

Data in `~/.config/containers/volumes/toolbx/fedora`. No `.env`, no secret and
no port: this one is not a service.

## Update

```bash
qh toolbx-fedora --update --apply
```

Pinned to `45`. Nothing updates on its own — a new version is applied
when you run the command above.

## Backup

```bash
qh toolbx-fedora --backup --apply --out ~/backups
```

It packs `/work` and nothing else — this unit shares no directory with the
other three. Restoring is `qh toolbx-fedora --restore <file> --apply`.

## Remove

```bash
qh toolbx-fedora --remove --apply
qh toolbx-fedora --remove --purge --apply   # and deletes /work
```

Only this unit. The other three keep their directories.

## Commands

```bash
systemctl --user status toolbx-fedora
podman exec -it toolbx-fedora bash
qh toolbx-fedora --update --apply
```

## Credits

[Toolbx](https://containertoolbx.org/) — Apache-2.0

[Official documentation](https://docs.fedoraproject.org/en-US/fedora-silverblue/toolbox/)
