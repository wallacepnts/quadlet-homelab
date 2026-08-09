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
install.ini
```

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
