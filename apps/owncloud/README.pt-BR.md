# ownCloud

<img src="https://cdn.jsdelivr.net/gh/homarr-labs/dashboard-icons/svg/owncloud.svg" width="64" height="64" alt="">

**[🇺🇸 Read in English](./README.md)**

Sincronização e compartilhamento de arquivos em nuvem própria.

## Instalar

```bash
qh owncloud            # mostra o plano
qh owncloud --apply
```

Abrir `http://<ip-do-host>:8094` ou `https://owncloud.<your-tailnet>.ts.net`.

<details>
<summary><b>Instalação manual</b></summary>

```bash
# 1. Baixar a unit (sem precisar clonar o repositório)
mkdir -p ~/.config/containers/systemd
wget -P ~/.config/containers/systemd/ \
  https://raw.githubusercontent.com/wallacepnts/quadlet-homelab/main/apps/owncloud/owncloud.container

# 2. Diretório de dados — bind mount exige que já exista antes do start
mkdir -p ~/.config/containers/volumes/owncloud/data

# 3. Secret — senha do admin (criado no primeiro start)
mkdir -p ~/.config/containers/secrets/owncloud
openssl rand -base64 18 | tr -d '\n' > ~/.config/containers/secrets/owncloud/admin-password.txt
chmod 600 ~/.config/containers/secrets/owncloud/admin-password.txt
podman secret create owncloud-admin-password ~/.config/containers/secrets/owncloud/admin-password.txt

# 4. Env não-secreto — baixar o exemplo e editar OWNCLOUD_DOMAIN/
#    OWNCLOUD_TRUSTED_DOMAINS com seu domínio da tailnet
mkdir -p ~/.config/containers/env
wget -O ~/.config/containers/env/owncloud.env \
  https://raw.githubusercontent.com/wallacepnts/quadlet-homelab/main/apps/owncloud/.env.example
# editar ~/.config/containers/env/owncloud.env

# 5. Subir
systemctl --user daemon-reload
systemctl --user start owncloud
```

</details>

## Arquivos

```
owncloud.container
.env.example
install.ini
```

## Atualizar

```bash
qh owncloud --update --apply
```

Fixado em `11.0.0-20260802`. Nada atualiza sozinho — versão nova entra quando você
roda o comando acima.

## Backup

```bash
qh owncloud --backup --apply --out ~/backups
```

Ele para o serviço, empacota os dados, o `.env` e os secrets, e sobe de novo.
A frio de propósito: copiar banco vivo dá um arquivo que só falha na hora de
restaurar.

Pra restaurar, por cima dos dados atuais:

```bash
qh owncloud --restore ~/backups/owncloud-20260809-1200.tar.gz --apply
```

Ele pede que você digite `owncloud` pra confirmar, porque os dados atuais são
apagados antes de o arquivo ser extraído.

## Remover

```bash
qh owncloud --remove --apply           # para e tira, mantendo os dados
qh owncloud --remove --purge --apply   # e apaga volumes, secrets e .env
```

O `--purge` também pede o nome digitado. O nó da tailnet não é desregistrado
por isso — isso é no admin do Tailscale.

## Comandos

```bash
systemctl --user status owncloud
podman logs -f owncloud
```

## Créditos

[owncloud/core](https://github.com/owncloud/core) — AGPL-3.0.

[Documentação oficial](https://owncloud.com)
