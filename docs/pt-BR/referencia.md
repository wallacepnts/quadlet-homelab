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
└── app.json                # tudo o que o app diz de si mesmo: veja manifesto.md
```

Não há README por app: o `app.json` guarda o título, a descrição de uma linha nos dois idiomas, a categoria,
as notas que o painel mostra, as receitas de secret e o resto ([o manifesto](./manifesto.md)), e a linha da
tabela de serviços do README raiz é gerada dele.

Na raiz, o `qhui.py` guarda a detecção de idioma e a coloração que as três
ferramentas compartilham.

## Anatomia de um `.container`

```ini
[Unit]
Description=<app>

[Container]
Image=<registry>/<imagem>
ContainerName=<app>

Network=tsdproxy-net.network
PublishPort=<host>:<container>

EnvironmentFile=%h/.config/containers/env/<app>.env
Secret=<app>-<nome>,type=env,target=<VAR>

Volume=%h/.config/containers/volumes/<app>/data:/data:Z

ReadOnly=true
Tmpfs=/tmp:size=64M
DropCapability=ALL
PidsLimit=256
NoNewPrivileges=true

HealthCmd=CMD-SHELL curl -fsS -o /dev/null http://127.0.0.1:<porta>/ || exit 1
HealthInterval=30s
HealthStartPeriod=20s
Notify=healthy

Label=tsdproxy.enable=true
Label=tsdproxy.name=<app>
Label=tsdproxy.port.web=443/https:<porta>/http

[Service]
Restart=always

[Install]
WantedBy=default.target
```

Dentro do `[Container]` toda unit mantém os mesmos blocos, na mesma ordem,
separados por uma linha em branco: **identidade** (`Image`, `ContainerName`,
`Exec`), **rede** (`Network`, `PublishPort`), **configuração** (`Environment`,
`EnvironmentFile`, `Secret`), **dados** (`SecurityLabel*`, `Volume`), **host**
(`AddDevice`, `ShmSize`, `PodmanArgs`), **endurecimento** (`ReadOnly`, `Tmpfs`,
capabilities, `User`, `PidsLimit`, `NoNewPrivileges`), **saúde** (`Health*`,
`Notify`) e os **labels**, um bloco por prefixo. A lista vive em `LAYOUT`, no
`qhui.py`.

É exigido, não sugerido: o `check.py` reprova unit fora dele, e

```bash
python3 check.py --format
```

reescreve todas as units (e o `_template/`) nele. Só muda ordem e linha em
branco — um comentário viaja com a linha abaixo dele, um bloco comentado (um
"interruptor" como o do `media-stack-gluetun`) viaja inteiro e depois das linhas
ativas de que fala, e chaves repetidas mantêm a ordem. Foi conferido contra o
que o Quadlet gera para cada unit: os argumentos do podman saem os mesmos.

Uma unit não leva labels de painel nem de vigia de atualização (`homepage.*`, `wud.*`): o
catálogo da loja lê o que mostra de outro lugar. Nome, ícone e descrição vêm das tabelas dos
README; a categoria é `category` no `app.json` do serviço, uma de AI, Automation,
Downloads, Files, Home, Media, Monitoring, Network & Security, Personal, Productivity, Tools e
Virtual Machines (a loja mostra o nome em português). Valor fora dessa lista reprova o
`check.py`, que é o que impede o catálogo de criar um grupo de um item só. O endereço da
tailnet é derivado de `tsdproxy.name`.

`%h` é a home do usuário, expandida pelo systemd. O `${TAILNET}` vem do
`~/.config/environment.d/tailnet.conf` e continua literal no `systemctl cat` —
quem mostra o valor resolvido é o `podman inspect`.

Um `Network=` ou um `Volume=` apontando pra outro Quadlet já injeta
`Requires=`/`After=`; não declarar de novo.
