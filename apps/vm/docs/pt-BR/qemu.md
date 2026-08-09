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

## Instalação

```bash
qh vm-qemu
qh vm-qemu --apply
```

Instalar a pasta — `qh vm --apply` — traz esta junto com as outras.

## Sistemas

A instalação pergunta e grava a resposta no `.env`. Só vale no primeiro boot:
a imagem é baixada uma vez, e mudar o valor depois não faz nada num disco já
escrito.

`BOOT` — Qual sistema instalar (baixado no primeiro boot).

| | Valor | O que é |
| --- | --- | --- |
| <img src="https://cdn.simpleicons.org/alpinelinux" width="20" height="20" alt=""> | `alpine` | Alpine Linux — 60 MB, o jeito mais rápido de provar que o KVM funciona |
| <img src="https://cdn.simpleicons.org/opensuse" width="20" height="20" alt=""> | `suse` | openSUSE — 1.0 GB |
| <img src="https://cdn.simpleicons.org/archlinux" width="20" height="20" alt=""> | `arch` | Arch Linux — 1.2 GB |
| <img src="https://cdn.jsdelivr.net/gh/selfhst/icons/svg/zimaos.svg" width="20" height="20" alt=""> | `zima` | ZimaOS — 1.4 GB |
| <img src="https://cdn.simpleicons.org/tails" width="20" height="20" alt=""> | `tails` | Tails — 1.5 GB |
| <img src="https://cdn.simpleicons.org/rockylinux" width="20" height="20" alt=""> | `rocky` | Rocky Linux — 2.1 GB |
| <img src="https://cdn.simpleicons.org/almalinux" width="20" height="20" alt=""> | `alma` | Alma Linux — 2.2 GB |
| <img src="https://cdn.simpleicons.org/mxlinux" width="20" height="20" alt=""> | `mx` | MX Linux — 2.2 GB |
| <img src="https://cdn.simpleicons.org/fedora" width="20" height="20" alt=""> | `fedora` | Fedora — 2.3 GB |
| <img src="https://cdn.simpleicons.org/nixos" width="20" height="20" alt=""> | `nixos` | NixOS — 2.4 GB |
| <img src="https://cdn.simpleicons.org/cachyos" width="20" height="20" alt=""> | `cachy` | CachyOS — 2.6 GB |
| <img src="https://cdn.simpleicons.org/linuxmint" width="20" height="20" alt=""> | `mint` | Linux Mint — 2.8 GB, padrão do próprio upstream |
| <img src="https://cdn.simpleicons.org/ubuntu" width="20" height="20" alt=""> | `ubuntus` | Ubuntu Server — 3.0 GB |
| <img src="https://cdn.simpleicons.org/debian" width="20" height="20" alt=""> | `debian` | Debian — 3.3 GB |
| <img src="https://cdn.simpleicons.org/gentoo" width="20" height="20" alt=""> | `gentoo` | Gentoo — 3.6 GB |
| <img src="https://cdn.simpleicons.org/slackware" width="20" height="20" alt=""> | `slack` | Slackware — 3.7 GB |
| <img src="https://cdn.simpleicons.org/kalilinux" width="20" height="20" alt=""> | `kali` | Kali Linux — 3.8 GB |
| <img src="https://cdn.simpleicons.org/zorin" width="20" height="20" alt=""> | `zorin` | Zorin OS — 3.8 GB |
| <img src="https://cdn.simpleicons.org/xubuntu" width="20" height="20" alt=""> | `xubuntu` | Xubuntu — 4.0 GB |
| <img src="https://cdn.simpleicons.org/manjaro" width="20" height="20" alt=""> | `manjaro` | Manjaro — 4.1 GB |
| <img src="https://cdn.simpleicons.org/kubuntu" width="20" height="20" alt=""> | `kubuntu` | Kubuntu — 4.4 GB |
| <img src="https://cdn.simpleicons.org/ubuntu" width="20" height="20" alt=""> | `ubuntu` | Ubuntu Desktop — 6.0 GB |
| <img src="https://cdn.simpleicons.org/centos" width="20" height="20" alt=""> | `centos` | CentOS — 7.0 GB |

## Arquivos

```
vm-qemu.container     unit
vm-qemu.env.example   ambiente
```

Dados em `~/.config/containers/volumes/vm/qemu/storage`.

## Atualizar

```bash
qh vm-qemu --update --apply
```

Pinado em `7.44`. Nada atualiza sozinho — a versão nova entra quando você roda
o comando acima.

## Backup

```bash
qh vm-qemu --backup --apply --out ~/backups
```

O arquivo guarda os diretórios desta unit, os segredos dela e o `.env` próprio — nada que uma irmã também leia.

Ele para esta unit, empacota e religa. A frio de propósito: copiar banco em uso
gera um arquivo que só falha na hora de restaurar.

```bash
qh vm-qemu --restore ~/backups/vm-qemu-20260809-1200.tar.gz --apply
```

A restauração pede que você digite `vm-qemu` para confirmar, porque os dados
atuais são apagados antes de o arquivo ser desempacotado.

## Remover

```bash
qh vm-qemu --remove --apply           # para, mantém os dados
qh vm-qemu --remove --purge --apply   # e apaga o volume dela
```

Só os volumes desta VM. O `vm-qemu.env` é mantido mesmo sendo lido só por ela —
o purge de uma unit não mexe no arquivo de ambiente.

## Comandos

```bash
systemctl --user status vm-qemu
podman logs -f vm-qemu
qh vm-qemu --update --apply
```

## Créditos

[QEMU](https://github.com/qemus/qemu) — MIT

[Documentação oficial](https://github.com/qemus/qemu#readme)
