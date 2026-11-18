In `~/.config/containers/env/collabora.env`, put your ownCloud address in `aliasgroup1` (a regular expression, dots escaped: `https://owncloud\.<your-tailnet>\.ts\.net:443`) and restart with `qh collabora --update --apply`. On the ownCloud side, once:

```bash
podman exec owncloud occ app:enable richdocuments
podman exec owncloud occ config:app:set richdocuments wopi_url \
  --value="https://collabora.<your-tailnet>.ts.net"
```

`wopi_url` is where *your browser* loads the editor from. A host missing from `aliasgroup1` gets `unauthorized WOPI host`, which looks like a document that spins forever. On removal, run `occ app:disable richdocuments` too.
