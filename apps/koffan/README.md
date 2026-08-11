# Koffan

<img src="https://cdn.jsdelivr.net/gh/homarr-labs/dashboard-icons/png/koffan.png" width="64" height="64" alt="">

**[🇧🇷 Leia em português](./README.pt-BR.md)**

The house's shopping list. Everyone opens the same list on their phone, ticks
things off in the aisle, and the others see it change.

There are no accounts: one password lets you in, and whoever has it edits. That
is the whole model, and it is why this fits a family and not a company.

## Install

```bash
qh koffan            # shows the plan
qh koffan --apply
```

`qh` generates the password and prints it once, at the end of the install.
Open `https://koffan.<your-tailnet>.ts.net`.

<details>
<summary><b>Manual install (advanced)</b></summary>

```bash
mkdir -p ~/.config/containers/systemd ~/.config/containers/env
mkdir -p ~/.config/containers/volumes/koffan/data

wget -P ~/.config/containers/systemd/ \
  https://raw.githubusercontent.com/wallacepnts/quadlet-homelab/main/apps/koffan/koffan.container
wget -O ~/.config/containers/env/koffan.env \
  https://raw.githubusercontent.com/wallacepnts/quadlet-homelab/main/apps/koffan/.env.example

openssl rand -base64 18 | tr -d '\n' | podman secret create koffan-password -

# The container runs as uid 1000, which is not yours after the mapping
podman unshare chown -R 1000:1000 ~/.config/containers/volumes/koffan

systemctl --user daemon-reload
systemctl --user start koffan
```

</details>

## Files

```
koffan.container   unit
.env.example       environment
install.ini
```

The list is `shopping.db` under `~/.config/containers/volumes/koffan/data`.
SQLite with WAL on, so the folder holds three files that only make sense
together — which is exactly what the zerobyte hook's `sqlite` mode copies
consistently.

## The password

It is the only credential, so it is a Podman secret and not a line in the
`.env` the upstream compose suggests — the shipped default there is
`shopping123`. `qh` generates it with `rand-base64 18` and shows it once.

To change it later:

```bash
podman secret rm koffan-password
openssl rand -base64 18 | tr -d '\n' | podman secret create koffan-password -
qh koffan --update --apply
```

## Notifications

`WEBHOOK_URL` in the `.env` is called on every change. Pointed at the
[ntfy](../ntfy) here, the phone buzzes when someone adds bread on the way home:

```ini
WEBHOOK_URL=http://ntfy:2586/groceries
```

Both containers are on `tsdproxy-net`, so `ntfy` resolves by name.

## Update

```bash
qh koffan --update --apply
```

Pinned to `v2.13.0`.

## Backup

```bash
qh koffan --backup --apply --out ~/backups
```

Stops it, packs the data folder and the `.env`, starts it again.

To restore, over the current data:

```bash
qh koffan --restore ~/backups/koffan-20260811-1200.tar.gz --apply
```

## Remove

```bash
qh koffan --remove --apply           # stops it, keeps the list
qh koffan --remove --purge --apply   # and deletes the volume and the secret
```

## Commands

```bash
systemctl --user status koffan
podman logs -f koffan
```

## Credits

[PanSalut/Koffan](https://github.com/PanSalut/Koffan) by Artur Witoś.

The licence is **MIT with the Commons Clause**: free to run and to change, but
it forbids selling the software or a service whose value is substantially the
software itself. Self-hosting it at home is exactly what it allows — the clause
is worth knowing about before building anything commercial on top.

[Official documentation](https://github.com/PanSalut/Koffan#readme)
