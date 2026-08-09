# ChromeOS

<img src="https://cdn.jsdelivr.net/gh/homarr-labs/dashboard-icons/svg/chrome.svg" width="64" height="64" alt="">

**[🇺🇸 Read in English](../chromeos.md)**

[< VMs](../../README.pt-BR.md)

ChromeOS Flex numa VM, com a GPU do host.

Visualizador web na **8013**, VNC na **5901**. Unit `vm-chromeos`.

A instalação pergunta qual canal acompanhar — stable, beta, ou um dos dois de longo prazo. Depois você entra com uma conta Google dentro da VM, como num Chromebook.

É a única VM daqui com senha no próprio visualizador: a conta é `admin` e a senha é um segredo gerado, mostrado pela instalação.

Ela alcança a placa de vídeo do host pelo `--device-cgroup-rule=c 226:* rwm`, que é a classe de dispositivos DRI. Sem essa regra ela ainda dá boot, só que sem aceleração.

Todas precisam do `/dev/kvm` no host — sem virtualização por hardware a VM
não sobe ou fica lentíssima. O `RAM_SIZE` é reservado por toda a vida da VM,
então deixe o host respirar; o `DISK_SIZE` é um teto e cresce conforme o uso.

## Comandos

```bash
systemctl --user status vm-chromeos
podman logs -f vm-chromeos
qh vm-chromeos --update --apply
```

## Créditos

[ChromeOS](https://github.com/dockur/chromeos) — MIT

[Documentação oficial](https://github.com/dockur/chromeos#readme)
