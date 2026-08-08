# Reference

Where every file lives, and how a `.container` is put together, line by line.

## The standard layout

```
~/.config/containers/
├── systemd/
│   ├── <simple-app>.container         # a single quadlet file: loose (rule below)
│   └── <app-with-several>/            # 2+ quadlet files: a subfolder
│       ├── <app>-net.network
│       └── <app>.container
├── secrets/
│   └── <app>/
│       └── *.txt          # the secrets' source files — never version these
├── env/
│   └── <app>.env
└── volumes/
    └── <app>/
        ├── config/
        └── data/
```

```bash
mkdir -p ~/.config/containers/{systemd,secrets,env,volumes}
```

In the **repository**, each service has a folder inside `apps/`, and the
`.container`/`.network` files sit at its root (e.g.
`apps/memos/memos.container`):

```
quadlet-homelab/
├── apps/
│   ├── memos/
│   │   ├── memos.container
│   │   └── README.md
│   └── immich/
│       ├── immich.container
│       ├── immich-postgres.container
│       ├── immich-net.network
│       └── README.md
├── _template/       # a starting point for a new service
├── README.md        # the index and the version table
└── LICENSE
```

`apps/` is repository organisation only: it has **no** effect on the host,
where the layout is still the one above.

**Loose vs. subfolder in `systemd/`** — the criterion is how many Quadlet
files (`.container`/`.network`) the service has:

- **A single file** (`<app>.container`, with no `.network` and no other
  container) — it goes loose, straight in `~/.config/containers/systemd/`.
  Most services in this repository (memos, vaultwarden, tsdproxy, gitea).
- **Two or more files** (`.network` + `.container`, or several `.container`
  files of a stack) — they get a dedicated subfolder,
  `~/.config/containers/systemd/<app>/`, purely to group the related files
  (Quadlet names the unit after the *basename* either way, rule 1 — the
  subfolder is organisation only; it changes neither the unit name nor the
  behaviour). For example adguardhome, audiobookshelf, beszel, immich,
  karakeep, media-stack, nginx, openwebui, owntracks, paperless-ngx.

Each service's README already carries the right `wget`/`mkdir` commands for
its case — just follow what is there.

## Reference anatomy

### `<app>-net.network`

```ini
[Unit]
Description=<app> network

[Network]
NetworkName=<app>-net
```

### `<app>.container`

```ini
[Unit]
Description=<App>
After=<other-dependency>.service
Requires=<other-dependency>.service

[Container]
Image=<registry>/<image>:<explicit-tag>
ContainerName=<app>
Network=<app>-net.network
PublishPort=8080:80

Volume=%h/.config/containers/volumes/<app>/data:/data:Z
EnvironmentFile=%h/.config/containers/env/<app>.env
Secret=<app>-password,target=/run/secrets/password

# Only if the image has a shell or utilities — see rule 9
HealthCmd=CMD-SHELL <command>
HealthInterval=5s
HealthTimeout=5s
HealthRetries=12
Notify=healthy

[Service]
Restart=always
TimeoutStartSec=120

[Install]
WantedBy=default.target
```

`:Z` on a volume relabels it in SELinux as private to the container
(lowercase `:z` = shared between containers) — only relevant on distros with
SELinux enforcing (Fedora, RHEL, openSUSE Tumbleweed/MicroOS); harmless and a
no-op elsewhere.

`%h` resolves to `$HOME`; `%t` resolves to `$XDG_RUNTIME_DIR` (useful for
sockets such as `%t/podman/podman.sock`).
