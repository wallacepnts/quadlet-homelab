# Omni Tools — Podman Quadlet (rootless)

**[🇬🇧 Read in English](./README.md)**

Deploy do [Omni Tools](https://github.com/iib0011/omni-tools) (caixa de
ferramentas offline) via Podman Quadlet, usando a imagem oficial
`docker.io/iib0011/omni-tools`.

Conversores, geradores, calculadoras, manipulação de imagem, JSON, texto,
data, hash. Substitui aqueles sites de utilitário onde você cola dado —
às vezes dado sensível — num servidor de terceiro.

## Arquitetura

Container único, nginx servindo um app estático. **Sem volume e sem
banco, de propósito**: tudo roda no navegador, o servidor só entrega os
arquivos. Nada do que você converte passa pelo servidor — é o ponto do
projeto, e é o que faz o backup deste serviço ser "nenhum".

### Hardening: herda os limites do nginx

Testado na prática, e o resultado é o mesmo do [nginx](../nginx/README.pt-BR.md) deste
repositório:

- `DropCapability=ALL` sozinho é recusado — `chown("/var/cache/nginx/client_temp", 101) failed (1: Operation not permitted)`
- `ReadOnly=true` é recusado — `10-listen-on-ipv6-by-default.sh: can not modify /etc/nginx/conf.d/default.conf`

O entrypoint da imagem nginx reescreve config no start; é o caso clássico
citado na [regra 20](../../docs/pt-BR/convencoes.md). O kit de 4 capabilities
(`CHOWN`, `SETUID`, `SETGID`, `NET_BIND_SERVICE`) é o mínimo que sobe.

### A tag está no Docker Hub, não no ghcr

O `ghcr.io/iib0011/omni-tools` publica **só `latest`** — a listagem de
tags do ghcr devolve uma entrada. As versões numeradas (`0.6.0`, `0.5.0`…)
estão no Docker Hub, que é de onde esta unit puxa, pra poder pinar como
manda a regra 9.

## Arquivos

```
omni-tools.container   # unit principal
```

## Instalação

```bash
python3 install.py omni-tools            # dry-run: mostra o que vai fazer
python3 install.py omni-tools --apply
```

Só na rede local, `--access local`; na tailnet e na LAN, `--access
both`. Acrescentar `--href-local` faz o link do dashboard apontar pra LAN. O script cria os diretórios, grava o
`.env`, gera os secrets, ajusta o dono dos volumes, sobe o serviço e
imprime o endereço no fim — ver
[Instalando e operando](../../docs/pt-BR/instalacao.md) no README
raiz.

Acessar `http://<ip-do-host>:8101` (ou via [tsdproxy](../tsdproxy/README.pt-BR.md) em
`https://omni-tools.<your-tailnet>.ts.net`).

<details>
<summary><b>Instalação manual</b> (avançado) — os mesmos passos, um a um</summary>


```bash
# 1. Baixar a unit (sem precisar clonar o repositório)
mkdir -p ~/.config/containers/systemd
wget -P ~/.config/containers/systemd/ \
  https://raw.githubusercontent.com/wallacepnts/quadlet-homelab/main/apps/omni-tools/omni-tools.container

# 2. Subir — sem mkdir, sem secret, sem env
systemctl --user daemon-reload
systemctl --user start omni-tools
```

Acessar `http://<ip-do-host>:8101` (ou via [tsdproxy](../tsdproxy/README.pt-BR.md) em
`https://omni-tools.<your-tailnet>.ts.net`).

</details>

## Por que ele e não o IT-Tools

O [IT-Tools](https://github.com/CorentinTh/it-tools) é o projeto mais
conhecido dessa categoria, mas está parado: última release em outubro de
2024. O Omni Tools é a alternativa mantida, com a mesma proposta.

## Auto-update

Sem `AutoUpdate=` — tag explícita (`0.6.0`), bump manual (regra 9 do
convenções). Este é dos poucos onde ligar auto-update seria defensável:
não tem estado, não tem migração de banco, e o healthcheck HTTP cobre o
rollback. Ainda assim fica manual, por consistência (convenções, "Por
que a maioria está desligado").

## Backup & Recuperação

Nenhum. Não há estado — reinstalar é o "restore".

## Comandos úteis

```bash
systemctl --user status omni-tools
podman logs -f omni-tools
```

## Créditos

Deploy Quadlet baseado no
[Omni Tools](https://github.com/iib0011/omni-tools) de
[iib0011](https://github.com/iib0011) (MIT).
