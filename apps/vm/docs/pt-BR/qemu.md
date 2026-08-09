# QEMU

<img src="https://cdn.jsdelivr.net/gh/homarr-labs/dashboard-icons/svg/qemu.svg" width="64" height="64" alt="">

**[🇺🇸 Read in English](../qemu.md)**

[< VMs](../../README.pt-BR.md)

Qualquer sistema operacional numa VM, escolhido na instalação.

Visualizador web na **8007**. Unit `vm-qemu`.

A instalação lista vinte e três sistemas, do Alpine com 60 MB ao CentOS com 7 GB. A ISO é baixada no primeiro boot e o instalador roda no visualizador.

O Alpine é o jeito rápido de provar que o KVM funciona no host antes de gastar um download maior nisso.

Esta é a de uso geral: sem senha, sem RDP, sem integração. Ela dá boot numa ISO e te mostra a tela.

Todas precisam do `/dev/kvm` no host — sem virtualização por hardware a VM
não sobe ou fica lentíssima. O `RAM_SIZE` é reservado por toda a vida da VM,
então deixe o host respirar; o `DISK_SIZE` é um teto e cresce conforme o uso.

## Comandos

```bash
systemctl --user status vm-qemu
podman logs -f vm-qemu
qh vm-qemu --update --apply
```

## Créditos

[QEMU](https://github.com/qemus/qemu) — MIT

[Documentação oficial](https://github.com/qemus/qemu#readme)
