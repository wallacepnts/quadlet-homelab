# CookCLI

<img src="https://cdn.simpleicons.org/gnubash" width="64" height="64" alt="">

**[🇧🇷 Leia em português](./README.pt-BR.md)**

Plain-text recipes in the CookLang format — versionable in git, with no database and no forms.

## Install

```bash
qh cookcli            # shows the plan
qh cookcli --apply
```

Open `http://<host-ip>:9080` or `https://cookcli.<your-tailnet>.ts.net`.

<details>
<summary><b>Manual install</b></summary>

```bash
# 1. Download the unit (no need to clone the repository)
mkdir -p ~/.config/containers/systemd
wget -P ~/.config/containers/systemd/ \
  https://raw.githubusercontent.com/wallacepnts/quadlet-homelab/main/apps/cookcli/cookcli.container

# 2. The recipes folder. Do NOT chown it here: it is yours, and the unit's
#    keep-id is precisely what makes the container accept that.
mkdir -p ~/.config/containers/volumes/cookcli/recipes

# 3. Start it
systemctl --user daemon-reload
systemctl --user start cookcli
```

</details>

## Files

```
cookcli.container
aisle.conf.example
bolo-de-cenoura.cook.example
calda-de-chocolate.cook.example
pantry.conf.example
semana.menu.example
install.ini
```

## Update

```bash
qh cookcli --update --apply
```

Pinned to `0.32.1`. Nothing updates on its own — a new version is applied
when you run the command above.

## Backup

```bash
qh cookcli --backup --apply --out ~/backups
```

It stops the service, packs the data, the `.env` and the secrets, and starts
it again. Cold on purpose: copying a live database gives an archive that only
fails when you restore it.

To restore, over the current data:

```bash
qh cookcli --restore ~/backups/cookcli-20260809-1200.tar.gz --apply
```

It asks you to type `cookcli` to confirm, because the current data is deleted
before the archive is unpacked.

## Remove

```bash
qh cookcli --remove --apply           # stops it, keeps the data
qh cookcli --remove --purge --apply   # and deletes volumes, secrets and .env
```

`--purge` asks for the typed name too. The tailnet node is not deregistered by
this — that is done in the Tailscale admin.

## Commands

```bash
systemctl --user status cookcli
podman logs -f cookcli
```

## Credits

[cooklang/cookcli](https://github.com/cooklang/cookcli) — MIT

[Official documentation](https://demo.cooklang.org)
