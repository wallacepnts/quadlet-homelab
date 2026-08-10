# Karaoke Eternal

<img src="https://api.iconify.design/mdi/microphone-variant.svg?color=%23888888" width="64" height="64" alt="">

**[🇧🇷 Leia em português](./README.pt-BR.md)**

A karaoke party from your own library. Everyone queues songs from their phone,
and one screen — a TV, a laptop — runs the player fullscreen. The player is
just a page in the same app, so it needs no install.

## Install

```bash
qh karaoke-eternal            # shows the plan
qh karaoke-eternal --apply
```

Put the karaoke files in
`~/.config/containers/volumes/karaoke-eternal/media`, then open
`http://<host-ip>:8017` or `https://karaoke.<your-tailnet>.ts.net`. **The first
account you create is the admin.** In the app, add `/mnt/karaoke` under Media
Folders and scan.

It reads CDG+MP3 and MP4; the filename is what it parses for artist and title,
so `Artist - Title.mp4` is the shape to aim for.

<details>
<summary><b>Manual install</b></summary>

```bash
mkdir -p ~/.config/containers/systemd ~/.config/containers/env
mkdir -p ~/.config/containers/volumes/karaoke-eternal/{config,media}
podman unshare chown -R 1000:1000 ~/.config/containers/volumes/karaoke-eternal

wget -P ~/.config/containers/systemd/ \
  https://raw.githubusercontent.com/wallacepnts/quadlet-homelab/main/apps/karaoke-eternal/karaoke-eternal.container
wget -O ~/.config/containers/env/karaoke-eternal.env \
  https://raw.githubusercontent.com/wallacepnts/quadlet-homelab/main/apps/karaoke-eternal/.env.example

systemctl --user daemon-reload
systemctl --user start karaoke-eternal
```

</details>

## Files

```
karaoke-eternal.container   unit
.env.example                environment
install.ini                 where updates.py should look
```

Database in `~/.config/containers/volumes/karaoke-eternal/config`, media in
`.../media`, on port **8017**.

The database is SQLite in WAL mode. For the scheduled backup that means
`karaoke-eternal:sqlite` in [Zerobyte's hook](../zerobyte) — copying the
`.sqlite3` and its `-wal` as two files is what gives an archive that fails on
restore.

## Rooms

A room is what a player joins; the queue belongs to the room, not to the
server. That is how two parties in the same house do not share a queue, and it
is also why the player asks which room before it starts.

## Update

```bash
qh karaoke-eternal --update --apply
```

Pinned to `2.0.2`. Nothing updates on its own — a new version is applied when
you run the command above.

## Backup

```bash
qh karaoke-eternal --backup --apply --out ~/backups
```

It stops the service, packs the database, the media and the `.env`, and starts
it again.

To restore, over the current data:

```bash
qh karaoke-eternal --restore ~/backups/karaoke-eternal-20260810-1200.tar.gz --apply
```

## Remove

```bash
qh karaoke-eternal --remove --apply           # stops it, keeps the data
qh karaoke-eternal --remove --purge --apply   # and deletes the volumes and the .env
```

`--purge` deletes the media too — it lives in a volume like everything else.

## Commands

```bash
systemctl --user status karaoke-eternal
podman logs -f karaoke-eternal
podman exec karaoke-eternal wget -q --spider http://127.0.0.1:8080/ && echo ok
```

## Credits

[Karaoke Eternal](https://github.com/bhj/KaraokeEternal) by
[bhj](https://github.com/bhj) — ISC

[Official documentation](https://www.karaoke-eternal.com/docs/)
