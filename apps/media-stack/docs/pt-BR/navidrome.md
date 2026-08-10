# Navidrome

<img src="https://cdn.jsdelivr.net/gh/homarr-labs/dashboard-icons/svg/navidrome.svg" width="64" height="64" alt="">

**[🇺🇸 Read in English](../navidrome.md)**

[< Media Stack](../../README.pt-BR.md)

Toca a música que o Lidarr e o Downtify colocam na raiz de mídia. Fala a API
Subsonic, então qualquer cliente dela funciona no celular, inclusive com
sincronização offline — que é justamente o que o Jellyfin não faz bem.

Porta **4533**, unit `media-stack-navidrome`.

A raiz de mídia é montada **somente leitura** em `/music`, e o Navidrome varre
tudo. Em biblioteca grande, aponte só para a música com
`ND_MUSICFOLDER=/music/media/music` no `media-stack.env`.

A primeira conta criada é a de administrador. A varredura roda no start e a
cada hora depois disso.

## Instalação

```bash
qh media-stack-navidrome
qh media-stack-navidrome --apply
```

Instalar a pasta — `qh media-stack --apply` — traz esta junto com as outras.

## Arquivos

```
media-stack-navidrome.container   unit
.env.example                      ambiente, compartilhado com a pasta toda
```

Dados em `~/.config/containers/volumes/media-stack/navidrome/data`.

## Atualizar

```bash
qh media-stack-navidrome --update --apply
```

Pinado em `0.63.2`. Nada atualiza sozinho — a versão nova entra quando você
roda o comando acima.

## Backup

```bash
qh media-stack-navidrome --backup --apply --out ~/backups
```

O arquivo guarda só o diretório desta unit — as contagens de reprodução, as
notas e as contas. A música em si está na raiz de mídia, que não é desta unit
para empacotar.

```bash
qh media-stack-navidrome --restore ~/backups/media-stack-navidrome-20260810-1200.tar.gz --apply
```

## Remover

```bash
qh media-stack-navidrome --remove --apply           # para, mantém os dados
qh media-stack-navidrome --remove --purge --apply   # e apaga o volume dela
```

Só o que é desta unit: o `.env` compartilhado e a música ficam intactos.

## Comandos

```bash
systemctl --user status media-stack-navidrome
podman logs -f navidrome
qh media-stack-navidrome --update --apply
```

## Créditos

[Navidrome](https://github.com/navidrome/navidrome) — GPL-3.0

[Documentação oficial](https://www.navidrome.org/docs/)
