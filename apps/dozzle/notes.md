Open `https://dozzle.<your-tailnet>.ts.net`.

### The socket is the whole story

```ini
Volume=%t/podman/podman.sock:/var/run/docker.sock:ro
```

That line is what makes Dozzle work, and it is the only thing worth thinking
about before installing it. The socket is Podman's whole API: read-only stops
this container from creating or killing anything, but it still **reads
everything** — every container's logs, environment and configuration, including
the ones carrying secrets in their environment.

So whoever opens the page reads all of it. Two settings narrow that, both in
the `.env`:

- `DOZZLE_AUTH_PROVIDER=simple` puts a login in front. Off by default, which is
  fine behind a tailnet you are the only one on, and not fine otherwise.
- `DOZZLE_FILTER=name=media-stack` limits it to the containers you name.

`DOZZLE_NO_ACTIONS=true` ships on: the buttons that stop and restart containers
would fail against a read-only socket anyway, and offering a button that cannot
work is worse than not offering it.

### Backup

Nothing to back up. Removing it loses no data — the logs belong to Podman.
