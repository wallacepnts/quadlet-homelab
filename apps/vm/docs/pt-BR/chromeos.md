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

## Instalação

```bash
qh vm-chromeos
qh vm-chromeos --apply
```

Instalar a pasta — `qh vm --apply` — traz esta junto com as outras.

## Sistemas

A instalação pergunta e grava a resposta no `.env`. Só vale no primeiro boot:
a imagem é baixada uma vez, e mudar o valor depois não faz nada num disco já
escrito.

`VERSION` — Qual canal do ChromeOS Flex acompanhar.

| | Valor | O que é |
| --- | --- | --- |
| <img src="https://cdn.simpleicons.org/googlechrome" width="20" height="20" alt=""> | `stable` | Stable — atualiza a cada 4 semanas, mais ou menos |
| <img src="https://cdn.simpleicons.org/googlechrome" width="20" height="20" alt=""> | `ltc` | Long-Term Channel — a cada 6 meses, mais ou menos |
| <img src="https://cdn.simpleicons.org/googlechrome" width="20" height="20" alt=""> | `ltr` | Long-Term Release — a cada 18 meses, mais ou menos |
| <img src="https://cdn.simpleicons.org/googlechrome" width="20" height="20" alt=""> | `beta` | Beta — toda semana, mais ou menos |

## Arquivos

```
vm-chromeos.container     unit
vm-chromeos.env.example   ambiente
```

Dados em `~/.config/containers/volumes/vm/chromeos/storage`.

A senha dela é o segredo `vm-chromeos-password`, gerado pela instalação.

## Atualizar

```bash
qh vm-chromeos --update --apply
```

Pinado em `1.02`. Nada atualiza sozinho — a versão nova entra quando você roda
o comando acima.

## Backup

```bash
qh vm-chromeos --backup --apply --out ~/backups
```

O arquivo guarda os diretórios desta unit, os segredos dela e o `.env` próprio — nada que uma irmã também leia.

Ele para esta unit, empacota e religa. A frio de propósito: copiar banco em uso
gera um arquivo que só falha na hora de restaurar.

```bash
qh vm-chromeos --restore ~/backups/vm-chromeos-20260809-1200.tar.gz --apply
```

A restauração pede que você digite `vm-chromeos` para confirmar, porque os dados
atuais são apagados antes de o arquivo ser desempacotado.

## Remover

```bash
qh vm-chromeos --remove --apply           # para, mantém os dados
qh vm-chromeos --remove --purge --apply   # e apaga o volume dela
```

Só os volumes desta VM. O `vm-chromeos.env` é mantido mesmo sendo lido só por ela —
o purge de uma unit não mexe no arquivo de ambiente.

O segredo `vm-chromeos-password` sobrevive à remoção de uma unit — ele fica registrado no
podman, não dentro do volume. `podman secret rm vm-chromeos-password` é o passo separado.

## Comandos

```bash
systemctl --user status vm-chromeos
podman logs -f vm-chromeos
qh vm-chromeos --update --apply
```

## Créditos

[ChromeOS](https://github.com/dockur/chromeos) — MIT

[Documentação oficial](https://github.com/dockur/chromeos#readme)
