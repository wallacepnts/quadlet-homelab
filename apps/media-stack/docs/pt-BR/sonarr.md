# Sonarr

<img src="https://cdn.jsdelivr.net/gh/homarr-labs/dashboard-icons/svg/sonarr.svg" width="64" height="64" alt="">

**[🇺🇸 Read in English](../sonarr.md)**

[< Media Stack](../../README.pt-BR.md)

Séries: acompanha o que você adiciona, baixa episódios novos e arquiva na biblioteca.

Porta **8989**, unit `media-stack-sonarr`.

Settings -> Media Management, acrescente uma root folder dentro de `/data` (por exemplo `/data/media/tv`). Settings -> Download Clients, acrescente o SABnzbd (`sabnzbd:8080`) ou o Deluge (`deluge:8112`). Os indexadores chegam pelo Prowlarr.

Os downloads caem em `/data/downloads` e a biblioteca fica dentro do mesmo `/data`. É por isso que a raiz inteira é montada de uma vez: arquivar um episódio pronto vira renomear no mesmo sistema de arquivos, não copiar vários gigabytes.

## Instalação

```bash
qh media-stack-sonarr
qh media-stack-sonarr --apply
```

Instalar a pasta — `qh media-stack --apply` — traz esta junto com as outras.

## Arquivos

```
media-stack-sonarr.container   unit
.env.example                   ambiente, compartilhado com a pasta toda
```

Dados em `~/.config/containers/volumes/media-stack/sonarr/config`.

## Atualizar

```bash
qh media-stack-sonarr --update --apply
```

Pinado em `4.0.19`. Nada atualiza sozinho — a versão nova entra quando você roda
o comando acima.

## Backup

```bash
qh media-stack --backup --apply --out ~/backups
```

O backup age sobre a pasta inteira, não sobre uma unit — nomear `media-stack-sonarr` aqui é
recusado. O arquivo guarda todos os apps de `media-stack`, e restaurar é
`qh media-stack --restore <arquivo> --apply`.

## Remover

```bash
qh media-stack-sonarr --remove --apply           # para, mantém os dados
qh media-stack-sonarr --remove --purge --apply   # e apaga o volume dela
```

Só o que é desta unit: o `.env` compartilhado e os outros apps da pasta ficam
intactos.

## Comandos

```bash
systemctl --user status media-stack-sonarr
podman logs -f sonarr
qh media-stack-sonarr --update --apply
```

## Créditos

[Sonarr](https://github.com/Sonarr/Sonarr) — GPL-3.0

[Documentação oficial](https://wiki.servarr.com/sonarr)
