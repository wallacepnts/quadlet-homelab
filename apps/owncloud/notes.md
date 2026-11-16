Open `http://<host-ip>:8094` or `https://owncloud.<your-tailnet>.ts.net`.

### Editing documents

With [Collabora](../collabora) running, `.docx`, `.xlsx` and `.odt` open in the
browser instead of only downloading. Enable the app once:

```bash
podman exec owncloud occ app:enable richdocuments
podman exec owncloud occ config:app:set richdocuments wopi_url \
  --value="https://collabora.<your-tailnet>.ts.net"
```

The `wopi_url` is where your browser loads the editor from, so it is the
tailnet address and not a container name.
