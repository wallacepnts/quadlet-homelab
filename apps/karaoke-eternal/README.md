# Karaoke Eternal

<img src="https://api.iconify.design/mdi/microphone-variant.svg?color=%23888888" width="64" height="64" alt="">

**[🇧🇷 Leia em português](./README.pt-BR.md)**

A karaoke party from your own library. Everyone queues songs from their phone,
and one screen — a TV, a laptop — runs the player fullscreen. The player is
just a page in the same app, so it needs no install.

## First run

Put the karaoke files in
`~/.config/containers/volumes/karaoke-eternal/media`, then open
`http://<host-ip>:8017` or `https://karaoke.<your-tailnet>.ts.net`. **The first
account you create is the admin.** In the app, add `/mnt/karaoke` under Media
Folders and scan.

It reads CDG+MP3 and MP4; the filename is what it parses for artist and title,
so `Artist - Title.mp4` is the shape to aim for.

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

## Backup

It stops the service, packs the database, the media and the `.env`, and starts
it again.

## Remove

`--purge` deletes the media too — it lives in a volume like everything else.

## Credits

[Karaoke Eternal](https://github.com/bhj/KaraokeEternal) by
[bhj](https://github.com/bhj) — ISC

[Official documentation](https://www.karaoke-eternal.com/docs/)
