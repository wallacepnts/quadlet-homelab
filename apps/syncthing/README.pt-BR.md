# Syncthing

<img src="https://cdn.jsdelivr.net/gh/homarr-labs/dashboard-icons/svg/syncthing.svg" width="64" height="64" alt="">

**[🇺🇸 Read in English](./README.md)**

Sincronização de arquivos P2P entre dispositivos, sem servidor central.

## Instalar

```bash
qh syncthing            # mostra o plano
qh syncthing --apply
```

Abrir `http://<ip-do-host>:8384` ou `https://syncthing.<your-tailnet>.ts.net`.

<details>
<summary><b>Instalação manual</b></summary>

```bash
# 1. Baixar a unit (sem precisar clonar o repositório)
mkdir -p ~/.config/containers/systemd
wget -P ~/.config/containers/systemd/ \
  https://raw.githubusercontent.com/wallacepnts/quadlet-homelab/main/apps/syncthing/syncthing.container

# 2. Diretório de dados — bind mount exige que já exista antes do start
mkdir -p ~/.config/containers/volumes/syncthing/data
podman unshare chown -R 1000:1000 ~/.config/containers/volumes/syncthing   # a unit usa User=1000

# 3. Env não-secreto — baixar o exemplo, ajustar PUID/PGID pro usuário
#    que roda o Podman (mesmo dono do volume acima)
mkdir -p ~/.config/containers/env
wget -O ~/.config/containers/env/syncthing.env \
  https://raw.githubusercontent.com/wallacepnts/quadlet-homelab/main/apps/syncthing/.env.example
sed -i "s/^PUID=.*/PUID=$(id -u)/;s/^PGID=.*/PGID=$(id -g)/" \
  ~/.config/containers/env/syncthing.env

# 4. Subir
systemctl --user daemon-reload
systemctl --user start syncthing
```

</details>

## Arquivos

```
syncthing.container
.env.example
```

## Atualizar

```bash
qh syncthing --update --apply
```

Fixado em `2.1.3`. Nada atualiza sozinho — versão nova entra quando você
roda o comando acima.

## Backup

```bash
qh syncthing --backup --apply --out ~/backups
```

Ele para o serviço, empacota os dados, o `.env` e os secrets, e sobe de novo.
A frio de propósito: copiar banco vivo dá um arquivo que só falha na hora de
restaurar.

Pra restaurar, por cima dos dados atuais:

```bash
qh syncthing --restore ~/backups/syncthing-20260809-1200.tar.gz --apply
```

Ele pede que você digite `syncthing` pra confirmar, porque os dados atuais são
apagados antes de o arquivo ser extraído.

## Remover

```bash
qh syncthing --remove --apply           # para e tira, mantendo os dados
qh syncthing --remove --purge --apply   # e apaga volumes, secrets e .env
```

O `--purge` também pede o nome digitado. O nó da tailnet não é desregistrado
por isso — isso é no admin do Tailscale.

## Comandos

```bash
systemctl --user status syncthing
podman logs -f syncthing
```

## Créditos

[syncthing/syncthing](https://github.com/syncthing/syncthing) — MPL-2.0.

[Documentação oficial](https://syncthing.net/)
