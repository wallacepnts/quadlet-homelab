# nginx — Podman Quadlet (rootless)

**[🇬🇧 Read in English](./README.md)**

Deploy do [nginx](https://nginx.org) como servidor de arquivos estáticos
via Podman Quadlet, usando a imagem oficial
[`nginx`](https://hub.docker.com/_/nginx) (variante Alpine).

## Arquitetura

Container único. Dois bind mounts, ambos `:ro` de propósito (o nginx só
lê, quem edita é você direto no host):

- `html/` → `/usr/share/nginx/html` — o conteúdo estático em si (o que
  fica montado aqui é o que é servido).
- `conf.d/` → `/etc/nginx/conf.d` — server blocks. **Não pode ficar
  vazio**: montar um diretório vazio por cima de `/etc/nginx/conf.d`
  apaga o `default.conf` embutido da imagem — sem nenhum `server {
  listen 80; }`, o nginx sobe mas não escuta em porta nenhuma
  (`wget: can't connect to remote host` no healthcheck, testado na
  prática). Por isso este repositório versiona uma cópia do
  `default.conf` original da imagem em `conf.d/` — baixado no passo 2 da
  instalação; editar esse arquivo (ou adicionar outros `.conf` do lado)
  pra customizar rotas.

## Arquivos

```
nginx.container         # unit principal

conf.d/
└── default.conf        # cópia do default.conf original da imagem
```

Sem `.env.example` — nada aqui depende de variável de ambiente.

## Pré-requisitos

- Podman rootless com systemd `--user` funcionando

## Instalação

```bash
python3 install.py nginx            # dry-run: mostra o que vai fazer
python3 install.py nginx --apply
```

Só na rede local, `--access local`; na tailnet e na LAN, `--access
both`. Acrescentar `--href-local` faz o link do dashboard apontar pra LAN. O script cria os diretórios, grava o
`.env`, gera os secrets, ajusta o dono dos volumes, sobe o serviço e
imprime o endereço no fim — ver
[Instalando e operando](../../docs/pt-BR/instalacao.md) no README
raiz.

Acessar em `http://<ip-do-host>:8103`, ou via [tsdproxy](../tsdproxy/README.pt-BR.md)
(tailnet) em `https://nginx.<your-tailnet>.ts.net`.

<details>
<summary><b>Instalação manual</b> (avançado) — os mesmos passos, um a um</summary>


```bash
# 1. Baixar as units (sem precisar clonar o repositório)
mkdir -p ~/.config/containers/systemd
wget -P ~/.config/containers/systemd/ \
  https://raw.githubusercontent.com/wallacepnts/quadlet-homelab/main/apps/nginx/nginx.container

# 2. Diretórios de dados — bind mount exige que já existam antes do start
mkdir -p ~/.config/containers/volumes/nginx/{html,conf.d}
echo "<h1>Funcionando</h1>" > ~/.config/containers/volumes/nginx/html/index.html
wget -O ~/.config/containers/volumes/nginx/conf.d/default.conf \
  https://raw.githubusercontent.com/wallacepnts/quadlet-homelab/main/apps/nginx/conf.d/default.conf

# 3. Subir
systemctl --user daemon-reload
systemctl --user start nginx
```

Acessar em `http://<ip-do-host>:8103`, ou via [tsdproxy](../tsdproxy/README.pt-BR.md)
(tailnet) em `https://nginx.<your-tailnet>.ts.net`.

</details>

## Auto-update

Sem `AutoUpdate=` — tag explícita (`1.30.4-alpine`, atual `stable`),
bump manual ([regra 9](../../docs/pt-BR/convencoes.md)). A imagem tem `wget`/healthcheck
real — daria pra habilitar `AutoUpdate=registry` com rollback de
verdade, mas mantido manual por padrão como o resto do repositório.

## Backup & Recuperação

```bash
tar -czf nginx-backup-$(date +%Y%m%d-%H%M%S).tar.gz \
  -C ~/.config/containers/volumes nginx
```

Sem precisar parar o container (leitura só, sem estado próprio além do
conteúdo estático).

## Comandos úteis

```bash
systemctl --user status nginx
podman logs -f nginx
podman exec nginx wget -qO- http://127.0.0.1:80/
```

## Créditos

Deploy Quadlet usando a imagem oficial [nginx](https://hub.docker.com/_/nginx)
(BSD-2-Clause).
