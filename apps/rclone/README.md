# rclone

<img src="https://cdn.jsdelivr.net/gh/homarr-labs/dashboard-icons/svg/rclone.svg" width="64" height="64" alt="">

**[🇧🇷 Leia em português](./README.pt-BR.md)**

[rclone](https://rclone.org) running as its remote-control server with the web
GUI on. It reads the same `~/.config/rclone/rclone.conf` as the `rclone` command
on the host, so every cloud account already set up there shows up in the browser,
and new ones can be added from it.

## First run

The install ends by printing the login (`admin` and a generated password). Open
`https://rclone.<your-tailnet>.ts.net`: the browser asks for them once.

## Files

```
rclone.container   unit
install.ini        the secret's recipe, the login and where updates come from
```

Port **5572** on the LAN. The GUI files are cached in
`~/.config/containers/volumes/rclone/cache`.

## What it sees

- **Remotes only.** No local folder is mounted, so the GUI browses and moves
  files between the accounts in the config, not the host's disk. To use a local
  folder as a remote end, add a `Volume=` for it and an `alias` or `local`
  remote that points at the container path.
- **The host's config, writable.** `~/.config/rclone` is mounted read-write on
  purpose: OAuth providers rotate the refresh token, and a read-only config would
  keep the old one on disk until it stops working. Zerobyte mounts the same
  folder read-only, and the Air Explorer RS on the host uses the same file, so
  there is one copy of every token. The mount is `:z` (shared label) because
  more than one thing opens it.
- **Whoever has the password has every account.** The GUI can read, copy and
  delete in all remotes. It is behind the tailnet and basic auth, nothing else.

## Your own password

```bash
qh rclone --reinstall --ask-secrets --apply
```

## Update

**The web GUI is a separate project and is pinned too.** By default `rcd` asks
GitHub for the newest GUI release at every start. `--rc-web-fetch-url` points it
at one release (`v2.0.5`, the current one), so a start fetches that and later
starts reuse the cache. To move to another GUI release, change the tag in that
URL in `Exec=` and delete `~/.config/containers/volumes/rclone/cache/rclone/webgui`.

## Hardening

Measured on `1.75.2`: read-only root with a 64 MB `/tmp`, no capabilities, no
extra privileges. The process runs as your own uid through `UserNS=keep-id`,
which is not hardening — it is what lets it read and rewrite a `rclone.conf`
that is mode 600 and yours. Without it the file would belong to the container's
root and be unreadable to a non-root process.

Tested in a lab with the same flags: login (401 without it, 200 with it), the
GUI served from the cache after a restart, the health check, and creating a
remote through the API, which wrote `rclone.conf` as 600 and owned by the host
user. Not tested: a real cloud remote, or a browser session through tsdproxy.

## Remove

`~/.config/rclone` is never touched by `--purge`: it is the host's own config. The tailnet node is not deregistered when an app is removed: do that in the Tailscale admin.

## Credits

[rclone/rclone](https://github.com/rclone/rclone) — MIT. The web GUI is
[rclone/rclone-webui-react](https://github.com/rclone/rclone-webui-react).

[Official documentation](https://rclone.org/rc/)
