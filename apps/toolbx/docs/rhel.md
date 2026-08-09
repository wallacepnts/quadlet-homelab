# Toolbx RHEL

<img src="https://cdn.simpleicons.org/redhat" width="64" height="64" alt="">

**[🇧🇷 Leia em português](./pt-BR/rhel.md)**

[< Toolbx](../README.md)

A Red Hat Enterprise Linux shell, on the UBI image.

Unit `toolbx-rhel`, image `registry.access.redhat.com/ubi10/toolbox:10.2`.

UBI — Universal Base Image — is the part of RHEL Red Hat publishes without a subscription. It is the one to reproduce a problem that only shows up on an enterprise distribution.

The repositories that need a subscription are not enabled, so `dnf` reaches fewer packages than on a licensed RHEL.

The container runs `sleep infinity` and does nothing on its own — the point is
the shell you open in it. `/work` is the only directory that survives a
restart; anything installed with the package manager is lost when the
container is recreated, which is what makes it disposable.

```bash
podman exec -it toolbx-rhel bash
podman exec -it --user root toolbx-rhel bash   # to install a package
```

`UserNS=keep-id` keeps your uid inside, so files written to `/work` come out
owned by you. It is also why installing a package needs `--user root`
explicitly.

## Install

```bash
qh toolbx-rhel
qh toolbx-rhel --apply
```

Installing the folder — `qh toolbx --apply` — brings this one along with the
other three.

## Files

```
toolbx-rhel.container   unit
```

Data in `~/.config/containers/volumes/toolbx/rhel`. No `.env`, no secret and
no port: this one is not a service.

## Update

```bash
qh toolbx-rhel --update --apply
```

Pinned to `10.2`. Nothing updates on its own — a new version is applied
when you run the command above.

## Backup

```bash
qh toolbx-rhel --backup --apply --out ~/backups
```

It packs `/work` and nothing else — this unit shares no directory with the
other three. Restoring is `qh toolbx-rhel --restore <file> --apply`.

## Remove

```bash
qh toolbx-rhel --remove --apply
qh toolbx-rhel --remove --purge --apply   # and deletes /work
```

Only this unit. The other three keep their directories.

## Commands

```bash
systemctl --user status toolbx-rhel
podman exec -it toolbx-rhel bash
qh toolbx-rhel --update --apply
```

## Credits

[Toolbx](https://containertoolbx.org/) — Apache-2.0

[Official documentation](https://catalog.redhat.com/software/base-images)
