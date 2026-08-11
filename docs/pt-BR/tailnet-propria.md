# Uma tailnet sua

Trocando o control plane da Tailscale pelo [headscale](../../apps/headscale/README.pt-BR.md),
a interface dele pelo [headplane](../../apps/headplane/README.pt-BR.md), e os
certificados pelo [Caddy](../../apps/caddy/README.pt-BR.md) assinando nomes que
o [AdGuard Home](../../apps/adguardhome/README.pt-BR.md) resolve.

Nada aqui toca no Tailscale que você já roda. Os quatro serviços sobem ao lado
dele, e você troca os clientes quando estiver convencido — ou nunca.

## Para que serve cada peça

| | |
| --- | --- |
| **headscale** | distribui chaves, decide quem fala com quem, responde o MagicDNS |
| **headplane** | a tela do de cima |
| **Caddy** | HTTPS para `*.casa`, assinado por uma CA que ele mesmo roda |
| **AdGuard Home** | responde `*.casa` com o endereço do host |

Os dois últimos existem por um motivo só: sem um domínio seu, ninguém emite
certificado público pra você, e nada resolve um nome que você inventou.

## 1. Os serviços

A ordem importa — o headplane monta a configuração do headscale, e bind mount
de diretório inexistente falha:

```bash
qh headscale --apply
qh headplane --apply
qh caddy --apply
qh adguardhome --apply
```

## 2. Dois espaços de nome, não um

O headscale recusa subir quando o `server_url` está dentro do `base_domain`:

```
server_url cannot be part of base_domain in a way that could make the
DERP and headscale server unreachable
```

Um nó chamado `headscale` sombrearia o servidor. Então eles ficam separados, e
é isso que o `config.yaml` publicado usa:

- `server_url: https://headscale.casa` — o control plane
- `base_domain: rede.casa` — o que o MagicDNS acrescenta, então um notebook
  atende por `laptop.rede.casa`

## 3. Rotas no Caddy

No `~/.config/containers/volumes/caddy/config/Caddyfile`:

```
headscale.casa {
	reverse_proxy headscale:8080
}

headplane.casa {
	reverse_proxy headplane:3000
}
```

```bash
podman exec caddy caddy reload --config /etc/caddy/Caddyfile
```

Nome de container, não endereço: todo mundo divide a `tsdproxy-net`, então o
Caddy alcança cada serviço pelo nome sem nada publicado na LAN.

## 4. O AdGuard responde os nomes

O primeiro start serve só o assistente — o servidor DNS não sobe enquanto ele
não for configurado. Pela API dele, de um container na mesma rede:

```bash
curl -X POST http://adguardhome:3000/control/install/configure \
  -H 'Content-Type: application/json' \
  -d '{"web":{"ip":"0.0.0.0","port":3000},"dns":{"ip":"0.0.0.0","port":53},
       "username":"admin","password":"<a sua>"}'
```

Depois uma reescrita manda todo nome `.casa` para o host:

```bash
curl -u admin:<a sua> -X POST http://adguardhome:3000/control/rewrite/add \
  -H 'Content-Type: application/json' \
  -d '{"domain":"*.casa","answer":"<ip tailscale do host>"}'
```

Conferindo:

```bash
dig +short @127.0.0.1 -p 5335 headscale.casa
```

**A porta é a pegadinha.** O Podman rootless não abre a 53, então o AdGuard
escuta na **5335**, e as configurações de DNS do Tailscale aceitam endereço sem
porta. Até resolver isso, a resolução funciona para quem apontar explicitamente
na 5335 — o que basta para testar, e não basta para celular. Duas saídas: baixar
o piso no host, uma vez,

```bash
echo 'net.ipv4.ip_unprivileged_port_start=53' | sudo tee /etc/sysctl.d/50-unprivileged-ports.conf
sudo sysctl --system
```

e publicar `53:53`; ou dispensar o AdGuard para os nomes e pô-los no
`dns.extra_records` do próprio headscale, que os clientes dele recebem sem
resolvedor no meio.

## 5. Confiar na autoridade certificadora

Todo dispositivo que for abrir esses nomes precisa confiar na CA do Caddy, uma
vez:

```bash
find ~/.config/containers/volumes/caddy/data -name root.crt
# openSUSE
sudo cp <esse arquivo> /etc/pki/trust/anchors/caddy-local.crt
sudo update-ca-certificates
```

Isso inclui a máquina que roda o `tailscale`: o cliente valida o TLS contra o
control plane, então sem a CA ele não entra.

## 6. Um cliente

```bash
podman exec headscale /ko-app/headscale users create casa
podman exec headscale /ko-app/headscale preauthkeys create --user casa --expiration 24h

sudo tailscale up --login-server https://headscale.casa:8443 --authkey <chave>
```

A porta está na URL porque o Caddy publica na 8443, pelo mesmo motivo que o
AdGuard publica na 5335. Com o sysctl acima e `443:443` na unit, vira
`https://headscale.casa`.

O `headscale apikeys create --expiration 90d` dá a chave que o headplane pede
na entrada.

## O que ainda falta para sair de casa

Tudo acima funciona na sua rede. Para um aparelho no 4G alcançar o
`server_url`, é preciso endereço público e porta aberta, ou o headscale num
VPS. Sem isso, a tailnet se coordena em casa e em lugar nenhum mais.

Os relays são a outra metade: com `derp.server.enabled: false`, como vem, a
travessia de NAT cai nos servidores DERP públicos da Tailscale — infraestrutura
deles, sem tráfego em claro. O DERP embutido torna isso seu, e pede uma porta
UDP alcançável.

## Verificado

Medido no host em que isto foi escrito, com os quatro serviços saudáveis:

```
dig @127.0.0.1 -p 5335 headscale.casa   ->  100.x.y.z
https://headscale.casa:8443/health      ->  {"status":"pass"}
https://headplane.casa:8443/admin/      ->  302
```
