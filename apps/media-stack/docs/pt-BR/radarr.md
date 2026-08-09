# Radarr

<img src="https://cdn.jsdelivr.net/gh/homarr-labs/dashboard-icons/svg/radarr.svg" width="64" height="64" alt="">

**[🇺🇸 Read in English](../radarr.md)**

[< Media Stack](../../README.pt-BR.md)

O mesmo do Sonarr, para filmes.

Porta **7878**, unit `media-stack-radarr`.

Mesma configuração: uma root folder dentro de `/data` (`/data/media/movies`), um cliente de download, e os indexadores vindos do Prowlarr.

Sonarr e Radarr são separados de propósito — filme e série são nomeados e organizados por regras diferentes.

## Instalação

```bash
qh media-stack-radarr
qh media-stack-radarr --apply
```

Instalar a pasta — `qh media-stack --apply` — traz esta junto com as outras.

## Arquivos

```
media-stack-radarr.container   unit
.env.example                   ambiente, compartilhado com a pasta toda
```

Dados em `~/.config/containers/volumes/media-stack/radarr/config`.

## Atualizar

```bash
qh media-stack-radarr --update --apply
```

Pinado em `6.3.0`. Nada atualiza sozinho — a versão nova entra quando você roda
o comando acima.

## Backup

```bash
qh media-stack --backup --apply --out ~/backups
```

O backup age sobre a pasta inteira, não sobre uma unit — nomear `media-stack-radarr` aqui é
recusado. O arquivo guarda todos os apps de `media-stack`, e restaurar é
`qh media-stack --restore <arquivo> --apply`.

## Remover

```bash
qh media-stack-radarr --remove --apply           # para, mantém os dados
qh media-stack-radarr --remove --purge --apply   # e apaga o volume dela
```

Só o que é desta unit: o `.env` compartilhado e os outros apps da pasta ficam
intactos.

## Comandos

```bash
systemctl --user status media-stack-radarr
podman logs -f radarr
qh media-stack-radarr --update --apply
```

## Créditos

[Radarr](https://github.com/Radarr/Radarr) — GPL-3.0

[Documentação oficial](https://wiki.servarr.com/radarr)
