# Uptime Kuma — Podman Quadlet (rootless)

**[🇬🇧 Read in English](./README.md)**

Deploy do [Uptime Kuma](https://github.com/louislam/uptime-kuma) (monitor
de disponibilidade self-hosted) via Podman Quadlet, usando a imagem
oficial `docker.io/louislam/uptime-kuma`.

## Arquitetura

Container único (Node + SQLite embutido) — um volume só (`/app/data`),
guarda banco, uploads e configuração.

**É o serviço mais endurecido do repositório**: aceitou o nível máximo
testado — `ReadOnly=true`, `DropCapability=ALL` (zero capabilities) e
`User=1000`, ou seja, o processo roda como não-root **dentro** do
container e cai num uid de subuid (100999) **no host**, fora do seu
próprio usuário. É o único desta faixa junto com beszel, paperless-ngx e
immich-machine-learning.

Consequência prática: o volume precisa pertencer a esse uid mapeado, e
isso se faz com `podman unshare chown` (passo 2 da instalação) — um
`chown` normal no host não serve, porque o número 1000 dentro do
namespace não é o 1000 de fora.

## Arquivos

```
uptime-kuma.container   # unit principal
```

## Pré-requisitos

- Podman rootless com systemd `--user` funcionando

## Instalação

```bash
python3 install.py uptime-kuma            # dry-run: mostra o que vai fazer
python3 install.py uptime-kuma --apply
```

Só na rede local, `--access local`; na tailnet e na LAN, `--access
both`. Acrescentar `--href-local` faz o link do dashboard apontar pra LAN. O script cria os diretórios, grava o
`.env`, gera os secrets, ajusta o dono dos volumes, sobe o serviço e
imprime o endereço no fim — ver
[Instalando e operando](../../docs/pt-BR/instalacao.md) no README
raiz.

Acessar `http://<ip-do-host>:3005` (ou via [tsdproxy](../tsdproxy/README.pt-BR.md) em
`https://uptime-kuma.<your-tailnet>.ts.net`) — a primeira tela cria a
conta de administrador. **Criar antes de expor**, a instalação fica
aberta até isso.

<details>
<summary><b>Instalação manual</b> (avançado) — os mesmos passos, um a um</summary>


```bash
# 1. Baixar as units (sem precisar clonar o repositório)
mkdir -p ~/.config/containers/systemd
wget -P ~/.config/containers/systemd/ \
  https://raw.githubusercontent.com/wallacepnts/quadlet-homelab/main/apps/uptime-kuma/uptime-kuma.container

# 2. Diretório de dados + dono correspondente ao User=1000 da unit.
#    `podman unshare` executa o chown DENTRO do user namespace, que é
#    onde o 1000 do container existe (no host isso vira 100999).
mkdir -p ~/.config/containers/volumes/uptime-kuma/data
podman unshare chown -R 1000:1000 ~/.config/containers/volumes/uptime-kuma/data

# 3. Subir
systemctl --user daemon-reload
systemctl --user start uptime-kuma
```

Acessar `http://<ip-do-host>:3005` (ou via [tsdproxy](../tsdproxy/README.pt-BR.md) em
`https://uptime-kuma.<your-tailnet>.ts.net`) — a primeira tela cria a
conta de administrador. **Criar antes de expor**, a instalação fica
aberta até isso.

</details>

## Monitorando os serviços deste repositório

Cada serviço aqui já publica uma porta no host e tem healthcheck próprio.
Dois jeitos de apontar o monitor:

- **HTTP(s)** em `http://<ip-do-host>:<porta>` — usa a porta publicada da
  tabela do [convenções](../../docs/pt-BR/convencoes.md). Funciona pra tudo que serve
  HTTP, e é o que dá tempo de resposta real.
- **HTTP(s)** na URL da tailnet (`https://<app>.<your-tailnet>.ts.net`) —
  testa o caminho completo, incluindo o [tsdproxy](../tsdproxy/README.pt-BR.md). Só
  funciona se o host do Uptime Kuma estiver na mesma tailnet (aqui está,
  é a mesma máquina).

Monitorar pela porta local detecta "o container caiu"; monitorar pela
URL da tailnet detecta também "o tsdproxy caiu" — vale ter os dois nos
serviços que importam.

## Auto-update

Sem `AutoUpdate=` — tag explícita (`2.5.0`), bump manual (regra 9 do
convenções). Aqui há um motivo extra: um monitor que se atualiza sozinho
e quebra é exatamente o que não avisa que quebrou.

## Backup & Recuperação

```bash
systemctl --user stop uptime-kuma
tar -czf uptime-kuma-backup-$(date +%Y%m%d-%H%M%S).tar.gz \
  -C ~/.config/containers/volumes uptime-kuma
systemctl --user start uptime-kuma
```

Restaurando em outra máquina, refazer o `podman unshare chown` do passo 2
depois de extrair — o tar preserva o uid antigo, que pode não ser o
mesmo mapeamento no destino.

## Comandos úteis

```bash
systemctl --user status uptime-kuma
podman logs -f uptime-kuma
podman exec uptime-kuma extra/healthcheck && echo OK
```

## Créditos

Deploy Quadlet baseado no
[Uptime Kuma](https://github.com/louislam/uptime-kuma) de
[louislam](https://github.com/louislam) (MIT).
