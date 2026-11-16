The install prints the user and password at the end; the admin password is a
second secret. Open `http://<host-ip>:8018` or
`https://neko.<your-tailnet>.ts.net`.

**Then set `NEKO_NAT1TO1`** in `~/.config/containers/env/neko.env` to the
address clients reach the host at — its tailnet IP, or the LAN one. Without it
the page loads and the screen stays black: neko advertises the container's own
IP for the media stream, and nothing outside can route to it. Restart with `qh
neko --update --apply`.

### Other browsers

The image name is the flavour: `firefox` is what ships, and upstream also
publishes `chromium`, `brave`, `vivaldi`, `tor-browser` and a plain `xfce`
desktop. Change `Image=` in the unit and `qh neko --update --apply`. Chromium
derivatives need more shared memory than Firefox — `ShmSize=2g` is already
generous, but that is the knob if a tab dies.

### Backup

There is nothing to back up: no volume, no state. Removing and reinstalling
gives you the same thing.
