# Karaoke Eternal

<img src="https://api.iconify.design/mdi/microphone-variant.svg?color=%23888888" width="64" height="64" alt="">

**[🇺🇸 Read in English](./README.md)**

Karaokê com a sua própria biblioteca. Cada um enfileira música pelo celular, e
uma tela — TV, notebook — roda o player em tela cheia. O player é só uma página
do mesmo app, então não precisa instalar nada.

## Primeiro acesso

Coloque os arquivos de karaokê em
`~/.config/containers/volumes/karaoke-eternal/media` e abra
`http://<ip-do-host>:8017` ou `https://karaoke.<your-tailnet>.ts.net`. **A
primeira conta criada é a de administrador.** No app, acrescente `/mnt/karaoke`
em Media Folders e mande varrer.

Ele lê CDG+MP3 e MP4; o nome do arquivo é o que ele interpreta como artista e
título, então `Artista - Título.mp4` é o formato a mirar.

## Arquivos

```
karaoke-eternal.container   unit
.env.example                ambiente
install.ini                 onde o updates.py deve procurar
```

Banco em `~/.config/containers/volumes/karaoke-eternal/config`, mídia em
`.../media`, na porta **8017**.

O banco é SQLite em modo WAL. Para o backup agendado isso significa
`karaoke-eternal:sqlite` no [gancho do Zerobyte](../zerobyte/README.pt-BR.md) —
copiar o `.sqlite3` e o `-wal` como dois arquivos é o que dá um arquivo que
falha na restauração.

## Salas

Uma sala é o que um player entra; a fila pertence à sala, não ao servidor. É
assim que duas festas na mesma casa não dividem fila, e é também por isso que o
player pergunta a sala antes de começar.

## Backup

Para o serviço, empacota o banco, a mídia e o `.env`, e religa.

## Remover

O `--purge` apaga a mídia junto — ela fica num volume como todo o resto.

## Créditos

[Karaoke Eternal](https://github.com/bhj/KaraokeEternal) por
[bhj](https://github.com/bhj) — ISC

[Documentação oficial](https://www.karaoke-eternal.com/docs/)
