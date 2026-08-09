# VM

<img src="https://cdn.jsdelivr.net/gh/homarr-labs/dashboard-icons/svg/qemu.svg" width="64" height="64" alt="">

**[🇺🇸 Read in English](./README.md)**

Windows, macOS, ChromeOS Flex, ZimaOS e 23 distros Linux como VMs em containers, vistas pelo navegador — exige KVM no host.

## Instalar

```bash
qh vm            # mostra o plano
qh vm --apply
```

Abrir `http://<ip-do-host>:3389` ou `https://chromeos.<your-tailnet>.ts.net`.

<details>
<summary><b>Instalação manual</b></summary>

```bash
# 1. Baixar a unit que você quer (sem precisar clonar o repositório)
mkdir -p ~/.config/containers/systemd/vm
wget -P ~/.config/containers/systemd/vm/ \
  https://raw.githubusercontent.com/wallacepnts/quadlet-homelab/main/apps/vm/vm-qemu.container

# 2. Diretórios
mkdir -p ~/.config/containers/volumes/vm/qemu/storage
mkdir -p ~/.config/containers/env

# 3. Ambiente
wget -O ~/.config/containers/env/vm-qemu.env \
  https://raw.githubusercontent.com/wallacepnts/quadlet-homelab/main/apps/vm/vm-qemu.env.example

# 4. Só pro Windows — a senha de RDP da conta `Docker`
podman secret create vm-windows-password - <<< "$(python3 -c 'import secrets,string;a=string.ascii_letters+string.digits;print("".join(secrets.choice(a) for _ in range(20)))')"

# 5. Subir
systemctl --user daemon-reload
systemctl --user start vm-qemu
```

</details>

## Arquivos

```
vm-chromeos.container
vm-macos.container
vm-qemu.container
vm-windows-arm.container
vm-windows.container
vm-zima.container
vm-chromeos.env.example
vm-macos.env.example
vm-qemu.env.example
vm-windows-arm.env.example
vm-windows.env.example
vm-zima.env.example
install.ini
```

Units da stack:

- `vm-chromeos`
- `vm-macos`
- `vm-qemu`
- `vm-windows-arm`
- `vm-windows`
- `vm-zima`

## Atualizar

```bash
qh vm --update --apply
```

Fixado em `1.02`, `1.7.0`, `3.09`. Nada atualiza sozinho — versão nova entra quando você
roda o comando acima.

## Backup

```bash
qh vm --backup --apply --out ~/backups
```

Ele para o serviço, empacota os dados, o `.env` e os secrets, e sobe de novo.
A frio de propósito: copiar banco vivo dá um arquivo que só falha na hora de
restaurar.

Pra restaurar, por cima dos dados atuais:

```bash
qh vm --restore ~/backups/vm-20260809-1200.tar.gz --apply
```

Ele pede que você digite `vm` pra confirmar, porque os dados atuais são
apagados antes de o arquivo ser extraído.

## Remover

```bash
qh vm --remove --apply           # para e tira, mantendo os dados
qh vm --remove --purge --apply   # e apaga volumes, secrets e .env
```

O `--purge` também pede o nome digitado. O nó da tailnet não é desregistrado
por isso — isso é no admin do Tailscale.

## Comandos

```bash
systemctl --user status vm
podman logs -f vm
```

## Créditos

[qemus/qemu](https://github.com/qemus/qemu) — MIT

[Documentação oficial](https://github.com/dockur/windows#readme)
