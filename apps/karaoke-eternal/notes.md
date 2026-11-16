Put the karaoke files in
`~/.config/containers/volumes/karaoke-eternal/media`, then open
`http://<host-ip>:8017` or `https://karaoke.<your-tailnet>.ts.net`. **The first
account you create is the admin.** In the app, add `/mnt/karaoke` under Media
Folders and scan.

It reads CDG+MP3 and MP4; the filename is what it parses for artist and title,
so `Artist - Title.mp4` is the shape to aim for.

### Rooms

A room is what a player joins; the queue belongs to the room, not to the
server. That is how two parties in the same house do not share a queue, and it
is also why the player asks which room before it starts.

### Backup

It stops the service, packs the database, the media and the `.env`, and starts
it again.

### Remove

`--purge` deletes the media too — it lives in a volume like everything else.
