# neko

<img src="https://api.iconify.design/mdi/web-box.svg?color=%23888888" width="64" height="64" alt="">

**[🇧🇷 Leia em português](./README.pt-BR.md)**

A browser running on the server, streamed to yours over WebRTC. Several
people can watch the same session and pass control around, and nothing it
opens ever touches your own machine — which is the point, whether you are
watching something together or opening a link you do not trust.

## Install

```bash
qh neko            # shows the plan
qh neko --apply
```

The install prints the user and password at the end; the admin password is a
second secret. Open `http://<host-ip>:8018` or
`https://neko.<your-tailnet>.ts.net`.

**Then set `NEKO_NAT1TO1`** in `~/.config/containers/env/neko.env` to the
address clients reach the host at — its tailnet IP, or the LAN one. Without it
the page loads and the screen stays black: neko advertises the container's own
IP for the media stream, and nothing outside can route to it. Restart with `qh
neko --update --apply`.

<details>
<summary><b>Manual install</b></summary>

```bash
mkdir -p ~/.config/containers/systemd ~/.config/containers/env

openssl rand -hex 10 | podman secret create neko-user-password -
openssl rand -hex 10 | podman secret create neko-admin-password -

wget -P ~/.config/containers/systemd/ \
  https://raw.githubusercontent.com/wallacepnts/quadlet-homelab/main/apps/neko/neko.container
wget -O ~/.config/containers/env/neko.env \
  https://raw.githubusercontent.com/wallacepnts/quadlet-homelab/main/apps/neko/.env.example

systemctl --user daemon-reload
systemctl --user start neko
```

</details>

## Files

```
neko.container   unit
.env.example     environment
install.ini      the passwords' recipes
```

Web on **8018**, WebRTC on **59000** (TCP and UDP). No volume: the session is
throwaway by design, and a restart is a fresh browser.

Upstream's compose publishes a 101-port UDP range. `NEKO_WEBRTC_UDPMUX` and
`NEKO_WEBRTC_TCPMUX` put all of it on one port instead, which is what makes
this a two-port service like everything else here.

## Other browsers

The image name is the flavour: `firefox` is what ships, and upstream also
publishes `chromium`, `brave`, `vivaldi`, `tor-browser` and a plain `xfce`
desktop. Change `Image=` in the unit and `qh neko --update --apply`. Chromium
derivatives need more shared memory than Firefox — `ShmSize=2g` is already
generous, but that is the knob if a tab dies.

## Update

```bash
qh neko --update --apply
```

Pinned to `3.1.5`. Nothing updates on its own — a new version is applied when
you run the command above.

## Backup

There is nothing to back up: no volume, no state. Removing and reinstalling
gives you the same thing.

## Remove

```bash
qh neko --remove --apply
qh neko --remove --purge --apply   # also removes the secrets and the .env
```

## Commands

```bash
systemctl --user status neko
podman logs -f neko
podman exec neko wget -q --spider http://127.0.0.1:8080/health && echo ok
```

## Credits

[neko](https://github.com/m1k1o/neko) by [m1k1o](https://github.com/m1k1o) —
Apache-2.0

[Official documentation](https://neko.m1k1o.net/)
