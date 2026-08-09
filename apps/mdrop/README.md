# mdrop

<img src="https://cdn.simpleicons.org/markdown" width="64" height="64" alt="">

**[🇧🇷 Leia em português](./README.pt-BR.md)**

Converts PDF, Office, image and audio to Markdown over the web, stateless and without leaving the machine.

## Install

```bash
qh mdrop            # shows the plan
qh mdrop --apply
```

Open `http://<host-ip>:8292` or `https://mdrop.<your-tailnet>.ts.net`.

<details>
<summary><b>Manual install</b></summary>

```bash
# 1. Download the unit (no need to clone the repository)
mkdir -p ~/.config/containers/systemd
wget -P ~/.config/containers/systemd/ \
  https://raw.githubusercontent.com/wallacepnts/quadlet-homelab/main/apps/mdrop/mdrop.container

# 2. Start it — sem mkdir, sem secret, sem env
systemctl --user daemon-reload
systemctl --user start mdrop
```

</details>

## Files

```
mdrop.container
```

## Update

```bash
qh mdrop --update --apply
```

Pinned to `692d8f63593667d78ef67d3b79b9e68ce22c8244ace30036fac0fd24cd529ca4`. Nothing updates on its own — a new version is applied
when you run the command above.

## Backup

```bash
qh mdrop --backup --apply --out ~/backups
```

It stops the service, packs the data, the `.env` and the secrets, and starts
it again. Cold on purpose: copying a live database gives an archive that only
fails when you restore it.

To restore, over the current data:

```bash
qh mdrop --restore ~/backups/mdrop-20260809-1200.tar.gz --apply
```

It asks you to type `mdrop` to confirm, because the current data is deleted
before the archive is unpacked.

## Remove

```bash
qh mdrop --remove --apply           # stops it, keeps the data
qh mdrop --remove --purge --apply   # and deletes volumes, secrets and .env
```

`--purge` asks for the typed name too. The tailnet node is not deregistered by
this — that is done in the Tailscale admin.

## Commands

```bash
systemctl --user status mdrop
podman logs -f mdrop
```

## Credits

[samapriya/mdrop](https://github.com/samapriya/mdrop) — MIT

[Official documentation](https://mdrop.remotelab.dev)
