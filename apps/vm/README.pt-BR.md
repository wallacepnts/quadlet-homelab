# VM

<img src="https://cdn.jsdelivr.net/gh/homarr-labs/dashboard-icons/svg/qemu.svg" width="64" height="64" alt="">

**[🇺🇸 Read in English](./README.md)**

Windows, macOS, ChromeOS Flex, ZimaOS e 23 distros Linux como VMs em containers, vistas pelo navegador — exige KVM no host.

Para um shell onde instalar uma ferramenta, sem o custo de uma VM, veja o [toolbx](../toolbx/README.pt-BR.md). Para a interface do próprio Proxmox, o [proxmox](../proxmox/README.pt-BR.md).

## Primeiro acesso

Abrir `http://<ip-do-host>:3389` ou `https://chromeos.<your-tailnet>.ts.net`.

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
| <img src="https://cdn.jsdelivr.net/gh/homarr-labs/dashboard-icons/png/windows-11.png" width="28" height="28" alt=""> | [Windows](./docs/pt-BR/windows.md) | VM de Windows no navegador, com RDP para um desktop de verdade | `6.05` |
| <img src="https://cdn.jsdelivr.net/gh/homarr-labs/dashboard-icons/png/windows-11.png" width="28" height="28" alt=""> | [Windows on ARM](./docs/pt-BR/windows-arm.md) | O mesmo, para host ARM64. Compartilha as portas — só uma das duas roda | `6.05` |
| <img src="https://cdn.simpleicons.org/macos/888888" width="28" height="28" alt=""> | [macOS](./docs/pt-BR/macos.md) | VM de macOS, do Big Sur ao Sequoia | `3.12` |
| <img src="https://cdn.jsdelivr.net/gh/homarr-labs/dashboard-icons/svg/qemu.svg" width="28" height="28" alt=""> | [QEMU](./docs/pt-BR/qemu.md) | Qualquer um de vinte e três sistemas, escolhido na instalação | `7.50` |
| <img src="https://cdn.jsdelivr.net/gh/homarr-labs/dashboard-icons/svg/chrome.svg" width="28" height="28" alt=""> | [ChromeOS](./docs/pt-BR/chromeos.md) | ChromeOS Flex com a GPU do host | `1.05` |
| <img src="https://cdn.jsdelivr.net/gh/dockur/zima@master/assets/20241126-153324.png" width="28" height="28" alt=""> | [ZimaOS](./docs/pt-BR/zima.md) | A interface de NAS derivada do CasaOS, sem o hardware | `1.7.1` |

Cada página acima diz o que a VM pede no primeiro boot. Elas são independentes:
instalar a pasta traz as seis, e você sobe a que quiser.

## Remover

O nó da tailnet não é desregistrado ao remover um app: isso é no admin do Tailscale.

## Créditos

[qemus/qemu](https://github.com/qemus/qemu) — MIT

[Documentação oficial](https://github.com/dockur/windows#readme)
