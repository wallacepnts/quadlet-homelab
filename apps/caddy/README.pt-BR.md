# Caddy

<img src="https://cdn.jsdelivr.net/gh/homarr-labs/dashboard-icons/svg/caddy.svg" width="64" height="64" alt="">

**[🇺🇸 Read in English](./README.md)**

Proxy reverso que dá HTTPS aos seus serviços em nomes escolhidos por você,
assinados por uma autoridade certificadora que ele mesmo roda. Sem domínio para
comprar, sem Let's Encrypt, sem nada publicado na internet.

É a alternativa ao [tsdproxy](../tsdproxy/README.pt-BR.md) para quem prefere
ter a corrente inteira: uma autoridade aqui, um certificado por nome, e nenhum
control plane decidindo se você recebe um.

## Instalação

```bash
qh caddy            # mostra o plano
qh caddy --apply
```

Depois acrescente uma rota por serviço no
`~/.config/containers/volumes/caddy/config/Caddyfile` e recarregue:

```
faved.casa {
	reverse_proxy faved:80
}
```

```bash
podman exec caddy caddy reload --config /etc/caddy/Caddyfile
```

<details>
<summary><b>Instalação manual (avançado)</b></summary>

```bash
mkdir -p ~/.config/containers/systemd
mkdir -p ~/.config/containers/volumes/caddy/{config,data,state}

wget -P ~/.config/containers/systemd/ \
  https://raw.githubusercontent.com/wallacepnts/quadlet-homelab/main/apps/caddy/caddy.container
wget -O ~/.config/containers/volumes/caddy/config/Caddyfile \
  https://raw.githubusercontent.com/wallacepnts/quadlet-homelab/main/apps/caddy/config/Caddyfile

systemctl --user daemon-reload
systemctl --user start caddy
```

</details>

## Arquivos

```
caddy.container    unit
config/Caddyfile   as rotas, para dentro do volume
install.ini
```

O `data/` guarda a autoridade certificadora e os certificados que ela emite — é
a pasta de fazer backup, porque perdê-la significa fazer todo dispositivo
confiar numa CA nova. O `state/` é a contabilidade interna do Caddy.

## As duas coisas que não são automáticas

**Cada dispositivo precisa confiar na CA, uma vez.** É esse o preço de não ter
domínio. O certificado raiz fica em
`~/.config/containers/volumes/caddy/data/caddy/pki/authorities/local/root.crt`:

```bash
# openSUSE
sudo cp root.crt /etc/pki/trust/anchors/caddy-local.crt && sudo update-ca-certificates
```

No Android e no iOS a instalação é pelas configurações, e no iOS ainda precisa
ser habilitado em **Ajustes de confiança de certificado** — duas telas
diferentes.

**Os nomes precisam resolver.** Nada sabe o que é `faved.casa`. Ou uma entrada
por dispositivo no `/etc/hosts`, ou um resolvedor que todos já usam — o
[adguardhome](../adguardhome/README.pt-BR.md) deste repositório responde
`*.casa` com o endereço do host, e a tailnet pode ser apontada para ele como
DNS dividido.

## Portas

O Podman rootless recusa publicar porta abaixo de 1024, então a unit publica
**8443** e **8114**, e as URLs carregam a porta. Para tirá-la, baixe o piso no
host uma vez e troque as duas linhas `PublishPort` por `443:443` e `80:80`:

```bash
echo 'net.ipv4.ip_unprivileged_port_start=80' | sudo tee /etc/sysctl.d/50-unprivileged-ports.conf
sudo sysctl --system
```

## Endurecimento

`ReadOnly=true` com todas as capacidades descartadas menos a
`NET_BIND_SERVICE`, de que ele precisa por escutar na 443 **dentro** do
container. Medido servindo uma requisição real até outro container.

Um erro aparece no log e é inofensivo:

```
pki.ca.local  failed to install root certificate
```

O Caddy tenta acrescentar a própria CA ao trust store do container e não
consegue, porque não tem capacidade para escrever ali. O certificado que ele
serve é o mesmo de qualquer forma — e container que não reescreve o próprio
trust store é o comportamento desejado.

## Atualizar

```bash
qh caddy --update --apply
```

Fixado em `2.11.4-alpine`.

## Backup

```bash
qh caddy --backup --apply --out ~/backups
```

A pasta que importa é a `data/`: é ela que carrega a CA. Restaurá-la faz os
dispositivos que já confiam em você continuarem confiando.

## Remover

```bash
qh caddy --remove --apply           # para e mantém a CA
qh caddy --remove --purge --apply   # e apaga a CA e todos os certificados
```

O `--purge` invalida todo dispositivo que confia na CA atual.

## Comandos

```bash
systemctl --user status caddy
podman logs -f caddy

podman exec caddy caddy validate --config /etc/caddy/Caddyfile
podman exec caddy caddy reload --config /etc/caddy/Caddyfile
```

## Créditos

[caddyserver/caddy](https://github.com/caddyserver/caddy) — Apache-2.0.

[Documentação oficial](https://caddyserver.com/docs/)
