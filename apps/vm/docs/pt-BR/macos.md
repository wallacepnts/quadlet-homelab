# macOS

<img src="https://cdn.simpleicons.org/macos/888888" width="64" height="64" alt="">

**[🇺🇸 Read in English](../macos.md)**

[< VMs](../../README.pt-BR.md)

Uma VM de macOS no navegador, do Big Sur ao Sequoia.

Visualizador web na **8008**, VNC na **5900**. Unit `vm-macos`.

A instalação pergunta qual versão. A imagem de recuperação é baixada da Apple no primeiro boot, e a instalação em si é feita na mão dentro do visualizador — Utilitário de Disco para apagar o disco virtual, depois o instalador.

Não há senha no visualizador: quem alcança a porta 8008 está dentro da máquina. A conta é a que você cria durante a configuração do macOS.

A licença da Apple só permite macOS em hardware Apple. Rodar aqui é decisão sua, e é por isso que esta VM não traz automação nenhuma para isso.

Todas precisam do `/dev/kvm` no host — sem virtualização por hardware a VM
não sobe ou fica lentíssima. O `RAM_SIZE` é reservado por toda a vida da VM,
então deixe o host respirar; o `DISK_SIZE` é um teto e cresce conforme o uso.

## Instalação

```bash
qh vm-macos
qh vm-macos --apply
```

Instalar a pasta — `qh vm --apply` — traz esta junto com as outras.

## Sistemas

A instalação pergunta e grava a resposta no `.env`. Só vale no primeiro boot:
a imagem é baixada uma vez, e mudar o valor depois não faz nada num disco já
escrito.

`VERSION` — Qual macOS instalar (baixado no primeiro boot).

| | Valor | O que é |
| --- | --- | --- |
| <img src="https://cdn.simpleicons.org/apple/888888" width="20" height="20" alt=""> | `15` | macOS 15 Sequoia — padrão do upstream |
| <img src="https://cdn.simpleicons.org/apple/888888" width="20" height="20" alt=""> | `14` | macOS 14 Sonoma |
| <img src="https://cdn.simpleicons.org/apple/888888" width="20" height="20" alt=""> | `13` | macOS 13 Ventura |
| <img src="https://cdn.simpleicons.org/apple/888888" width="20" height="20" alt=""> | `12` | macOS 12 Monterey |
| <img src="https://cdn.simpleicons.org/apple/888888" width="20" height="20" alt=""> | `11` | macOS 11 Big Sur |
| <img src="https://cdn.simpleicons.org/apple/888888" width="20" height="20" alt=""> | `26` | macOS 26 Tahoe — o upstream desaconselha, roda muito devagar |

## Arquivos

```
vm-macos.container     unit
vm-macos.env.example   ambiente
```

Dados em `~/.config/containers/volumes/vm/macos/storage`.

## Atualizar

```bash
qh vm-macos --update --apply
```

Pinado em `3.09`. Nada atualiza sozinho — a versão nova entra quando você roda
o comando acima.

## Backup

```bash
qh vm-macos --backup --apply --out ~/backups
```

O arquivo guarda os diretórios desta unit, os segredos dela e o `.env` próprio — nada que uma irmã também leia.

Ele para esta unit, empacota e religa. A frio de propósito: copiar banco em uso
gera um arquivo que só falha na hora de restaurar.

```bash
qh vm-macos --restore ~/backups/vm-macos-20260809-1200.tar.gz --apply
```

A restauração pede que você digite `vm-macos` para confirmar, porque os dados
atuais são apagados antes de o arquivo ser desempacotado.

## Remover

```bash
qh vm-macos --remove --apply           # para, mantém os dados
qh vm-macos --remove --purge --apply   # e apaga o volume dela
```

Só os volumes desta VM. O `vm-macos.env` é mantido mesmo sendo lido só por ela —
o purge de uma unit não mexe no arquivo de ambiente.

## Comandos

```bash
systemctl --user status vm-macos
podman logs -f vm-macos
qh vm-macos --update --apply
```

## Créditos

[macOS](https://github.com/dockur/macos) — MIT

[Documentação oficial](https://github.com/dockur/macos#readme)
