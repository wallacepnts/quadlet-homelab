# PKVault

<img src="https://cdn.jsdelivr.net/gh/selfhst/icons/svg/pkvault.svg" width="64" height="64" alt="">

**[🇧🇷 Leia em português](./README.pt-BR.md)**

Pokémon storage and save editing in the browser, built on
[PKHeX](https://github.com/kwsch/PKHeX) — something like Pokémon HOME, for your
own save files. Move Pokémon between saves, keep them in banks and boxes outside
any save, convert them between generations, and see one Pokédex built from
every save you have, from the first generation to Legends: Z-A.

## Install

```bash
qh pkvault            # shows the plan
qh pkvault --apply
```

Then open `https://pkvault.<your-tailnet>.ts.net`.

**There is no login.** Whoever reaches the page can edit and delete your saves.
On the tailnet that is you. With `--access tailnet`, the default, the LAN port
is not even published; with `local` or `both`, port `8126` is open to everyone
on your network — choose those only on a LAN that is yours alone.

<details>
<summary><b>Manual install (advanced)</b></summary>

```bash
# 1. Download the unit (no need to clone the repository)
mkdir -p ~/.config/containers/systemd
wget -P ~/.config/containers/systemd/ \
  https://raw.githubusercontent.com/wallacepnts/quadlet-homelab/main/apps/pkvault/pkvault.container

# 2. The data directory: database, storage, backups, logs and uploaded saves
mkdir -p ~/.config/containers/volumes/pkvault/data

systemctl --user daemon-reload
systemctl --user start pkvault
```

</details>

## Files

```
pkvault.container   unit
install.ini         where updates come from
```

Everything lives in `~/.config/containers/volumes/pkvault/data`: `db/` (SQLite),
`storage/` (the Pokémon kept outside saves), `backup/`, `logs/`,
`saves-uploads/`, and the app's settings in `config/pkvault.json`.

## Getting your saves in and out

The first start creates a sample Emerald save, so the app has something to show.
Remove it in the settings when yours are in.

- **Upload in the browser** — the simplest way: up to 5 files, 60 MB in total,
  stored in `saves-uploads/`. Each save has a download button to take the
  edited file back to the game or emulator.
- **A folder on the host** — for saves that live on this machine. Put them
  under the volume, for example in `data/saves/`, and add `/pkvault/saves/` to
  the save locations in the settings. **Copy them in with `cp`, not `mv`**:
  measured, a file moved from another folder keeps its old SELinux label and the
  container cannot read it, while a copy takes the folder's label.

To keep saves in step with other devices, the project recommends Syncthing
(which this repository also has). A folder mounted by two units uses `:z`, not
`:Z` — rule 16 of the conventions.

Every change is written to a save only when you press save in the app, and a
backup of all saves and storage is taken before each write. `BACKUP_FILE_COUNT_LIMIT=30`
keeps the latest 30 — without it the folder only grows. Measured: with the
limit at 2, four backups leave two on disk.

## Hardening

Read-only root, four capabilities (`chown`, `dac_override`, `setgid`, `setuid`),
no `User=`. Tested by exercising the app — a save uploaded, a backup taken, a
Pokémon moved from a save into storage and the save written back.

The image runs supervisord as root, with nginx on 3000 in front of the .NET
backend on 5000. That is what bounds it: nginx, as root, writes into a folder
owned by the `nginx` user, which takes those four capabilities, and
`supervisord.conf` declares `user=root`, which refuses any other user. The
details are in [the refusals](../../docs/hardening.md#refusals-on-record).

Two things in the unit follow from that:

- `Tmpfs=/var/lib/nginx/tmp` carries `mode=1777`: nginx spools every upload
  over 16 KB there, and without it uploading a save answered 500.
- `HealthCmd` asks the API, not just the page: with nginx dead, supervisord
  kept the container `Up`, and `/api/settings` only answers when nginx and the
  backend both do.

## Update

```bash
qh pkvault --update --apply
```

Pinned to `2.3.4`. Nothing updates on its own. The image is tagged without the
`v` the release carries. PKVault bundles its own PKHeX (26.8.26 in 2.3.3), so
support for a new game arrives with a PKVault release. The page checks GitHub
for a newer release from your browser; that is the only outside call.

## Backup

```bash
qh pkvault --backup --apply --out ~/backups
```

The app's own backups are in the same volume, so this copies them too.

## Remove

```bash
qh pkvault --remove --apply           # stops it, keeps the data
qh pkvault --remove --purge --apply   # and deletes the volume
```

The tailnet node is not deregistered by this — that is done in the Tailscale admin.

## Commands

```bash
systemctl --user status pkvault
podman logs -f pkvault
curl -s http://127.0.0.1:8126/api/settings   # version, paths, bundled PKHeX
```

## Credits

[Chnapy/PKVault](https://github.com/Chnapy/PKVault), by Richard Haddad — GPL-3.0.
Built on [PKHeX](https://github.com/kwsch/PKHeX) by Kaphotics — GPL-3.0.
Pokémon images and names are © The Pokémon Company.

[Official documentation](https://github.com/Chnapy/PKVault/blob/main/docs/functional/en/README.md)
