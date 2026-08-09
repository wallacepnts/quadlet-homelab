# Memos

<img src="https://cdn.jsdelivr.net/gh/homarr-labs/dashboard-icons/svg/memos.svg" width="64" height="64" alt="">

**[🇧🇷 Leia em português](./README.pt-BR.md)**

Self-hosted quick notes, markdown-native and lightweight.

## Install

```bash
qh memos            # shows the plan
qh memos --apply
```

Open `http://<host-ip>:5230` or `https://memos.<your-tailnet>.ts.net` and
create the account. **The first user to sign up becomes admin**, with no email
confirmation. Right after that, turn signup off in Settings → "Allow user
signup", or anyone who reaches the URL can create an account.

<details>
<summary><b>Manual install</b></summary>

```bash
mkdir -p ~/.config/containers/systemd ~/.config/containers/env
mkdir -p ~/.config/containers/volumes/memos/data
podman unshare chown -R 1000:1000 ~/.config/containers/volumes/memos

wget -P ~/.config/containers/systemd/ \
  https://raw.githubusercontent.com/wallacepnts/quadlet-homelab/main/apps/memos/memos.container
wget -O ~/.config/containers/env/memos.env \
  https://raw.githubusercontent.com/wallacepnts/quadlet-homelab/main/apps/memos/.env.example

systemctl --user daemon-reload
systemctl --user start memos
```

</details>

## Files

```
memos.container   unit
.env.example      environment
```

Data in `~/.config/containers/volumes/memos/data` on port **5230**.

## Update

```bash
qh memos --update --apply
```

Pinned to `0.30.0`. Nothing updates on its own — a new version is applied
when you run the command above.

## Backup

```bash
qh memos --backup --apply --out ~/backups
```

It stops the service, packs the data, the `.env` and the secrets, and starts it
again. Cold on purpose: copying a live database gives an archive that only
fails when you restore it.

To restore, over the current data:

```bash
qh memos --restore ~/backups/memos-20260809-1200.tar.gz --apply
```

It asks you to type `memos` to confirm, because the current data is deleted
before the archive is unpacked.

## Remove

```bash
qh memos --remove --apply           # stops it, keeps the data
qh memos --remove --purge --apply   # and deletes volumes, secrets and .env
```

`--purge` asks for the typed name too. The tailnet node is not deregistered by
this — that is done in the Tailscale admin.

## Commands

```bash
systemctl --user status memos
podman logs -f memos
podman exec memos wget -qO- http://127.0.0.1:5230/healthz
```

## Credits

[Memos](https://github.com/usememos/memos) — MIT

[Official documentation](https://www.usememos.com/docs)
