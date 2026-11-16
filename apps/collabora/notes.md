Then, in `~/.config/containers/env/collabora.env`, put your ownCloud address in
`aliasgroup1` and restart with `qh collabora --update --apply`. On the ownCloud
side, once:

```bash
podman exec owncloud occ app:enable richdocuments
podman exec owncloud occ config:app:set richdocuments wopi_url \
  --value="https://collabora.<your-tailnet>.ts.net"
```

### The two ends of the connection

They have to agree, and each one fails differently when they do not:

- **`aliasgroup1`**, here, is who may embed the editor — a regular expression,
  so the dots are escaped: `https://owncloud\.<your-tailnet>\.ts\.net:443`. A
  host that is not listed gets `unauthorized WOPI host`, which in ownCloud
  looks like a document that spins forever.
- **`wopi_url`**, in ownCloud, is where the browser loads the editor from. It
  has to be the address *your browser* can reach, not a container name — the
  page is rendered on your machine.

Server to server they talk over `tsdproxy-net` by name, which is how ownCloud
reads `http://collabora:9980/hosting/discovery` without a published port.

`extra_params=--o:ssl.enable=false --o:ssl.termination=true` is not optional
behind tsdproxy: without the second flag Collabora builds its URLs as `http://`
and the browser blocks them as mixed content; without the first it serves TLS
itself, on a certificate nobody trusts.

### Update

Collabora publishes no GitHub releases, so `qh-updates` compares against the registry's tag list.

### Backup

Nothing to back up — see [Files](#files). The documents are ownCloud's, and
`qh owncloud --backup` covers them.

### Remove

Turn the ownCloud side off too, or its file menu keeps offering an editor that
is no longer there:

```bash
podman exec owncloud occ app:disable richdocuments
```
