Coloque os arquivos de karaokê em
`~/.config/containers/volumes/karaoke-eternal/media` e abra
`http://<ip-do-host>:8017` ou `https://karaoke.<your-tailnet>.ts.net`. **A
primeira conta criada é a de administrador.** No app, acrescente `/mnt/karaoke`
em Media Folders e mande varrer.

Ele lê CDG+MP3 e MP4; o nome do arquivo é o que ele interpreta como artista e
título, então `Artista - Título.mp4` é o formato a mirar.

### Salas

Uma sala é o que um player entra; a fila pertence à sala, não ao servidor. É
assim que duas festas na mesma casa não dividem fila, e é também por isso que o
player pergunta a sala antes de começar.

### Backup

Para o serviço, empacota o banco, a mídia e o `.env`, e religa.

### Remover

O `--purge` apaga a mídia junto — ela fica num volume como todo o resto.
