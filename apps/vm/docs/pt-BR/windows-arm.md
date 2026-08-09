# Windows on ARM

<img src="https://cdn.jsdelivr.net/gh/homarr-labs/dashboard-icons/png/windows-11.png" width="64" height="64" alt="">

**[🇺🇸 Read in English](../windows-arm.md)**

[< VMs](../../README.pt-BR.md)

O mesmo do `vm-windows`, para um host ARM64.

Visualizador web na **8006**, RDP na **3389**. Unit `vm-windows-arm`.

Use esta quando a máquina que roda o Podman for ARM — um Raspberry Pi 5, um servidor Ampere, um Apple Silicon com Linux. Em host x86, a que serve é a `vm-windows`.

Compartilha a 8006 e a 3389 com a `vm-windows`, e o `check.py` está instruído a permitir. Subir as duas juntas falha na porta, e é esse o resultado esperado: só uma das duas faz sentido numa mesma máquina.

Tem menos edições que a imagem x86, porque nem todo Windows foi compilado para ARM.

Todas precisam do `/dev/kvm` no host — sem virtualização por hardware a VM
não sobe ou fica lentíssima. O `RAM_SIZE` é reservado por toda a vida da VM,
então deixe o host respirar; o `DISK_SIZE` é um teto e cresce conforme o uso.

## Comandos

```bash
systemctl --user status vm-windows-arm
podman logs -f vm-windows-arm
qh vm-windows-arm --update --apply
```

## Créditos

[Windows on ARM](https://github.com/dockur/windows-arm) — MIT

[Documentação oficial](https://github.com/dockur/windows-arm#readme)
