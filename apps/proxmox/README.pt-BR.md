# Proxmox VE

<img src="https://cdn.jsdelivr.net/gh/homarr-labs/dashboard-icons/svg/proxmox.svg" width="64" height="64" alt="">

**[🇺🇸 Read in English](./README.md)**

O hypervisor Proxmox num container, pra experimentar sem dedicar uma máquina — roda privileged.

É a interface, não um hypervisor com KVM por trás: para rodar um convidado de verdade aqui, veja o [vm](../vm/README.pt-BR.md).

## Primeiro acesso

Abrir `http://<ip-do-host>:8010` ou `https://proxmox.<your-tailnet>.ts.net`.

## Arquivos

```
proxmox.container
install.ini
```

## Remover

O nó da tailnet não é desregistrado ao remover um app: isso é no admin do Tailscale.

## Créditos

[dockur/proxmox](https://github.com/dockur/proxmox) — MIT

[Documentação oficial](https://pve.proxmox.com/pve-docs/)
