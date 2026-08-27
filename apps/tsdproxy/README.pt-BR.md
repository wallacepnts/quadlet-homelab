# tsdproxy

<img src="https://cdn.jsdelivr.net/gh/selfhst/icons/svg/tsdproxy.svg" width="64" height="64" alt="">

**[🇺🇸 Read in English](./README.md)**

Publica containers na tailnet automaticamente, só com labels — sem configurar proxy manualmente por serviço.

## Instalar

```bash
qh tsdproxy            # mostra o plano
qh tsdproxy --apply
```

Abrir `http://<ip-do-host>:8080` ou `https://dash.<your-tailnet>.ts.net`.

<details>
<summary><b>Instalação manual</b></summary>

```bash
# 1. Baixar a unit (sem precisar clonar o repositório)
mkdir -p ~/.config/containers/systemd
wget -P ~/.config/containers/systemd/ \
  https://raw.githubusercontent.com/wallacepnts/quadlet-homelab/main/apps/tsdproxy/tsdproxy.container

# 2. Diretórios de dados — bind mount exige que já existam antes do start.
#    O tsdproxy não gera um config padrão sozinho, então config/tsdproxy.yaml
#    também precisa vir de algum lugar antes do primeiro start.
mkdir -p ~/.config/containers/volumes/tsdproxy/{data,config}
wget -O ~/.config/containers/volumes/tsdproxy/config/tsdproxy.yaml \
  https://raw.githubusercontent.com/wallacepnts/quadlet-homelab/main/apps/tsdproxy/config/tsdproxy.yaml
wget -O ~/.config/containers/volumes/tsdproxy/config/lists.yaml \
  https://raw.githubusercontent.com/wallacepnts/quadlet-homelab/main/apps/tsdproxy/config/lists.yaml
# editar lists.yaml: trocar <host-ip> pelo endereço desta máquina

# 3. Secret com a authkey do Tailscale
mkdir -p ~/.config/containers/secrets/tsdproxy
echo -n "SUA_AUTHKEY" > ~/.config/containers/secrets/tsdproxy/authkey.txt
chmod 600 ~/.config/containers/secrets/tsdproxy/authkey.txt
podman secret create authkey ~/.config/containers/secrets/tsdproxy/authkey.txt

# 4. Socket do Podman
systemctl --user enable --now podman.socket

# 5. Subir
systemctl --user daemon-reload
systemctl --user start tsdproxy
```

</details>

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

O arquivo já vem com o **Cockpit**, o console web que o openSUSE traz de fábrica
(`cockpit.socket` na 9090, mais o `cockpit-podman` se quiser os containers
listados lá também). Troque `<host-ip>` pelo endereço desta máquina e ele
atende em `https://cockpit.<your-tailnet>.ts.net`:

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

Se você não usa Cockpit, esvazie o arquivo: entrada apontando para porta
fechada publica um nome que responde 502.

## Atualizar

```bash
qh tsdproxy --update --apply
```

Fixado em `2`. Nada atualiza sozinho — versão nova entra quando você
roda o comando acima.

## Backup

```bash
qh tsdproxy --backup --apply --out ~/backups
```

Ele para o serviço, empacota os dados, o `.env` e os secrets, e sobe de novo.
A frio de propósito: copiar banco vivo dá um arquivo que só falha na hora de
restaurar.

Pra restaurar, por cima dos dados atuais:

```bash
qh tsdproxy --restore ~/backups/tsdproxy-20260809-1200.tar.gz --apply
```

Ele pede que você digite `tsdproxy` pra confirmar, porque os dados atuais são
apagados antes de o arquivo ser extraído.

## Remover

```bash
qh tsdproxy --remove --apply           # para e tira, mantendo os dados
qh tsdproxy --remove --purge --apply   # e apaga volumes, secrets e .env
```

O `--purge` também pede o nome digitado. O nó da tailnet não é desregistrado
por isso — isso é no admin do Tailscale.

## Comandos

```bash
systemctl --user status tsdproxy
podman logs -f tsdproxy
```

## Créditos

[almeidapaulopt/tsdproxy](https://github.com/almeidapaulopt/tsdproxy) — MIT

[Documentação oficial](https://almeidapaulopt.github.io/tsdproxy/)
