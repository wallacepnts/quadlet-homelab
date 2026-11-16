# Kiwix

<img src="https://cdn.jsdelivr.net/gh/homarr-labs/dashboard-icons/svg/kiwix.svg" width="64" height="64" alt="">

**[🇧🇷 Leia em português](./README.pt-BR.md)**

Wikipedia on your own disk, and everything else Kiwix packages: Stack Overflow,
Project Gutenberg, TED talks, Wiktionary, medical and repair manuals. Served
over HTTP, searchable, and it keeps working with the internet unplugged.

Each library is one `.zim` file — a compressed, indexed snapshot. You choose
which ones to keep, and they cost what they cost: Portuguese Wikipedia without
images is around 5 GB, with images closer to 40 GB.

## First run

**It does not start empty.** With no `.zim` in the volume, `kiwix-serve` says
`Unable to add the ZIM file '*.zim' to the internal library` and exits — so the
install leaves the service in place and stopped. Put a library in
`~/.config/containers/volumes/kiwix/data` and start it:

```bash
cd ~/.config/containers/volumes/kiwix/data
wget https://download.kiwix.org/zim/wikipedia/wikipedia_pt_all_nopic_2026-07.zim
podman unshare chown 1001:1001 *.zim
systemctl --user start kiwix
```

The catalogue is at [library.kiwix.org](https://library.kiwix.org).

## Files

```
kiwix.container   unit
.env.example      environment
```

The volume holds the `.zim` files and nothing else. It is the one folder in
this repository where the size is the point — plan the disk before the first
download.

## How it knows which files to serve

```ini
Exec=*.zim
```

Not a shell trick that happens to work: the image's own `start.sh` builds
`kiwix-serve --port=$PORT $@` and runs it **unquoted**, from `/data`. The glob
is expanded there, so every `.zim` in the volume is served and a new one only
needs a restart.

## Downloading on start

`DOWNLOAD=<url>` in the `.env` fetches a file into the volume before serving.
Useful for the first one, and a bad habit after that: it runs on every start,
and a full Wikipedia is 100 GB. Once a library is in place, put new ones in the
folder by hand.

## Hardening

The whole ladder: `ReadOnly=true`, every capability dropped, `User=1001` — the
`user` the image itself runs as. Measured with a real library downloaded and
served, not just with the container up.

`ReadOnly=true` does not stop the download: the volume is a bind mount, and
read-only applies to the container's own filesystem.

## Update

The libraries update on their own schedule, which is yours: download the newer `.zim`, delete the old one, restart.

## Backup

Deliberately not covered by the backup jobs: a `.zim` is a public file you can
download again, and copying tens of gigabytes of Wikipedia into a Restic
repository would cost far more than fetching it a second time.

## Credits

[kiwix/kiwix-tools](https://github.com/kiwix/kiwix-tools) — GPL-3.0.

[Official documentation](https://wiki.kiwix.org/)
