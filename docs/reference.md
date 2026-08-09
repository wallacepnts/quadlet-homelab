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
├── install.ini             # secret recipes, login, upstream name
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
PublishPort=<host>:<container>

Volume=%h/.config/containers/volumes/<app>/data:/data:Z
EnvironmentFile=%h/.config/containers/env/<app>.env
Secret=<app>-<name>,type=env,target=<VAR>

NoNewPrivileges=true
PidsLimit=256
DropCapability=ALL
ReadOnly=true
Tmpfs=/tmp:size=64M

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
