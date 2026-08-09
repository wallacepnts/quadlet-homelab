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
