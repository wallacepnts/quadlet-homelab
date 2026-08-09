# Downtify

<img src="https://cdn.jsdelivr.net/gh/homarr-labs/dashboard-icons/png/downtify.png" width="64" height="64" alt="">

**[🇺🇸 Read in English](../downtify.md)**

[< Media Stack](../../README.pt-BR.md)

Cole um link do Spotify e a música cai no disco.

Porta **8000**, unit `media-stack-downtify`.

Escreve direto em `/data/downloads`, a mesma pasta dos clientes de download. Não passa pelo Lidarr e nada renomeia o resultado — é o atalho para um álbum, não uma biblioteca.

Esse subdiretório precisa existir antes do primeiro start, porque é montado sozinho. A instalação cria.

## Instalação

```bash
qh media-stack-downtify
qh media-stack-downtify --apply
```

Instalar a pasta — `qh media-stack --apply` — traz esta junto com as outras.

## Arquivos

```
media-stack-downtify.container   unit
```

Dados em `~/.config/containers/volumes/media-stack/downtify/data`.

## Atualizar

```bash
qh media-stack-downtify --update --apply
```

Pinado em `2.9.1`. Nada atualiza sozinho — a versão nova entra quando você roda
o comando acima.

## Backup

```bash
qh media-stack --backup --apply --out ~/backups
```

O backup age sobre a pasta inteira, não sobre uma unit — nomear `media-stack-downtify` aqui é
recusado. O arquivo guarda todos os apps de `media-stack`, e restaurar é
`qh media-stack --restore <arquivo> --apply`.

## Remover

```bash
qh media-stack-downtify --remove --apply           # para, mantém os dados
qh media-stack-downtify --remove --purge --apply   # e apaga o volume dela
```

Só o que é desta unit: o `.env` compartilhado e os outros apps da pasta ficam
intactos.

## Comandos

```bash
systemctl --user status media-stack-downtify
podman logs -f downtify
qh media-stack-downtify --update --apply
```

## Créditos

[Downtify](https://github.com/henriquesebastiao/downtify) — GPL-3.0

[Documentação oficial](https://github.com/henriquesebastiao/downtify#readme)
