# Omni Tools

<img src="https://cdn.jsdelivr.net/gh/homarr-labs/dashboard-icons/png/omni-tools.png" width="64" height="64" alt="">

**[🇧🇷 Leia em português](./README.pt-BR.md)**

Converters, generators and calculators that run in the browser — nothing is sent to the server.

## Install

```bash
qh omni-tools            # shows the plan
qh omni-tools --apply
```

Open `http://<host-ip>:8101` or `https://omni-tools.<your-tailnet>.ts.net`.

<details>
<summary><b>Manual install</b></summary>

```bash
# 1. Download the unit (no need to clone the repository)
mkdir -p ~/.config/containers/systemd
wget -P ~/.config/containers/systemd/ \
  https://raw.githubusercontent.com/wallacepnts/quadlet-homelab/main/apps/omni-tools/omni-tools.container

# 2. Start it — sem mkdir, sem secret, sem env
systemctl --user daemon-reload
systemctl --user start omni-tools
```

</details>

## Files

```
omni-tools.container
```

## Update

```bash
qh omni-tools --update --apply
```

Pinned to `0.6.0`. Nothing updates on its own — a new version is applied
when you run the command above.

## Backup

```bash
qh omni-tools --backup --apply --out ~/backups
```

It stops the service, packs the data, the `.env` and the secrets, and starts
it again. Cold on purpose: copying a live database gives an archive that only
fails when you restore it.

To restore, over the current data:

```bash
qh omni-tools --restore ~/backups/omni-tools-20260809-1200.tar.gz --apply
```

It asks you to type `omni-tools` to confirm, because the current data is deleted
before the archive is unpacked.

## Remove

```bash
qh omni-tools --remove --apply           # stops it, keeps the data
qh omni-tools --remove --purge --apply   # and deletes volumes, secrets and .env
```

`--purge` asks for the typed name too. The tailnet node is not deregistered by
this — that is done in the Tailscale admin.

## Commands

```bash
systemctl --user status omni-tools
podman logs -f omni-tools
```

## Credits

[iib0011/omni-tools](https://github.com/iib0011/omni-tools) — MIT

[Official documentation](https://omnitools.app)
