# Referência

Onde cada arquivo mora e como um `.container` é montado, linha a linha.

## Estrutura padrão

```
~/.config/containers/
├── systemd/
│   ├── <app-simples>.container        # 1 arquivo quadlet só: solto (regra abaixo)
│   └── <app-com-varios>/              # 2+ arquivos quadlet: subpasta
│       ├── <app>-net.network
│       └── <app>.container
├── secrets/
│   └── <app>/
│       └── *.txt          # arquivos-fonte dos secrets — nunca versionar
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

No **repositório**, cada serviço tem uma pasta dentro de `apps/`, e os
arquivos `.container`/`.network` ficam na raiz dela (ex.:
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
├── _template/       # ponto de partida pra serviço novo
├── README.md        # este arquivo — as regras
└── LICENSE
```

O `apps/` é só organização do repositório: **não** tem efeito nenhum no
host, onde o layout continua sendo o de cima.

**Solto vs. subpasta em `systemd/`** — o critério é a quantidade de
arquivos Quadlet (`.container`/`.network`) do serviço:

- **Um arquivo só** (`<app>.container`, sem `.network` nem outro
  container) — fica solto direto em `~/.config/containers/systemd/`.
  Maioria dos serviços deste repositório (ex.: memos, vaultwarden,
  tsdproxy, gitea).
- **Dois ou mais arquivos** (`.network` + `.container`, ou múltiplos
  `.container` de uma stack) — ganham subpasta dedicada,
  `~/.config/containers/systemd/<app>/`, só pra agrupar os arquivos
  relacionados (o Quadlet nomeia a unit pelo *basename* de qualquer
  jeito, regra 1 — a subpasta é só organização, não muda nome de unit
  nem comportamento). Ex.: adguardhome, audiobookshelf, beszel,
  immich, karakeep, media-stack, nginx, openwebui,
  owntracks, paperless-ngx.

Cada README de serviço já traz os comandos `wget`/`mkdir` certos pro seu
caso — só seguir o que está lá.

## Anatomia de referência

### `<app>-net.network`

```ini
[Unit]
Description=Rede do <app>

[Network]
NetworkName=<app>-net
```

### `<app>.container`

```ini
[Unit]
Description=<App>
After=<outra-dependencia>.service
Requires=<outra-dependencia>.service

[Container]
Image=<registry>/<imagem>:<tag-explícita>
ContainerName=<app>
Network=<app>-net.network
PublishPort=8080:80

Volume=%h/.config/containers/volumes/<app>/data:/data:Z
EnvironmentFile=%h/.config/containers/env/<app>.env
Secret=<app>-senha,target=/run/secrets/senha

# Só se a imagem tiver shell/utilitários — ver regra 9
HealthCmd=CMD-SHELL <comando>
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

`:Z` no volume relabela SELinux como privado do container (`:z` minúsculo
= compartilhado entre containers) — só relevante em distros com SELinux
enforcing (Fedora, RHEL, openSUSE Tumbleweed/MicroOS); inofensivo/no-op
nas demais.

`%h` resolve pra `$HOME`; `%t` resolve pra `$XDG_RUNTIME_DIR` (útil pra
sockets como `%t/podman/podman.sock`).

