# Lidarr

<img src="https://cdn.jsdelivr.net/gh/homarr-labs/dashboard-icons/svg/lidarr.svg" width="64" height="64" alt="">

**[🇺🇸 Read in English](../lidarr.md)**

[< Media Stack](../../README.pt-BR.md)

O mesmo do Sonarr, para músicas: acompanha artistas e busca o que sai.

Porta **8686**, unit `media-stack-lidarr`.

Mesma configuração: uma root folder dentro de `/data` (`/data/media/music`), um cliente de download, e o Prowlarr para indexadores.

Para pegar um álbum ou uma faixa sem seguir um artista, o Downtify é o caminho mais curto.

## Instalação

```bash
qh media-stack-lidarr
qh media-stack-lidarr --apply
```

Instalar a pasta — `qh media-stack --apply` — traz esta junto com as outras.

## Arquivos

```
media-stack-lidarr.container   unit
.env.example                   ambiente, compartilhado com a pasta toda
```

Dados em `~/.config/containers/volumes/media-stack/lidarr/config`.

## Atualizar

```bash
qh media-stack-lidarr --update --apply
```

Pinado em `3.1.0`. Nada atualiza sozinho — a versão nova entra quando você roda
o comando acima.

## Backup

```bash
qh media-stack-lidarr --backup --apply --out ~/backups
```

O arquivo guarda só os diretórios desta unit. O `.env` compartilhado da pasta fica de fora, para restaurar um app não devolver uma cópia velha aos outros onze.

Ele para esta unit, empacota e religa. A frio de propósito: copiar banco em uso
gera um arquivo que só falha na hora de restaurar.

```bash
qh media-stack-lidarr --restore ~/backups/media-stack-lidarr-20260809-1200.tar.gz --apply
```

A restauração pede que você digite `media-stack-lidarr` para confirmar, porque os dados
atuais são apagados antes de o arquivo ser desempacotado.

## Remover

```bash
qh media-stack-lidarr --remove --apply           # para, mantém os dados
qh media-stack-lidarr --remove --purge --apply   # e apaga o volume dela
```

Só o que é desta unit: o `.env` compartilhado e os outros apps da pasta ficam
intactos.

## Comandos

```bash
systemctl --user status media-stack-lidarr
podman logs -f lidarr
qh media-stack-lidarr --update --apply
```

## Créditos

[Lidarr](https://github.com/Lidarr/Lidarr) — GPL-3.0

[Documentação oficial](https://wiki.servarr.com/lidarr)
