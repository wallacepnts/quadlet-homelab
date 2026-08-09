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
vm-<nome>.container       uma unit por VM, seis delas
vm-<nome>.env.example     RAM, núcleos e disco, um por VM
install.ini               as senhas, e quais sistemas a instalação oferece
docs/                     uma página por VM
```

Discos em `~/.config/containers/volumes/vm/<nome>/`. As portas de cada VM estão
na página dela.

| | VM | Para que serve | Versão |
| --- | --- | --- | --- |
| <img src="https://cdn.jsdelivr.net/gh/homarr-labs/dashboard-icons/png/windows-11.png" width="28" height="28" alt=""> | [Windows](./docs/pt-BR/windows.md) | VM de Windows no navegador, com RDP para um desktop de verdade | `6.04` |
| <img src="https://cdn.jsdelivr.net/gh/homarr-labs/dashboard-icons/png/windows-11.png" width="28" height="28" alt=""> | [Windows on ARM](./docs/pt-BR/windows-arm.md) | O mesmo, para host ARM64. Compartilha as portas — só uma das duas roda | `6.04` |
| <img src="https://cdn.simpleicons.org/macos/888888" width="28" height="28" alt=""> | [macOS](./docs/pt-BR/macos.md) | VM de macOS, do Big Sur ao Sequoia | `3.09` |
| <img src="https://cdn.jsdelivr.net/gh/homarr-labs/dashboard-icons/svg/qemu.svg" width="28" height="28" alt=""> | [QEMU](./docs/pt-BR/qemu.md) | Qualquer um de vinte e três sistemas, escolhido na instalação | `7.44` |
| <img src="https://cdn.jsdelivr.net/gh/homarr-labs/dashboard-icons/svg/chrome.svg" width="28" height="28" alt=""> | [ChromeOS](./docs/pt-BR/chromeos.md) | ChromeOS Flex com a GPU do host | `1.02` |
| <img src="https://cdn.jsdelivr.net/gh/dockur/zima@master/assets/20241126-153324.png" width="28" height="28" alt=""> | [ZimaOS](./docs/pt-BR/zima.md) | A interface de NAS derivada do CasaOS, sem o hardware | `1.7.0` |

Cada página acima diz o que a VM pede no primeiro boot. Elas são independentes:
instalar a pasta traz as seis, e você sobe a que quiser.

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
