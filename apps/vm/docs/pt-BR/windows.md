# Windows

<img src="https://cdn.jsdelivr.net/gh/homarr-labs/dashboard-icons/png/windows-11.png" width="64" height="64" alt="">

**[🇺🇸 Read in English](../windows.md)**

[< VMs](../../README.pt-BR.md)

Uma VM de Windows que você abre no navegador. Nada é instalado no host.

Visualizador web na **8006**, RDP na **3389**. Unit `vm-windows`.

A instalação pergunta qual Windows colocar — dezenove opções, do Windows 11 Pro ao XP, ao ReactOS e às versões enxutas Tiny11. A imagem é baixada dos servidores da própria Microsoft no primeiro boot e demora; o visualizador no navegador mostra a instalação inteira.

Mudar o `VERSION` depois não faz nada: o disco já foi escrito. Para trocar, remova o volume e comece de novo.

A conta dentro do Windows é `Docker`, e a senha dela é um segredo gerado — a instalação mostra. É a que o RDP na 3389 pede; o visualizador no navegador não pede nada.

O `vm-windows-arm` publica as mesmas portas de propósito. São alternativas — uma para host x86, outra para ARM — e só uma roda por vez.

Todas precisam do `/dev/kvm` no host — sem virtualização por hardware a VM
não sobe ou fica lentíssima. O `RAM_SIZE` é reservado por toda a vida da VM,
então deixe o host respirar; o `DISK_SIZE` é um teto e cresce conforme o uso.

## Comandos

```bash
systemctl --user status vm-windows
podman logs -f vm-windows
qh vm-windows --update --apply
```

## Créditos

[Windows](https://github.com/dockur/windows) — MIT

[Documentação oficial](https://github.com/dockur/windows#readme)
