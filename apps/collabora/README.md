# Collabora Online

<img src="https://api.iconify.design/mdi/file-document-edit.svg?color=%23888888" width="64" height="64" alt="">

**[🇧🇷 Leia em português](./README.pt-BR.md)**

LibreOffice, rendered in the browser, editing the files that are already in
[ownCloud](../owncloud). Documents, spreadsheets and slides open in place, and
the file never leaves the house.

It is useless on its own: every document it opens is handed to it by ownCloud.
Install that one first.

## Install

```bash
qh collabora            # shows the plan
qh collabora --apply
```

Then, in `~/.config/containers/env/collabora.env`, put your ownCloud address in
`aliasgroup1` and restart with `qh collabora --update --apply`. On the ownCloud
side, once:

```bash
podman exec owncloud occ app:enable richdocuments
podman exec owncloud occ config:app:set richdocuments wopi_url \
  --value="https://collabora.<your-tailnet>.ts.net"
```

<details>
<summary><b>Manual install (advanced)</b></summary>

```bash
mkdir -p ~/.config/containers/systemd ~/.config/containers/env

wget -P ~/.config/containers/systemd/ \
  https://raw.githubusercontent.com/wallacepnts/quadlet-homelab/main/apps/collabora/collabora.container
wget -O ~/.config/containers/env/collabora.env \
  https://raw.githubusercontent.com/wallacepnts/quadlet-homelab/main/apps/collabora/.env.example
# edit ~/.config/containers/env/collabora.env: aliasgroup1

systemctl --user daemon-reload
systemctl --user start collabora
```

</details>

## Files

```
collabora.container   unit
.env.example          environment
install.ini
```

No volume: it stores nothing. Every document lives in ownCloud and is fetched
per edit, so there is nothing here to back up and nothing to lose on a
`--purge`.

## The two ends of the connection

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

## Hardening

One capability, `SYS_CHROOT`. Collabora runs each document in its own chroot
jail, and with everything dropped the kit dies at start:

```
FTL  chroot("/opt/cool/child-roots/...") failed (EPERM: Operation not permitted)
```

`ReadOnly=true` was tried and refused — `Access to file denied:
/opt/cool/child-roots/...`, because a tmpfs over that path belongs to root
while coolwsd runs as uid 1001, which the image already sets.

There is no `HealthCmd`, and therefore no `Notify=healthy`: the image carries
no shell and no `curl` or `wget` — `coolwsd`, `coolmount`, `coolforkit` and
`openssl` are the whole of `/usr/bin`, so there is nothing to run inside it.

## Update

```bash
qh collabora --update --apply
```

Pinned to `26.04.3.1.1`. Collabora publishes no GitHub releases, so
`qh-updates` compares against the registry's tag list.

## Backup

Nothing to back up — see [Files](#files). The documents are ownCloud's, and
`qh owncloud --backup` covers them.

## Remove

```bash
qh collabora --remove --apply           # stops it and removes the unit
qh collabora --remove --purge --apply   # and deletes the .env
```

Turn the ownCloud side off too, or its file menu keeps offering an editor that
is no longer there:

```bash
podman exec owncloud occ app:disable richdocuments
```

## Commands

```bash
systemctl --user status collabora
podman logs -f collabora

# what ownCloud asks for
podman exec owncloud curl -s http://collabora:9980/hosting/discovery | head -20
```

## Credits

[CollaboraOnline/online](https://github.com/CollaboraOnline/online) —
MPL-2.0. The image is CODE, the Collabora Online Development Edition.

[Official documentation](https://sdk.collaboraonline.com/docs/installation/)
