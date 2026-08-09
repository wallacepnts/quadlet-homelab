# Toolbx Fedora

<img src="https://cdn.simpleicons.org/fedora" width="64" height="64" alt="">

**[🇺🇸 Read in English](../fedora.md)**

[< Toolbx](../../README.pt-BR.md)

Um shell Fedora com `dnf`, na imagem que a própria Fedora publica para isso.

Unit `toolbx-fedora`, image `registry.fedoraproject.org/fedora-toolbox:45`.

A imagem vem do registry da própria Fedora, não do Docker Hub, e a tag é o número da versão.

É a natural em host baseado em rpm: os pacotes batem com o que o host teria instalado.

O container roda `sleep infinity` e não faz nada sozinho — o que importa é o
shell que você abre nele. O `/work` é o único diretório que sobrevive a um
restart; o que for instalado pelo gerenciador de pacotes se perde quando o
container é recriado, e é isso que o torna descartável.

```bash
podman exec -it toolbx-fedora bash
podman exec -it --user root toolbx-fedora bash   # para instalar um pacote
```

O `UserNS=keep-id` mantém o seu uid dentro, então arquivo escrito em `/work`
sai com você como dono. É também por isso que instalar pacote exige o
`--user root` explícito.

## Instalação

```bash
qh toolbx-fedora
qh toolbx-fedora --apply
```

Instalar a pasta — `qh toolbx --apply` — traz esta junto com as outras três.

## Arquivos

```
toolbx-fedora.container   unit
```

Dados em `~/.config/containers/volumes/toolbx/fedora`. Sem `.env`, sem segredo e
sem porta: esta não é um serviço.

## Atualizar

```bash
qh toolbx-fedora --update --apply
```

Pinado em `45`. Nada atualiza sozinho — a versão nova entra quando você
roda o comando acima.

## Backup

```bash
qh toolbx-fedora --backup --apply --out ~/backups
```

Empacota o `/work` e nada mais — esta unit não compartilha diretório com as
outras três. Restaurar é `qh toolbx-fedora --restore <arquivo> --apply`.

## Remover

```bash
qh toolbx-fedora --remove --apply
qh toolbx-fedora --remove --purge --apply   # e apaga o /work
```

Só esta unit. As outras três mantêm os diretórios delas.

## Comandos

```bash
systemctl --user status toolbx-fedora
podman exec -it toolbx-fedora bash
qh toolbx-fedora --update --apply
```

## Créditos

[Toolbx](https://containertoolbx.org/) — Apache-2.0

[Documentação oficial](https://docs.fedoraproject.org/en-US/fedora-silverblue/toolbox/)
