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

## Instalação

```bash
qh vm-windows
qh vm-windows --apply
```

Instalar a pasta — `qh vm --apply` — traz esta junto com as outras.

## Arquivos

```
vm-windows.container     unit
vm-windows.env.example   ambiente
```

Dados em `~/.config/containers/volumes/vm/windows/storage`, `~/.config/containers/volumes/vm/windows/oem`, `~/.config/containers/volumes/vm/windows/shared`.

A senha dela é o segredo `vm-windows-password`, gerado pela instalação.

## Atualizar

```bash
qh vm-windows --update --apply
```

Pinado em `6.04`. Nada atualiza sozinho — a versão nova entra quando você roda
o comando acima.

## Backup

```bash
qh vm-windows --backup --apply --out ~/backups
```

O arquivo guarda os diretórios desta unit, os segredos dela e o `.env` próprio — nada que uma irmã também leia.

Ele para esta unit, empacota e religa. A frio de propósito: copiar banco em uso
gera um arquivo que só falha na hora de restaurar.

```bash
qh vm-windows --restore ~/backups/vm-windows-20260809-1200.tar.gz --apply
```

A restauração pede que você digite `vm-windows` para confirmar, porque os dados
atuais são apagados antes de o arquivo ser desempacotado.

## Remover

```bash
qh vm-windows --remove --apply           # para, mantém os dados
qh vm-windows --remove --purge --apply   # e apaga o volume dela
```

Só os volumes desta VM. O `vm-windows.env` é mantido mesmo sendo lido só por ela —
o purge de uma unit não mexe no arquivo de ambiente.

O segredo `vm-windows-password` sobrevive à remoção de uma unit — ele fica registrado no
podman, não dentro do volume. `podman secret rm vm-windows-password` é o passo separado.

## Comandos

```bash
systemctl --user status vm-windows
podman logs -f vm-windows
qh vm-windows --update --apply
```

## Créditos

[Windows](https://github.com/dockur/windows) — MIT

[Documentação oficial](https://github.com/dockur/windows#readme)
