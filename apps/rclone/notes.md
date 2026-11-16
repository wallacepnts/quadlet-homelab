The install ends by printing the login (`admin` and a generated password). Open
`https://rclone.<your-tailnet>.ts.net`: the browser asks for them once.

### What it sees

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

### Your own password

```bash
qh rclone --reinstall --ask-secrets --apply
```

### Update

**The web GUI is a separate project and is pinned too.** By default `rcd` asks
GitHub for the newest GUI release at every start. `--rc-web-fetch-url` points it
at one release (`v2.0.5`, the current one), so a start fetches that and later
starts reuse the cache. To move to another GUI release, change the tag in that
URL in `Exec=` and delete `~/.config/containers/volumes/rclone/cache/rclone/webgui`.

### Remove

`~/.config/rclone` is never touched by `--purge`: it is the host's own config.
