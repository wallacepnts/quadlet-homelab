Open `https://dozzle.<your-tailnet>.ts.net`.

The Podman socket is mounted read-only: that stops it from creating or killing anything, but it still **reads every container's logs and environment**, secrets included, and whoever opens the page reads all of it. Two settings in the `.env` narrow that: `DOZZLE_AUTH_PROVIDER=simple` puts a login in front (off by default, fine only on a tailnet you are alone on) and `DOZZLE_FILTER=name=jellyfin` limits it to the containers you name.
