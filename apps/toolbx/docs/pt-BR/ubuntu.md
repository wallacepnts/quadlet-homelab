# Toolbx Ubuntu

<img src="https://cdn.simpleicons.org/ubuntu" width="64" height="64" alt="">

**[🇺🇸 Read in English](../ubuntu.md)**

[< Toolbx](../../README.pt-BR.md)

Um shell Ubuntu com `apt`, na imagem oficial do Toolbx.

Unit `toolbx-ubuntu`, image `quay.io/toolbx/ubuntu-toolbox:26.04`.

É a que serve quando uma ferramenta só publica `.deb`, ou quando as instruções que você segue pressupõem Ubuntu.

A tag é a versão do Ubuntu. Subir a tag é outra versão da distribuição, não um patch — os pacotes instalados na anterior não vêm junto.

O container roda `sleep infinity` e não faz nada sozinho — o que importa é o
shell que você abre nele. O `/work` é o único diretório que sobrevive a um
restart; o que for instalado pelo gerenciador de pacotes se perde quando o
container é recriado, e é isso que o torna descartável.

```bash
podman exec -it toolbx-ubuntu bash
podman exec -it --user root toolbx-ubuntu bash   # para instalar um pacote
```

O `UserNS=keep-id` mantém o seu uid dentro, então arquivo escrito em `/work`
sai com você como dono. É também por isso que instalar pacote exige o
`--user root` explícito.

## Instalação

```bash
qh toolbx-ubuntu
qh toolbx-ubuntu --apply
```

Instalar a pasta — `qh toolbx --apply` — traz esta junto com as outras três.

## Arquivos

```
toolbx-ubuntu.container   unit
```

Dados em `~/.config/containers/volumes/toolbx/ubuntu`. Sem `.env`, sem segredo e
sem porta: esta não é um serviço.

## Atualizar

```bash
qh toolbx-ubuntu --update --apply
```

Pinado em `26.04`. Nada atualiza sozinho — a versão nova entra quando você
roda o comando acima.

## Backup

```bash
qh toolbx-ubuntu --backup --apply --out ~/backups
```

Empacota o `/work` e nada mais — esta unit não compartilha diretório com as
outras três. Restaurar é `qh toolbx-ubuntu --restore <arquivo> --apply`.

## Remover

```bash
qh toolbx-ubuntu --remove --apply
qh toolbx-ubuntu --remove --purge --apply   # e apaga o /work
```

Só esta unit. As outras três mantêm os diretórios delas.

## Comandos

```bash
systemctl --user status toolbx-ubuntu
podman exec -it toolbx-ubuntu bash
qh toolbx-ubuntu --update --apply
```

## Créditos

[Toolbx](https://containertoolbx.org/) — Apache-2.0

[Documentação oficial](https://containertoolbx.org/)
