The install ends by printing the user and password. Then, in each client, point
sync at `https://anki.<your-tailnet>.ts.net/` and log in with them:

- **Anki (desktop)**: Preferences → Syncing → *Self-hosted sync server*.
- **AnkiDroid**: Settings → Sync → *Custom sync server*.
- **AnkiMobile**: Settings → Syncing → *Custom server*.

The first sync after switching servers is a full one: upload from the device
that has the collection you want to keep, download on the others.

### Reaching it

**There is no web page.** Opened in a browser, the address shows an empty
`404 Not Found` — that is the server running; it only answers the Anki apps,
under `/sync/`. To see it work, sync from a client.

The server speaks **plain HTTP** only. On the tailnet, tsdproxy puts HTTPS in
front of it, and that is the address to give the clients: **AnkiMobile refuses
a server without TLS**, and a password sent over plain HTTP crosses the network
readable. Port `8125` on the LAN is for a desktop client on the same network,
if you want one.

The phone reaches `anki.<your-tailnet>.ts.net` only while Tailscale is running
on it. On iOS, AnkiMobile also needs *Local Network* permission to reach a
server on your own network.

`SYNC_HOST=0.0.0.0` is set because the server listens on `localhost` by
default, which inside a container is unreachable from outside it.

### Your own password

The install generates one. To choose it, at install time or any time after:

```bash
qh anki --reinstall --ask-secrets --apply
```

and type **user and password together**, the way the server reads them:

```
anki:your-password
```

Only the password alone, with no `anki:` in front, and the server does not come
up — measured: the container exits at once, with code 0 and not one line in the
log, so nothing points at the secret. Retype it with the command above.

Enter with nothing typed generates a random one again. The password may hold
`:` — the server splits at the first one. `--reinstall` recreates the secret and
restarts the service, and leaves the collections alone; each client then logs in
again with the new password.

Keep the user name. Collections are stored in a folder named after it, so
`maria:…` in place of `anki:…` starts from an empty collection — the old one
stays on disk, unseen, and the next sync offers to upload a client's copy.
`qh anki` prints the user and password in use.

### More than one user

Each account is a `SYNC_USERn` variable (`SYNC_USER1`, `SYNC_USER2`, …), each
with its own collection. The install creates one. For a second person:

```bash
printf 'maria:%s' "$(openssl rand -hex 16)" | podman secret create anki-user2 -
```

and add `Secret=anki-user2,type=env,target=SYNC_USER2` to the unit. Local
edits to the unit are shown by `qh anki --update` before they are overwritten.

### Update

**There is no official image.** Anki's repository carries the Dockerfile but
publishes no image; this one is built from that Dockerfile by its author, on
his own schedule — 25.07 to 26.05 took ten months, and the image lags Anki's
releases. That is harmless: the sync protocol is stable across versions, and a
26.09 client was measured syncing against this 26.08 server.
`install.ini` compares against the registry, not Anki's release page.

The distroless variant, not the Alpine one, because the Alpine entrypoint
`chown`s the data and drops to a user with `su-exec` — which needs root and
capabilities. The distroless one has no entrypoint, so it runs unprivileged
from the start.

### Backup

The volume holds each user's collection and media as SQLite files and a
folder. The clients keep their own copy too, so a lost server is recovered by
a full upload from any of them.
