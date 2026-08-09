# Toolbx

<img src="https://cdn.jsdelivr.net/gh/containers/containertoolbx.org@main/apple-touch-icon.png" width="64" height="64" alt="">

**[🇺🇸 Read in English](./README.md)**

Shells descartáveis de Arch, Fedora, RHEL e Ubuntu, nas imagens oficiais do Toolbx — um lugar pra instalar ferramenta avulsa que não é o host.

## Instalar

```bash
qh toolbx            # mostra o plano
qh toolbx --apply
```

## Arquivos

```
toolbx-<distro>.container   uma unit por shell, quatro delas
install.ini                 onde o updates.py deve procurar cada uma
docs/                       uma página por shell
```

Dados em `~/.config/containers/volumes/toolbx/<distro>`, montados em `/work`.
Sem `.env`, sem segredos e sem portas: são shells, não serviços.

| | Shell | O que é | Versão |
| --- | --- | --- | --- |
| <img src="https://cdn.simpleicons.org/fedora" width="28" height="28" alt=""> | [Fedora](./docs/pt-BR/fedora.md) | Um shell Fedora com `dnf`, na imagem da própria Fedora | `45` |
| <img src="https://cdn.simpleicons.org/ubuntu" width="28" height="28" alt=""> | [Ubuntu](./docs/pt-BR/ubuntu.md) | Um shell Ubuntu com `apt`, para o que só publica `.deb` | `26.04` |
| <img src="https://cdn.simpleicons.org/archlinux" width="28" height="28" alt=""> | [Arch Linux](./docs/pt-BR/arch.md) | Um shell Arch com `pacman` e o AUR. Pinada por digest, não por tag | `digest` |
| <img src="https://cdn.simpleicons.org/redhat" width="28" height="28" alt=""> | [RHEL](./docs/pt-BR/rhel.md) | Um shell do RHEL, na imagem UBI que não exige assinatura | `10.2` |

São independentes — instalar a pasta traz as quatro, e você sobe a que precisa.
Nada se perde deixando as outras paradas.

## Atualizar

```bash
qh toolbx --update --apply
```

Cada shell tem a própria tag — a tabela acima lista todas. O Arch é a exceção,
pinado por digest porque a única tag dele é `latest`.

## Backup

```bash
qh toolbx --backup --apply --out ~/backups
```

Ele para as quatro, empacota os quatro `/work` e religa. Não há `.env` nem
segredo aqui para empacotar. Dá para fazer backup de um shell só — `qh
toolbx-fedora --backup --apply` — porque nenhum compartilha diretório com os
outros.
A frio de propósito: copiar banco vivo dá um arquivo que só falha na hora de
restaurar.

Pra restaurar, por cima dos dados atuais:

```bash
qh toolbx --restore ~/backups/toolbx-20260809-1200.tar.gz --apply
```

Ele pede que você digite `toolbx` pra confirmar, porque os dados atuais são
apagados antes de o arquivo ser extraído.

## Remover

```bash
qh toolbx --remove --apply           # para e tira, mantendo os dados
qh toolbx --remove --purge --apply   # e apaga volumes, secrets e .env
```

O `--purge` também pede o nome digitado, e apaga o `/work` das quatro. Não há
nó de tailnet a desregistrar: nenhuma delas é publicada.

## Comandos

Não existe unit `toolbx` — nomeie o shell que você quer:

```bash
systemctl --user status toolbx-fedora
podman exec -it toolbx-fedora bash
```

O log não é onde está o interessante: eles rodam `sleep infinity`, então o
`podman logs` fica vazio de propósito.

## Créditos

[containers/toolbox](https://containertoolbx.org/) — Apache-2.0

[Documentação oficial](https://containertoolbx.org/)
