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

## Sistemas

A instalação pergunta e grava a resposta no `.env`. Só vale no primeiro boot:
a imagem é baixada uma vez, e mudar o valor depois não faz nada num disco já
escrito.

`VERSION` — Qual Windows instalar (baixado no primeiro boot).

| Valor | O que é |
| --- | --- |
| `11` | Windows 11 Pro — 7.9 GB |
| `11l` | Windows 11 LTSC — 4.7 GB, sem a Store, manutenção de longo prazo |
| `11e` | Windows 11 Enterprise — 6.6 GB |
| `10` | Windows 10 Pro — 5.7 GB |
| `10l` | Windows 10 LTSC — 4.6 GB |
| `10e` | Windows 10 Enterprise — 5.2 GB |
| `2025` | Windows Server 2025 — 7.6 GB |
| `2022` | Windows Server 2022 — 6.0 GB |
| `2019` | Windows Server 2019 — 5.3 GB |
| `2016` | Windows Server 2016 — 6.5 GB |
| `tiny11` | Tiny11 — 5.3 GB, versão enxuta da comunidade |
| `core11` | Tiny11 Core — 3.0 GB, o menor Windows 11 daqui |
| `tiny10` | Tiny10 — 3.6 GB |
| `8e` | Windows 8.1 Enterprise — 3.7 GB |
| `7u` | Windows 7 Ultimate — 3.1 GB |
| `vu` | Windows Vista Ultimate — 3.0 GB |
| `xp` | Windows XP Professional — 0.6 GB |
| `2k` | Windows 2000 Professional — 0.4 GB |
| `reactos` | ReactOS — 0.1 GB, não é Windows, não precisa de licença |

`LANGUAGE` — Idioma de instalação — qualquer um dos 33 nomes do upstream vale, não só estes.

| Valor | O que é |
| --- | --- |
| `English` |  |
| `Portuguese` | para pt-BR, ajuste também REGION e KEYBOARD no .env |
| `Spanish` |  |
| `French` |  |
| `German` |  |
| `Italian` |  |
| `Japanese` |  |
| `Chinese` |  |
| `Russian` |  |

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
