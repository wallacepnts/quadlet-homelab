# Referência

## No host

```
~/.config/containers/
├── systemd/
│   ├── <app>.container         # um arquivo quadlet: solto
│   └── <app>/                  # dois ou mais: subpasta própria
│       ├── <app>-net.network
│       └── <app>.container
├── secrets/<app>/*.txt         # os arquivos de origem dos secrets — nunca versionados
├── env/<app>.env
└── volumes/<app>/{config,data}
```

Solto ou em subpasta se decide por quantos arquivos Quadlet o serviço tem, não
por quantos containers.

## No repositório

```
apps/<app>/
├── <app>.container
├── <app>-net.network       # só pra stack que conversa entre si
├── .env.example
├── install.ini             # receitas de secret, login, nome no upstream
├── README.md
└── README.pt-BR.md
```

Na raiz, o `qhui.py` guarda a detecção de idioma e a coloração que as três
ferramentas compartilham.

## Anatomia de um `.container`

```ini
[Unit]
Description=<app>

[Container]
Image=<registry>/<imagem>:<tag>
ContainerName=<app>
PublishPort=<host>:<container>

Volume=%h/.config/containers/volumes/<app>/data:/data:Z
EnvironmentFile=%h/.config/containers/env/<app>.env
Secret=<app>-<nome>,type=env,target=<VAR>

NoNewPrivileges=true
PidsLimit=256
DropCapability=ALL
ReadOnly=true
Tmpfs=/tmp:size=64M

HealthCmd=CMD-SHELL curl -fsS -o /dev/null http://127.0.0.1:<porta>/ || exit 1
HealthInterval=30s
HealthStartPeriod=20s
Notify=healthy

Label=tsdproxy.enable=true
Label=tsdproxy.name=<app>
Label=tsdproxy.port.web=443/https:<porta>/http
Label=homepage.group=Self-Hosted
Label=homepage.name=<App>
Label=homepage.icon=<url>
Label=homepage.href=https://<app>.${TAILNET}.ts.net
Label=homepage.description="<uma linha>"

[Service]
Restart=always

[Install]
WantedBy=default.target
```

O `%h` é a home do usuário, expandida pelo systemd. O `${TAILNET}` vem do
`~/.config/environment.d/tailnet.conf` e continua literal no `systemctl cat` —
quem mostra o valor resolvido é o `podman inspect`.

Um `Network=` ou um `Volume=` apontando pra outro Quadlet já injeta
`Requires=`/`After=`; não declarar de novo.
