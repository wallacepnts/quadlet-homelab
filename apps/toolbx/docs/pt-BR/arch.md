# Toolbx Arch Linux

<img src="https://cdn.simpleicons.org/archlinux" width="64" height="64" alt="">

**[🇺🇸 Read in English](../arch.md)**

[< Toolbx](../../README.pt-BR.md)

Um shell Arch com `pacman` e acesso ao AUR.

Unit `toolbx-arch`, image `quay.io/toolbx/arch-toolbox@sha256:38d89c…`.

Pinada por digest, não por tag. Arch é rolling release: a única tag dele é `latest`, que muda a cada reconstrução da imagem, e tag que se move não é versão que este repositório consiga fixar.

Atualizar é trocar o digest na mão — `podman pull quay.io/toolbx/arch-toolbox:latest` e ler o novo no `podman inspect`. O `qh-updates` não tem como comparar, e o `install.ini` marca `-` por isso.

O container roda `sleep infinity` e não faz nada sozinho — o que importa é o
shell que você abre nele. O `/work` é o único diretório que sobrevive a um
restart; o que for instalado pelo gerenciador de pacotes se perde quando o
container é recriado, e é isso que o torna descartável.

```bash
podman exec -it toolbx-arch bash
podman exec -it --user root toolbx-arch bash   # para instalar um pacote
```

O `UserNS=keep-id` mantém o seu uid dentro, então arquivo escrito em `/work`
sai com você como dono. É também por isso que instalar pacote exige o
`--user root` explícito.

## Instalação

```bash
qh toolbx-arch
qh toolbx-arch --apply
```

Instalar a pasta — `qh toolbx --apply` — traz esta junto com as outras três.

## Arquivos

```
toolbx-arch.container   unit
```

Dados em `~/.config/containers/volumes/toolbx/arch`. Sem `.env`, sem segredo e
sem porta: esta não é um serviço.

## Atualizar

```bash
qh toolbx-arch --update --apply
```

Pinada por digest, então o comando acima reaplica a mesma imagem até o digest
da unit ser trocado.

## Backup

```bash
qh toolbx-arch --backup --apply --out ~/backups
```

Empacota o `/work` e nada mais — esta unit não compartilha diretório com as
outras três. Restaurar é `qh toolbx-arch --restore <arquivo> --apply`.

## Remover

```bash
qh toolbx-arch --remove --apply
qh toolbx-arch --remove --purge --apply   # e apaga o /work
```

Só esta unit. As outras três mantêm os diretórios delas.

## Comandos

```bash
systemctl --user status toolbx-arch
podman exec -it toolbx-arch bash
qh toolbx-arch --update --apply
```

## Créditos

[Toolbx](https://containertoolbx.org/) — Apache-2.0

[Documentação oficial](https://wiki.archlinux.org/title/Toolbx)
