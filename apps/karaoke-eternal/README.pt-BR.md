# Karaoke Eternal

<img src="https://api.iconify.design/mdi/microphone-variant.svg?color=%23888888" width="64" height="64" alt="">

**[🇺🇸 Read in English](./README.md)**

Karaokê com a sua própria biblioteca. Cada um enfileira música pelo celular, e
uma tela — TV, notebook — roda o player em tela cheia. O player é só uma página
do mesmo app, então não precisa instalar nada.

## Instalação

```bash
qh karaoke-eternal            # mostra o plano
qh karaoke-eternal --apply
```

Coloque os arquivos de karaokê em
`~/.config/containers/volumes/karaoke-eternal/media` e abra
`http://<ip-do-host>:8017` ou `https://karaoke.<your-tailnet>.ts.net`. **A
primeira conta criada é a de administrador.** No app, acrescente `/mnt/karaoke`
em Media Folders e mande varrer.

Ele lê CDG+MP3 e MP4; o nome do arquivo é o que ele interpreta como artista e
título, então `Artista - Título.mp4` é o formato a mirar.

<details>
<summary><b>Instalação manual</b></summary>

```bash
mkdir -p ~/.config/containers/systemd ~/.config/containers/env
mkdir -p ~/.config/containers/volumes/karaoke-eternal/{config,media}
podman unshare chown -R 1000:1000 ~/.config/containers/volumes/karaoke-eternal

wget -P ~/.config/containers/systemd/ \
  https://raw.githubusercontent.com/wallacepnts/quadlet-homelab/main/apps/karaoke-eternal/karaoke-eternal.container
wget -O ~/.config/containers/env/karaoke-eternal.env \
  https://raw.githubusercontent.com/wallacepnts/quadlet-homelab/main/apps/karaoke-eternal/.env.example

systemctl --user daemon-reload
systemctl --user start karaoke-eternal
```

</details>

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

## Atualizar

```bash
qh karaoke-eternal --update --apply
```

Pinado em `2.0.2`. Nada atualiza sozinho — a versão nova entra quando você roda
o comando acima.

## Backup

```bash
qh karaoke-eternal --backup --apply --out ~/backups
```

Para o serviço, empacota o banco, a mídia e o `.env`, e religa.

Para restaurar, por cima dos dados atuais:

```bash
qh karaoke-eternal --restore ~/backups/karaoke-eternal-20260810-1200.tar.gz --apply
```

## Remover

```bash
qh karaoke-eternal --remove --apply           # para, mantém os dados
qh karaoke-eternal --remove --purge --apply   # e apaga os volumes e o .env
```

O `--purge` apaga a mídia junto — ela fica num volume como todo o resto.

## Comandos

```bash
systemctl --user status karaoke-eternal
podman logs -f karaoke-eternal
podman exec karaoke-eternal wget -q --spider http://127.0.0.1:8080/ && echo ok
```

## Créditos

[Karaoke Eternal](https://github.com/bhj/KaraokeEternal) por
[bhj](https://github.com/bhj) — ISC

[Documentação oficial](https://www.karaoke-eternal.com/docs/)
