# Dozzle

<img src="https://cdn.jsdelivr.net/gh/homarr-labs/dashboard-icons/svg/dozzle.svg" width="64" height="64" alt="">

**[🇧🇷 Leia em português](./README.pt-BR.md)**

Live logs of every container, in the browser. It replaces the `podman logs -f`
you would otherwise run over SSH, with search, several containers side by side,
and no terminal.

It stores nothing: no database, no volume, no log copy. What you see is what
Podman is holding at that moment.

## Install

```bash
qh dozzle            # shows the plan
qh dozzle --apply
```

Open `https://dozzle.<your-tailnet>.ts.net`.

<details>
<summary><b>Manual install (advanced)</b></summary>

```bash
mkdir -p ~/.config/containers/systemd ~/.config/containers/env

wget -P ~/.config/containers/systemd/ \
  https://raw.githubusercontent.com/wallacepnts/quadlet-homelab/main/apps/dozzle/dozzle.container
wget -O ~/.config/containers/env/dozzle.env \
  https://raw.githubusercontent.com/wallacepnts/quadlet-homelab/main/apps/dozzle/.env.example

systemctl --user daemon-reload
systemctl --user start dozzle
```

</details>

## Files

```
dozzle.container   unit
.env.example       environment
```

No volume, because there is nothing to keep.

## The socket is the whole story

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

## Hardening

The whole ladder: `ReadOnly=true`, every capability dropped, `User=1000`.
Measured with it connected — `Connected to Docker` in the log and the interface
answering — not just with the container up.

The health check is the binary's own subcommand, `/dozzle healthcheck`, in exec
form: the image ships no shell, so `CMD-SHELL` would fail.

## Update

```bash
qh dozzle --update --apply
```

Pinned to `v10.7.1`.

## Backup

Nothing to back up. Removing it loses no data — the logs belong to Podman.

## Remove

```bash
qh dozzle --remove --apply
```

## Commands

```bash
systemctl --user status dozzle
podman logs -f dozzle
```

## Credits

[amir20/dozzle](https://github.com/amir20/dozzle) — MIT.

[Official documentation](https://dozzle.dev/)
