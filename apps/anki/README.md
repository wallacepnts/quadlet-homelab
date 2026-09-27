# Anki

<img src="https://cdn.jsdelivr.net/gh/selfhst/icons/svg/anki.svg" width="64" height="64" alt="">

**[🇧🇷 Leia em português](./README.pt-BR.md)**

The sync server that ships with [Anki](https://apps.ankiweb.net) itself, run
here instead of AnkiWeb. Decks, review history and media sync between Anki on
the desktop, AnkiDroid and AnkiMobile through your own machine.

## Install

```bash
qh anki            # shows the plan
qh anki --apply
```

The install ends by printing the user and password. Then, in each client, point
sync at `https://anki.<your-tailnet>.ts.net/` and log in with them:

- **Anki (desktop)**: Preferences → Syncing → *Self-hosted sync server*.
- **AnkiDroid**: Settings → Sync → *Custom sync server*.
- **AnkiMobile**: Settings → Syncing → *Custom server*.

The first sync after switching servers is a full one: upload from the device
that has the collection you want to keep, download on the others.

<details>
<summary><b>Manual install (advanced)</b></summary>

```bash
# 1. Download the unit (no need to clone the repository)
mkdir -p ~/.config/containers/systemd
wget -P ~/.config/containers/systemd/ \
  https://raw.githubusercontent.com/wallacepnts/quadlet-homelab/main/apps/anki/anki.container

# 2. The data directory. The unit runs as uid 65532, distroless's nonroot user.
mkdir -p ~/.config/containers/volumes/anki/data
podman unshare chown -R 65532:65532 ~/.config/containers/volumes/anki/data

# 3. The account, as `user:password`, the form the server reads
printf 'anki:%s' "$(openssl rand -hex 16)" | podman secret create anki-user -
podman secret inspect anki-user --showsecret --format '{{.SecretData}}'; echo

systemctl --user daemon-reload
systemctl --user start anki
```

</details>

## Files

```
anki.container   unit
install.ini      the secret's recipe and where updates come from
```

Data in `~/.config/containers/volumes/anki/data`, one folder per user. Port
**8125** on the LAN.

## Reaching it

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

## More than one user

Each account is a `SYNC_USERn` variable (`SYNC_USER1`, `SYNC_USER2`, …), each
with its own collection. The install creates one. For a second person:

```bash
printf 'maria:%s' "$(openssl rand -hex 16)" | podman secret create anki-user2 -
```

and add `Secret=anki-user2,type=env,target=SYNC_USER2` to the unit. Local
edits to the unit are shown by `qh anki --update` before they are overwritten.

## Update

```bash
qh anki --update --apply
```

Pinned to `26.08-distroless`. Nothing updates on its own.

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

## Hardening

Everything, measured on `26.08-distroless`: read-only root with no `/tmp`
(a 3 MB media file synced without one), no capabilities, `User=65532`. Tested
with a real client — login, a wrong password refused, a note and a media file
uploaded from one collection and downloaded into another.

`StopSignal=SIGINT` because the server has no handler for SIGTERM, podman's
default: every stop and restart waited the 10 seconds to SIGKILL. On SIGINT it
exits cleanly, with code 0.

## Backup

```bash
qh anki --backup --apply --out ~/backups
```

The volume holds each user's collection and media as SQLite files and a
folder. The clients keep their own copy too, so a lost server is recovered by
a full upload from any of them.

## Remove

```bash
qh anki --remove --apply           # stops it, keeps the data
qh anki --remove --purge --apply   # and deletes the volume and secret
```

The tailnet node is not deregistered by this — that is done in the Tailscale admin.

## Commands

```bash
systemctl --user status anki
podman logs -f anki
podman exec anki anki-sync-server --healthcheck; echo $?
```

## Credits

[ankitects/anki](https://github.com/ankitects/anki) — AGPL-3.0-or-later.
The image, [jeankhawand/anki-sync-server](https://hub.docker.com/r/jeankhawand/anki-sync-server),
is built from the Dockerfile in Anki's `docs/syncserver`, maintained by Jean Khawand.

[Official documentation](https://docs.ankiweb.net/sync-server.html)
