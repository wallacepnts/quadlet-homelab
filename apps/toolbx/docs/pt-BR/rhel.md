# Toolbx RHEL

<img src="https://cdn.simpleicons.org/redhat" width="64" height="64" alt="">

**[🇺🇸 Read in English](../rhel.md)**

[< Toolbx](../../README.pt-BR.md)

Um shell do Red Hat Enterprise Linux, na imagem UBI.

Unit `toolbx-rhel`, image `registry.access.redhat.com/ubi10/toolbox:10.2`.

UBI — Universal Base Image — é a parte do RHEL que a Red Hat publica sem assinatura. É a que serve para reproduzir um problema que só aparece em distribuição corporativa.

Os repositórios que exigem assinatura não estão habilitados, então o `dnf` alcança menos pacotes que num RHEL licenciado.

O container roda `sleep infinity` e não faz nada sozinho — o que importa é o
shell que você abre nele. O `/work` é o único diretório que sobrevive a um
restart; o que for instalado pelo gerenciador de pacotes se perde quando o
container é recriado, e é isso que o torna descartável.

```bash
podman exec -it toolbx-rhel bash
podman exec -it --user root toolbx-rhel bash   # para instalar um pacote
```

O `UserNS=keep-id` mantém o seu uid dentro, então arquivo escrito em `/work`
sai com você como dono. É também por isso que instalar pacote exige o
`--user root` explícito.

## Instalação

```bash
qh toolbx-rhel
qh toolbx-rhel --apply
```

Instalar a pasta — `qh toolbx --apply` — traz esta junto com as outras três.

## Arquivos

```
toolbx-rhel.container   unit
```

Dados em `~/.config/containers/volumes/toolbx/rhel`. Sem `.env`, sem segredo e
sem porta: esta não é um serviço.

## Atualizar

```bash
qh toolbx-rhel --update --apply
```

Pinado em `10.2`. Nada atualiza sozinho — a versão nova entra quando você
roda o comando acima.

## Backup

```bash
qh toolbx-rhel --backup --apply --out ~/backups
```

Empacota o `/work` e nada mais — esta unit não compartilha diretório com as
outras três. Restaurar é `qh toolbx-rhel --restore <arquivo> --apply`.

## Remover

```bash
qh toolbx-rhel --remove --apply
qh toolbx-rhel --remove --purge --apply   # e apaga o /work
```

Só esta unit. As outras três mantêm os diretórios delas.

## Comandos

```bash
systemctl --user status toolbx-rhel
podman exec -it toolbx-rhel bash
qh toolbx-rhel --update --apply
```

## Créditos

[Toolbx](https://containertoolbx.org/) — Apache-2.0

[Documentação oficial](https://catalog.redhat.com/software/base-images)
