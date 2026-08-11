# Headscale

<img src="https://cdn.jsdelivr.net/gh/homarr-labs/dashboard-icons/svg/headscale.svg" width="64" height="64" alt="">

**[🇺🇸 Read in English](./README.md)**

Implementação aberta do control plane do Tailscale: a parte que distribui
chaves, decide quem fala com quem e responde o MagicDNS. Os mesmos clientes,
coordenados por um servidor seu em vez do de uma empresa.

É um servidor, não uma identidade de rede — e é por isso que aqui ele é
container enquanto o `tailscaled` continua instalado no host. Quem cria a
interface e fala WireGuard é o cliente; isto só conta pra ele quem mais existe.

## Instalação

```bash
qh headscale            # mostra o plano
qh headscale --apply
```

Depois edite o `~/.config/containers/volumes/headscale/config/config.yaml` — o
`server_url` tem que ser o endereço que os clientes vão alcançar, e tem que ser
HTTPS — e reinicie com `qh headscale --update --apply`.

Crie um usuário e uma chave, e aponte um cliente:

```bash
podman exec headscale headscale users create casa
podman exec headscale headscale preauthkeys create --user casa --expiration 24h

# na máquina cliente
sudo tailscale up --login-server https://headscale.casa --authkey <chave>
```

<details>
<summary><b>Instalação manual (avançado)</b></summary>

```bash
mkdir -p ~/.config/containers/systemd
mkdir -p ~/.config/containers/volumes/headscale/{config,data}

wget -P ~/.config/containers/systemd/ \
  https://raw.githubusercontent.com/wallacepnts/quadlet-homelab/main/apps/headscale/headscale.container
wget -O ~/.config/containers/volumes/headscale/config/config.yaml \
  https://raw.githubusercontent.com/wallacepnts/quadlet-homelab/main/apps/headscale/config/config.yaml

# O container roda como uid 1000, que não é o seu depois do mapeamento
podman unshare chown -R 1000:1000 ~/.config/containers/volumes/headscale

systemctl --user daemon-reload
systemctl --user start headscale
```

</details>

## Arquivos

```
headscale.container   unit
config/config.yaml    a configuração, para dentro do volume
install.ini
```

O `data/` guarda o `db.sqlite` e o `noise_private.key`. Essa chave é a
identidade do servidor: perdê-la faz todo cliente registrar de novo. O SQLite é
o padrão do próprio projeto, então não há um segundo container de banco.

## O que este repositório mudou na configuração

O arquivo é o exemplo do próprio headscale com quatro linhas diferentes, e elas
estão marcadas no topo dele:

- **`server_url`** — o endereço para onde os clientes apontam. Precisa ser
  alcançável de onde os seus dispositivos estiverem, e precisa ser HTTPS.
- **`listen_addr: 0.0.0.0:8080`** — o exemplo escuta em `127.0.0.1`, que dentro
  de um container significa que nada de fora conecta.
- **`metrics_listen_addr`** — mesmo motivo.
- **`base_domain: casa`** — o que o MagicDNS acrescenta, para um nó atender por
  `laptop.casa`.

As linhas de TLS ficam vazias de propósito: o [Caddy](../caddy/README.pt-BR.md)
termina na frente, e servidor atrás de proxy não deve fazer ACME próprio.

## A parte que não está neste repositório

Os clientes precisam alcançar o `server_url` **de qualquer lugar**, não só da
sua LAN. Isso significa endereço público e porta aberta, ou o headscale num
VPS. Sem isso, os dispositivos se coordenam em casa e em lugar nenhum mais, o
que joga fora quase todo o ganho.

Os relays são a outra metade: com `derp.server.enabled: false`, como vem, a
travessia de NAT cai nos servidores DERP públicos da Tailscale. Funciona e não
expõe tráfego em claro, mas ainda é infraestrutura deles. Ligar o DERP embutido
torna isso seu, e exige também uma porta UDP alcançável.

## Endurecimento

O ladder inteiro: `ReadOnly=true`, todas as capacidades descartadas e
`User=1000`. Medido com o servidor de fato respondendo — `/health` devolvendo
`{"status":"pass"}` e o banco gravado no volume.

O `/var/run/headscale` é tmpfs porque o headscale abre ali um socket unix para
o próprio CLI, e o sistema de arquivos raiz é somente-leitura.

## Atualizar

```bash
qh headscale --update --apply
```

Fixado em `v0.29.3`. Leia as notas da release antes de subir versão: esta é a
peça de que todo dispositivo depende para achar todos os outros.

## Backup

```bash
qh headscale --backup --apply --out ~/backups
```

Para o serviço, empacota o banco, a chave noise e a configuração, e sobe de
novo.

Pra restaurar, por cima dos dados atuais:

```bash
qh headscale --restore ~/backups/headscale-20260811-1200.tar.gz --apply
```

## Remover

```bash
qh headscale --remove --apply           # para e mantém a tailnet
qh headscale --remove --purge --apply   # e apaga o banco e a chave
```

O `--purge` encerra a tailnet: todo cliente teria que se registrar num servidor
novo.

## Comandos

```bash
systemctl --user status headscale
podman logs -f headscale

podman exec headscale headscale nodes list
podman exec headscale headscale users list
```

## Créditos

[juanfont/headscale](https://github.com/juanfont/headscale) — BSD-3-Clause.
Sem vínculo com a Tailscale Inc.

[Documentação oficial](https://headscale.net/)
