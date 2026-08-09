# Dispatcharr

<img src="https://cdn.jsdelivr.net/gh/homarr-labs/dashboard-icons/svg/dispatcharr.svg" width="64" height="64" alt="">

**[🇺🇸 Read in English](../dispatcharr.md)**

[< Media Stack](../../README.pt-BR.md)

IPTV: organiza listas de canais, o guia e vídeo sob demanda.

Porta **9191**, unit `media-stack-dispatcharr`.

À parte da corrente: não usa o Prowlarr, os *arr nem os clientes de download, e guarda os próprios dados em vez de escrever na raiz de mídia.

Acrescente a lista M3U e a fonte de EPG pela interface. Ele carrega Postgres e Redis dentro do mesmo container, e é por isso que é uma unit e não três.

## Instalação

```bash
qh media-stack-dispatcharr
qh media-stack-dispatcharr --apply
```

Instalar a pasta — `qh media-stack --apply` — traz esta junto com as outras.

## Arquivos

```
media-stack-dispatcharr.container   unit
```

Dados em `~/.config/containers/volumes/media-stack/dispatcharr/data`.

## Atualizar

```bash
qh media-stack-dispatcharr --update --apply
```

Pinado em `latest`. Nada atualiza sozinho — a versão nova entra quando você roda
o comando acima.

## Backup

```bash
qh media-stack-dispatcharr --backup --apply --out ~/backups
```

O arquivo guarda os diretórios desta unit, os segredos dela e o `.env` próprio — nada que uma irmã também leia.

Ele para esta unit, empacota e religa. A frio de propósito: copiar banco em uso
gera um arquivo que só falha na hora de restaurar.

```bash
qh media-stack-dispatcharr --restore ~/backups/media-stack-dispatcharr-20260809-1200.tar.gz --apply
```

A restauração pede que você digite `media-stack-dispatcharr` para confirmar, porque os dados
atuais são apagados antes de o arquivo ser desempacotado.

## Remover

```bash
qh media-stack-dispatcharr --remove --apply           # para, mantém os dados
qh media-stack-dispatcharr --remove --purge --apply   # e apaga o volume dela
```

Só o que é desta unit: o `.env` compartilhado e os outros apps da pasta ficam
intactos.

## Comandos

```bash
systemctl --user status media-stack-dispatcharr
podman logs -f dispatcharr
qh media-stack-dispatcharr --update --apply
```

## Créditos

[Dispatcharr](https://github.com/Dispatcharr/Dispatcharr) — CC-BY-NC-SA-4.0

[Documentação oficial](https://dispatcharr.github.io/Dispatcharr-Docs/)
