# Reference

## On the host

```
~/.config/containers/
├── systemd/
│   ├── <app>.container         # one quadlet file: loose
│   └── <app>/                  # two or more: a subfolder of its own
│       ├── <app>-net.network
│       └── <app>.container
├── secrets/<app>/*.txt         # the secrets' source files — never versioned
├── env/<app>.env
└── volumes/<app>/{config,data}
```

Loose or subfolder is decided by how many Quadlet files the service has, not by
how many containers.

## In the repository

```
apps/<app>/
├── <app>.container
├── <app>-net.network       # only for a stack that talks to itself
├── .env.example
├── install.ini             # secret recipes, validation, login, upstream name
├── README.md
└── README.pt-BR.md
```

At the root, `qhui.py` holds the language detection and the colouring the
three tools share.

## Anatomy of a `.container`

```ini
[Unit]
Description=<app>

[Container]
Image=<registry>/<image>:<tag>
ContainerName=<app>

Network=tsdproxy-net.network
PublishPort=<host>:<container>

EnvironmentFile=%h/.config/containers/env/<app>.env
Secret=<app>-<name>,type=env,target=<VAR>

Volume=%h/.config/containers/volumes/<app>/data:/data:Z

ReadOnly=true
Tmpfs=/tmp:size=64M
DropCapability=ALL
PidsLimit=256
NoNewPrivileges=true

HealthCmd=CMD-SHELL curl -fsS -o /dev/null http://127.0.0.1:<port>/ || exit 1
HealthInterval=30s
HealthStartPeriod=20s
Notify=healthy

Label=tsdproxy.enable=true
Label=tsdproxy.name=<app>
Label=tsdproxy.port.web=443/https:<port>/http

Label=homepage.group=<group>
Label=homepage.name=<App>
Label=homepage.icon=<url>
Label=homepage.href=https://<app>.${TAILNET}.ts.net
Label=homepage.description="<one line>"

[Service]
Restart=always

[Install]
WantedBy=default.target
```

Inside `[Container]` every unit keeps the same blocks, in the same order, a
blank line apart: **identity** (`Image`, `ContainerName`, `Exec`), **network**
(`Network`, `PublishPort`), **configuration** (`Environment`, `EnvironmentFile`,
`Secret`), **data** (`SecurityLabel*`, `Volume`), **host** (`AddDevice`,
`ShmSize`, `PodmanArgs`), **hardening** (`ReadOnly`, `Tmpfs`, capabilities,
`User`, `PidsLimit`, `NoNewPrivileges`), **health** (`Health*`, `Notify`), and
the **labels**, one block per prefix. The list lives in `LAYOUT` in `qhui.py`.

It is enforced, not suggested: `check.py` fails a unit that is out of it, and

```bash
python3 check.py --format
```

rewrites every unit (and `_template/`) into it. Nothing but order and blank
lines changes — a comment moves with the line under it, a commented-out block
(a "switch" like the one in `media-stack-gluetun`) moves whole and after the
active lines it talks about, and repeated keys keep their order. It was
checked against what Quadlet generates for every unit: the podman arguments
come out the same.

`homepage.group` is one of AI, Automation, Downloads, Files, Home, Media,
Monitoring, `"Network & Security"`, Personal, Productivity, Tools and
`"Virtual Machines"` — quoted when it has a space. A value outside that set
fails `qh --selftest`, which is what keeps the dashboard from growing a
group of one.

`%h` is the user's home, expanded by systemd. `${TAILNET}` comes from
`~/.config/environment.d/tailnet.conf` and stays literal in `systemctl cat` —
`podman inspect` shows the resolved value.

A `Network=` or a `Volume=` pointing at another Quadlet already injects
`Requires=`/`After=`; do not declare them again.
