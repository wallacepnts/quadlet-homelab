# tsdproxy

<img src="https://cdn.jsdelivr.net/gh/selfhst/icons/svg/tsdproxy.svg" width="64" height="64" alt="">

**[🇺🇸 Read in English](./README.md)**

Publica containers na tailnet automaticamente, só com labels — sem configurar proxy manualmente por serviço.

## Primeiro acesso

Abrir `http://<ip-do-host>:8080` ou `https://dash.<your-tailnet>.ts.net`.

## Arquivos

```
tsdproxy.container
config/tsdproxy.yaml   a configuração do próprio proxy
config/lists.yaml      serviços que não são container
install.ini
```

## Publicar algo que não é container

Container é descoberto pelas labels. Os serviços do próprio host não têm
label nenhuma, então vão no `config/lists.yaml` — uma entrada por nome, e o
tsdproxy relê esse arquivo sem reiniciar.

O arquivo traz o **Cockpit**, o console web que o openSUSE tem de fábrica
(`cockpit.socket` na 9090, mais o `cockpit-podman` se quiser os containers
listados lá também), comentado. Descomente, troque `<host-ip>` pelo endereço
desta máquina, e ele atende em `https://cockpit.<your-tailnet>.ts.net`:

```yaml
cockpit:
  ports:
    443/https:
      targets:
        - https://<host-ip>:9090
```

Dois detalhes que não são óbvios:

- O endereço tem que ser **real**. O `host.containers.internal` só responde na
  rede default do Podman, e o tsdproxy vive na `tsdproxy-net` — de lá ele dá
  timeout. O endereço tailscale é o mais estável, porque não muda com DHCP.
- O alvo é `https://`, não `http://` — o Cockpit serve TLS por conta própria na
  9090. Com o esquema certo a checagem de origem dele passa como está, sem
  precisar de `/etc/cockpit/cockpit.conf`; com o errado a tela de login abre
  mas a sessão nunca sobe.

O Cockpit é o serviço do host que vale essa entrada: disco, rede, journal e as
atualizações do próprio sistema, nada disso um container mostra. Criar
container *por ele* é outra história — uma unit `--replace --rm` volta assim
que o Cockpit a para, e o que for criado na mão fica invisível para este
repositório. Ler, não escrever.

Por isso a entrada vem comentada: apontando para porta fechada, ela publica
um nome que responde 502 — e a maioria dos hosts não roda Cockpit.

## Remover

O nó da tailnet não é desregistrado ao remover um app: isso é no admin do Tailscale.

## Créditos

[almeidapaulopt/tsdproxy](https://github.com/almeidapaulopt/tsdproxy) — MIT

[Documentação oficial](https://almeidapaulopt.github.io/tsdproxy/)
