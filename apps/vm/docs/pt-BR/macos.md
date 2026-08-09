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

## Comandos

```bash
systemctl --user status vm-macos
podman logs -f vm-macos
qh vm-macos --update --apply
```

## Créditos

[macOS](https://github.com/dockur/macos) — MIT

[Documentação oficial](https://github.com/dockur/macos#readme)
