# FileBrowser Quantum

<img src="https://cdn.jsdelivr.net/gh/homarr-labs/dashboard-icons/svg/filebrowser-quantum.svg" width="64" height="64" alt="">

**[🇧🇷 Leia em português](./README.pt-BR.md)**

A web file manager: browse, search, preview, upload, download, share by link
and edit text, over a directory you choose.

## First run

Put your files in `~/.config/containers/volumes/filebrowser/files/` and open
`https://filebrowser.<your-tailnet>.ts.net` or `http://<host-ip>:8014`.

The user is `admin`. The password is printed at the end of the install, and
again by `qh filebrowser`.

## Files

```
filebrowser.container   unit
config.yaml.example     app config — the app will not start without it
.env.example            environment
install.ini             secret recipes, login, upstream name
```

## Volumes

| path | holds |
| --- | --- |
| `volumes/filebrowser/data` | `config.yaml`, `database.db`, thumbnail cache |
| `volumes/filebrowser/files` | the files it manages |

Host port **8014** maps to **8080** inside.

## Adding a directory

Add a `Volume=` to the unit and a matching source in `config.yaml`:

```ini
Volume=%h/Documents:/docs:Z
```

```yaml
server:
  sources:
    - path: "/srv"
    - path: "/docs"
```

Each source gets its own index. A large tree costs memory and a first-run scan.

## Password

```bash
qh filebrowser        # prints user and password
```

To change it:

```bash
podman secret rm filebrowser-admin-password
podman secret create filebrowser-admin-password -   # type it, Enter, Ctrl-D
systemctl --user restart filebrowser
```

Rotating `filebrowser-jwt-secret` the same way logs every session out without
changing the password.

## Update

`config.yaml` is versioned here, so read the release notes for schema changes before a major bump.

## Backup

Stopped on purpose: `database.db` is live, and copying it while the app writes
gives an archive that only fails when you restore it.

Metadata only, without the files:

## Credits

[gtsteffaniak/filebrowser](https://github.com/gtsteffaniak/filebrowser) — Apache-2.0

[Official documentation](https://filebrowserquantum.com/en/docs/)
