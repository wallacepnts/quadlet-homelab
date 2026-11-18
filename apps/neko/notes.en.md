The install prints the user and password at the end (the admin password is a second secret). Open `http://<host-ip>:8018` or `https://neko.<your-tailnet>.ts.net`.

**Then set `NEKO_NAT1TO1`** in `~/.config/containers/env/neko.env` to the address clients reach the host at (its tailnet IP, or the LAN one) and run `qh neko --update --apply`. Without it the page loads and the screen stays black.
