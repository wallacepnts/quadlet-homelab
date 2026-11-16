# ownCloud

<img src="https://cdn.jsdelivr.net/gh/homarr-labs/dashboard-icons/svg/owncloud.svg" width="64" height="64" alt="">

**[🇧🇷 Leia em português](./README.pt-BR.md)**

File sync and sharing on a cloud of your own.

## First run

Open `http://<host-ip>:8094` or `https://owncloud.<your-tailnet>.ts.net`.

## Files

```
owncloud.container
.env.example
install.ini
```

## Remove

The tailnet node is not deregistered when an app is removed: do that in the Tailscale admin.

## Editing documents

With [Collabora](../collabora) running, `.docx`, `.xlsx` and `.odt` open in the
browser instead of only downloading. Enable the app once:

```bash
podman exec owncloud occ app:enable richdocuments
podman exec owncloud occ config:app:set richdocuments wopi_url \
  --value="https://collabora.<your-tailnet>.ts.net"
```

The `wopi_url` is where your browser loads the editor from, so it is the
tailnet address and not a container name.

## Credits

[owncloud/core](https://github.com/owncloud/core) — AGPL-3.0.

[Official documentation](https://owncloud.com)
