# FileBrowser Quantum

<img src="https://cdn.jsdelivr.net/gh/homarr-labs/dashboard-icons/svg/filebrowser-quantum.svg" width="64" height="64" alt="">

**[🇧🇷 Leia em português](./README.pt-BR.md)**

A web file manager: browse, search, preview, upload, download, share by link
and edit text, over a directory you choose.

## Install

```bash
qh filebrowser            # shows the plan
qh filebrowser --apply
```

Put your files in `~/.config/containers/volumes/filebrowser/files/` and open
`https://filebrowser.<your-tailnet>.ts.net` or `http://<host-ip>:8014`.

The user is `admin`. The password is printed at the end of the install, and
again by `qh filebrowser`.

<details>
<summary><b>Manual install</b></summary>

```bash
mkdir -p ~/.config/containers/systemd ~/.config/containers/env
mkdir -p ~/.config/containers/volumes/filebrowser/{data,files}

wget -P ~/.config/containers/systemd/ \
  https://raw.githubusercontent.com/wallacepnts/quadlet-homelab/main/apps/filebrowser/filebrowser.container
wget -O ~/.config/containers/volumes/filebrowser/data/config.yaml \
  https://raw.githubusercontent.com/wallacepnts/quadlet-homelab/main/apps/filebrowser/config.yaml.example
wget -O ~/.config/containers/env/filebrowser.env \
  https://raw.githubusercontent.com/wallacepnts/quadlet-homelab/main/apps/filebrowser/.env.example

podman secret create filebrowser-admin-password - <<< "$(python3 -c 'import secrets,string;a=string.ascii_letters+string.digits;print("".join(secrets.choice(a) for _ in range(20)))')"
podman secret create filebrowser-jwt-secret - <<< "$(python3 -c 'import secrets;print(secrets.token_hex(32))')"

systemctl --user daemon-reload
systemctl --user start filebrowser
```

</details>

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

```bash
qh filebrowser --update --apply
```

Pinned to `1.5.1-stable`. Nothing updates on its own — a new version is
applied when you run the command above. `config.yaml` is versioned here, so
read the release notes for schema changes before a major bump.

## Backup

```bash
systemctl --user stop filebrowser
tar -czf filebrowser-$(date +%Y%m%d).tar.gz \
  -C ~/.config/containers/volumes filebrowser
systemctl --user start filebrowser
```

Stopped on purpose: `database.db` is live, and copying it while the app writes
gives an archive that only fails when you restore it.

Metadata only, without the files:

```bash
tar -czf filebrowser-data-$(date +%Y%m%d).tar.gz --exclude=data/cache \
  -C ~/.config/containers/volumes/filebrowser data
```

## Commands

```bash
systemctl --user status filebrowser
podman logs -f filebrowser
du -sh ~/.config/containers/volumes/filebrowser/data/cache
```

## Credits

[gtsteffaniak/filebrowser](https://github.com/gtsteffaniak/filebrowser) — Apache-2.0

[Official documentation](https://filebrowserquantum.com/en/docs/)
