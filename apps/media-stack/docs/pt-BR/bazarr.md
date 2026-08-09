# Bazarr

<img src="https://cdn.jsdelivr.net/gh/homarr-labs/dashboard-icons/svg/bazarr.svg" width="64" height="64" alt="">

**[🇺🇸 Read in English](../bazarr.md)**

[< Media Stack](../../README.pt-BR.md)

Busca legendas para o que o Sonarr e o Radarr trouxeram.

Porta **6767**, unit `media-stack-bazarr`.

Settings -> Sonarr e Settings -> Radarr, com o endereço (`http://sonarr:8989`) e a API key de cada um. Depois Settings -> Languages, escolha os idiomas, e Settings -> Providers, escolha onde procurar.

Ele lê a biblioteca pelos *arr, então só enxerga o que eles conhecem. Arquivo colocado na pasta na mão não aparece.

## Instalação

```bash
qh media-stack-bazarr
qh media-stack-bazarr --apply
```

Instalar a pasta — `qh media-stack --apply` — traz esta junto com as outras.

## Arquivos

```
media-stack-bazarr.container   unit
.env.example                   ambiente, compartilhado com a pasta toda
```

Dados em `~/.config/containers/volumes/media-stack/bazarr/config`.

## Atualizar

```bash
qh media-stack-bazarr --update --apply
```

Pinado em `1.6.0`. Nada atualiza sozinho — a versão nova entra quando você roda
o comando acima.

## Backup

```bash
qh media-stack-bazarr --backup --apply --out ~/backups
```

O arquivo guarda só os diretórios desta unit. O `.env` compartilhado da pasta fica de fora, para restaurar um app não devolver uma cópia velha aos outros onze.

Ele para esta unit, empacota e religa. A frio de propósito: copiar banco em uso
gera um arquivo que só falha na hora de restaurar.

```bash
qh media-stack-bazarr --restore ~/backups/media-stack-bazarr-20260809-1200.tar.gz --apply
```

A restauração pede que você digite `media-stack-bazarr` para confirmar, porque os dados
atuais são apagados antes de o arquivo ser desempacotado.

## Remover

```bash
qh media-stack-bazarr --remove --apply           # para, mantém os dados
qh media-stack-bazarr --remove --purge --apply   # e apaga o volume dela
```

Só o que é desta unit: o `.env` compartilhado e os outros apps da pasta ficam
intactos.

## Comandos

```bash
systemctl --user status media-stack-bazarr
podman logs -f bazarr
qh media-stack-bazarr --update --apply
```

## Créditos

[Bazarr](https://github.com/morpheus65535/bazarr) — GPL-3.0

[Documentação oficial](https://wiki.bazarr.media/)
