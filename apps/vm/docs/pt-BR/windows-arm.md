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

## Instalação

```bash
qh vm-windows-arm
qh vm-windows-arm --apply
```

Instalar a pasta — `qh vm --apply` — traz esta junto com as outras.

## Arquivos

```
vm-windows-arm.container     unit
vm-windows-arm.env.example   ambiente
```

Dados em `~/.config/containers/volumes/vm/windows-arm/storage`.

A senha dela é o segredo `vm-windows-arm-password`, gerado pela instalação.

## Atualizar

```bash
qh vm-windows-arm --update --apply
```

Pinado em `6.04`. Nada atualiza sozinho — a versão nova entra quando você roda
o comando acima.

## Backup

```bash
qh vm --backup --apply --out ~/backups
```

O backup age sobre a pasta inteira, não sobre uma unit — nomear `vm-windows-arm` aqui é
recusado. O arquivo guarda todos os apps de `vm`, e restaurar é
`qh vm --restore <arquivo> --apply`.

## Remover

```bash
qh vm-windows-arm --remove --apply           # para, mantém os dados
qh vm-windows-arm --remove --purge --apply   # e apaga o volume dela
```

Só os volumes desta VM. O `vm-windows-arm.env` é mantido mesmo sendo lido só por ela —
o purge de uma unit não mexe no arquivo de ambiente.

O segredo `vm-windows-arm-password` sobrevive à remoção de uma unit — ele fica registrado no
podman, não dentro do volume. `podman secret rm vm-windows-arm-password` é o passo separado.

## Comandos

```bash
systemctl --user status vm-windows-arm
podman logs -f vm-windows-arm
qh vm-windows-arm --update --apply
```

## Créditos

[Windows on ARM](https://github.com/dockur/windows-arm) — MIT

[Documentação oficial](https://github.com/dockur/windows-arm#readme)
