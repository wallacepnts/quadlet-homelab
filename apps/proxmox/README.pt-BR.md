# Proxmox VE

<img src="https://cdn.jsdelivr.net/gh/homarr-labs/dashboard-icons/svg/proxmox.svg" width="64" height="64" alt="">

**[🇺🇸 Read in English](./README.md)**

O hypervisor Proxmox num container, pra experimentar sem dedicar uma máquina — roda privileged.

## Instalar

```bash
qh proxmox            # mostra o plano
qh proxmox --apply
```

Abrir `http://<ip-do-host>:8010` ou `https://proxmox.<your-tailnet>.ts.net`.

<details>
<summary><b>Instalação manual</b></summary>

```bash
# 1. Baixar a unit (sem precisar clonar o repositório)
mkdir -p ~/.config/containers/systemd
wget -P ~/.config/containers/systemd/ \
  https://raw.githubusercontent.com/wallacepnts/quadlet-homelab/main/apps/proxmox/proxmox.container

# 2. Diretórios
mkdir -p ~/.config/containers/volumes/proxmox/{data,config}

# 3. Secret — a senha de root da interface web
podman secret create proxmox-root-password - <<< "$(python3 -c 'import secrets,string;a=string.ascii_letters+string.digits;print("".join(secrets.choice(a) for _ in range(20)))')"

# 4. Subir
systemctl --user daemon-reload
systemctl --user start proxmox
```

</details>

## Arquivos

```
proxmox.container
install.ini
```

## Atualizar

```bash
qh proxmox --update --apply
```

Fixado em `9.2.9`. Nada atualiza sozinho — versão nova entra quando você
roda o comando acima.

## Backup

```bash
qh proxmox --backup --apply --out ~/backups
```

Ele para o serviço, empacota os dados, o `.env` e os secrets, e sobe de novo.
A frio de propósito: copiar banco vivo dá um arquivo que só falha na hora de
restaurar.

Pra restaurar, por cima dos dados atuais:

```bash
qh proxmox --restore ~/backups/proxmox-20260809-1200.tar.gz --apply
```

Ele pede que você digite `proxmox` pra confirmar, porque os dados atuais são
apagados antes de o arquivo ser extraído.

## Remover

```bash
qh proxmox --remove --apply           # para e tira, mantendo os dados
qh proxmox --remove --purge --apply   # e apaga volumes, secrets e .env
```

O `--purge` também pede o nome digitado. O nó da tailnet não é desregistrado
por isso — isso é no admin do Tailscale.

## Comandos

```bash
systemctl --user status proxmox
podman logs -f proxmox
```

## Créditos

[dockur/proxmox](https://github.com/dockur/proxmox) — MIT

[Documentação oficial](https://pve.proxmox.com/pve-docs/)
