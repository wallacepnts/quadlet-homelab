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
| **Caddy** | HTTPS para `*.qh`, assinado por uma CA que ele mesmo roda |
| **AdGuard Home** | responde `*.qh` com o endereço do host |

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

- `server_url: https://headscale.qh` — o control plane
- `base_domain: rede.qh` — o que o MagicDNS acrescenta, então um notebook
  atende por `laptop.rede.qh`

## 3. Rotas no Caddy

No `~/.config/containers/volumes/caddy/config/Caddyfile`:

```
headscale.qh {
	reverse_proxy headscale:8080
}

headplane.qh {
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
não for configurado. Faça pelo navegador, em
`https://adguardhome.<your-tailnet>.ts.net` ou `http://<ip-do-host>:3006`, com
duas respostas em mente: a interface de administrador fica na porta **3000**, e
o servidor DNS na **53**. São as portas que a unit mapeia.

Depois uma reescrita, em **Filters → DNS rewrites**, manda todo nome para o
host:

| Domínio | Resposta |
| --- | --- |
| `*.qh` | o endereço do host na tailnet |
| `qh` | o mesmo |

O curinga é o ponto: um serviço acrescentado mês que vem resolve sem tocar em
DNS de novo. Só o Caddy precisa de rota nova.

### Em que endereço ele escuta

Não em `0.0.0.0`. Esse endereço inclui o gateway da rede dos containers, onde o
`aardvark-dns` responde, e publicar por cima derruba a resolução de nomes
*entre todos os containers do host* — medido aqui, e quebrou de uma vez
`zerobyte → ntfy`, `caddy → headscale` e o resto.

Então a unit fixa um endereço, e o pega do `environment.d` (regra 19 das
convenções), do mesmo jeito que o `${TAILNET}` funciona:

```bash
echo 'AGH_DNS_BIND=100.x.y.z' > ~/.config/environment.d/adguardhome.conf
systemctl --user set-environment AGH_DNS_BIND=100.x.y.z
qh adguardhome --update --apply
```

Escutar na porta 53 exige o sysctl do passo anterior. Sem ele, deixe a unit na
`5335` e use o atalho do `/etc/hosts` abaixo.

### Entregando o resolvedor a todo dispositivo

Uma configuração no admin do Tailscale, e todo dispositivo da tailnet passa a
resolver `.qh` — celular incluído:

1. **DNS → Nameservers → Add nameserver → Custom**
2. endereço: o do host na tailnet, o mesmo do `AGH_DNS_BIND`
3. marque **Restrict to domain** e ponha `qh`

DNS dividido: só o `.qh` vai para o AdGuard, o resto continua como estava. É
isso que torna a montagem usável do celular, e é o motivo de o AdGuard fixar um
endereço da tailnet e não um da LAN.

Conferindo:

```bash
dig +short @100.x.y.z karakeep.qh
```

### O atalho de uma máquina só

Enquanto o DNS dividido não está posto, o `/etc/hosts` faz o mesmo para um
computador:

```bash
echo "100.x.y.z karakeep.qh homepage.qh" | sudo tee -a /etc/hosts
```

Apague depois. Um `/etc/hosts` parcial vence o DNS, o que dá o pior resultado:
três serviços resolvendo e o resto não, sem motivo visível.

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

sudo tailscale up --login-server https://headscale.qh:8443 --authkey <chave>
```

A porta está na URL porque o Caddy publica na 8443, pelo mesmo motivo que o
AdGuard publica na 5335. Com o sysctl acima e `443:443` na unit, vira
`https://headscale.qh`.

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
dig @127.0.0.1 -p 5335 headscale.qh   ->  100.x.y.z
https://headscale.qh:8443/health      ->  {"status":"pass"}
https://headplane.qh:8443/admin/      ->  302
```
