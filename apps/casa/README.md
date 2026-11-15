# CasaOS

<img src="https://cdn.jsdelivr.net/gh/homarr-labs/dashboard-icons/svg/casaos.svg" width="64" height="64" alt="">

**[🇧🇷 Leia em português](./README.pt-BR.md)**

CasaOS in a container (the [dockur/casa](https://github.com/dockur/casa) build): a home server dashboard that talks to the Podman socket.

## Read this first

It works as a dashboard, but one of its two jobs did not work in testing, and the other one is a lot of access.

- **It holds your Podman socket.** It lists, starts, stops and creates *any* container of your user, the Quadlet ones included — whoever is logged in to it is, in practice, you on this host. That is why the account is created at the first start, with a generated password, and why the LAN port stays closed under the default `tailnet` access rule.
- **Installing apps from its store failed.** Tried on Podman 6.1.4 rootless, openSUSE Tumbleweed with SELinux enforcing, image `0.4.15`, through the API: the store's own Memos and a hand-written compose both ended in `making volume mountpoint for volume /DATA/AppData/memos/memos: mkdir /DATA: permission denied`. The path inside CasaOS's container is not turned into the host path, so Podman, running as you, tries to create `/DATA` at the root. `DATA_ROOT` does reach the process that installs; the conversion just did not happen. What was **not** tested: installing through the web UI, the file manager and drives, and sharing over Samba.
- **What it creates is not this repository's.** Even where an install works, the containers come out of the store's compose files: no Quadlet, no pinned tag (the store's Excalidraw is `:latest`), no hardening, no `qh`. For installing apps, use `qh` or the store (`qh-store`).
- **It changes your Podman at the first start:** it creates the `casa-net` network (`10.22.0.0/16`, set with `SUBNET` in the `.env`) and joins itself to it.

## Install

```bash
qh casa            # shows the plan
qh casa --apply
```

Open `https://casa.<your-tailnet>.ts.net`, or `http://<host-ip>:8129` with `--access local` or `both`. `qh` prints the login (`admin` and the generated password) at the end of the install.

<details>
<summary><b>Manual install</b></summary>

```bash
# 1. Download the unit (no need to clone the repository)
mkdir -p ~/.config/containers/systemd
wget -P ~/.config/containers/systemd/ \
  https://raw.githubusercontent.com/wallacepnts/quadlet-homelab/main/apps/casa/casa.container

# 2. Data directory — a bind mount requires it to exist before the start
mkdir -p ~/.config/containers/volumes/casa/data

# 3. Env — download the example. The only setting is the subnet of casa-net
mkdir -p ~/.config/containers/env
wget -O ~/.config/containers/env/casa.env \
  https://raw.githubusercontent.com/wallacepnts/quadlet-homelab/main/apps/casa/.env.example

# 4. The first account. CasaOS reads USER=<name>:<password> at the first start;
#    without it the first visitor to the port registers as the administrator
printf 'admin:%s' "$(openssl rand -hex 16)" | podman secret create casa-user -

# 5. The Podman socket
systemctl --user enable --now podman.socket

# 6. Start it
systemctl --user daemon-reload
systemctl --user start casa
```

Read the login back with `podman secret inspect casa-user --showsecret --format '{{.SecretData}}'` (the form is `admin:<password>`).

</details>

## Why the unit looks like this

Each line below was measured, and the refusals are in [docs/hardening.md](../../docs/hardening.md).

- **Root, with six capabilities.** The entrypoint refuses to run unprivileged and drops to uid 1000 itself. Without `chown`, `dac_override`, `fowner`, `setuid` or `setgid` it does not start; without `kill` it starts but a stop takes 11 s and ends in `SIGKILL`.
- **`PodmanArgs=--cgroupns=host`.** The entrypoint finds its own container by the id in `/proc/self/cgroup`. A private cgroup namespace (Podman's default) shows none, and its fallback returns the wrong name: `Failed to identify the current container!`.
- **`ContainerName=casa` stays.** It is how the entrypoint finds itself, and it connects itself to `casa-net` by that name.
- **`SecurityLabelType=container_runtime_t`** for the socket, like the other units that mount it (`:z` alone leaves the API refusing under SELinux).
- **Not read-only.** The entrypoint rewrites `/etc/group` and the user database on every start.
- **The healthcheck is `/v1/users/status`**, not `/`: the gateway answers `200` on `/` a few seconds before the user service is up, while `/v1/users/status` answers `404` until then.

## Files

```
casa.container
.env.example
install.ini
```

## Update

```bash
qh casa --update --apply
```

The version is not kept in this repository: `qh` pins the latest release on this host when it installs, and moves it with `qh casa --update --latest --apply` (the store's Update button does the same).

## Backup

```bash
qh casa --backup --apply --out ~/backups
```

It stops the service, packs the data, the `.env` and the secrets, and starts
it again. Cold on purpose: copying a live database gives an archive that only
fails when you restore it. Everything CasaOS keeps — accounts, databases, its apps' data — is under `/DATA`, which is the one volume.

To restore, over the current data:

```bash
qh casa --restore ~/backups/casa-20260809-1200.tar.gz --apply
```

It asks you to type `casa` to confirm, because the current data is deleted
before the archive is unpacked.

## Remove

```bash
qh casa --remove --apply           # stops it, keeps the data
qh casa --remove --purge --apply   # and deletes volumes, secrets and .env
```

`--purge` asks for the typed name too. The tailnet node is not deregistered by
this — that is done in the Tailscale admin.

What CasaOS created in your Podman is not removed either — the `casa-net` network and any container installed from it:

```bash
podman network rm casa-net
```

## Commands

```bash
systemctl --user status casa
podman logs -f casa
```

## Credits

[dockur/casa](https://github.com/dockur/casa) — MIT. A fork of [worph/casa-img](https://github.com/worph/casa-img), which packages CasaOS for Docker.

[IceWhaleTech/CasaOS](https://github.com/IceWhaleTech/CasaOS) — Apache-2.0
