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
qh media-stack-sonarr --backup --apply --out ~/backups
```

O arquivo guarda só os diretórios desta unit. O `.env` compartilhado da pasta fica de fora, para restaurar um app não devolver uma cópia velha aos outros onze.

Ele para esta unit, empacota e religa. A frio de propósito: copiar banco em uso
gera um arquivo que só falha na hora de restaurar.

```bash
qh media-stack-sonarr --restore ~/backups/media-stack-sonarr-20260809-1200.tar.gz --apply
```

A restauração pede que você digite `media-stack-sonarr` para confirmar, porque os dados
atuais são apagados antes de o arquivo ser desempacotado.

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
