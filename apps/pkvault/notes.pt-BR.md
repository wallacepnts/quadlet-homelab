Depois abra `https://pkvault.<your-tailnet>.ts.net`.

**Não há login.** Quem alcançar a página pode editar e apagar seus saves. Na
tailnet, esse alguém é você. Com `--access tailnet`, o padrão, a porta da LAN
nem é publicada; com `local` ou `both`, a porta `8126` fica aberta a todo mundo
da sua rede — escolha esses só numa LAN que seja só sua.

### Colocando e tirando seus saves

O primeiro start cria um save de exemplo do Emerald, para o app ter o que
mostrar. Tire-o nas configurações quando os seus estiverem lá.

- **Enviar pelo navegador** — o jeito mais simples: até 5 arquivos, 60 MB no
  total, guardados em `saves-uploads/`. Cada save tem um botão de download para
  levar o arquivo editado de volta ao jogo ou emulador.
- **Uma pasta no host** — para saves que ficam nesta máquina. Ponha-os dentro do
  volume, por exemplo em `data/saves/`, e acrescente `/pkvault/saves/` aos locais
  de save nas configurações. **Copie com `cp`, não mova com `mv`**: medido, um
  arquivo movido de outra pasta mantém o rótulo SELinux antigo e o container não
  consegue lê-lo, enquanto a cópia recebe o rótulo da pasta.

Para manter os saves em sincronia com outros aparelhos, o projeto recomenda o
Syncthing (que este repositório também tem). Pasta montada por duas units usa
`:z`, não `:Z` — regra 16 das convenções.

Uma mudança só vai para o save quando você manda salvar no app, e antes de cada
gravação é feito um backup de todos os saves e do armazenamento. O
`BACKUP_FILE_COUNT_LIMIT=30` mantém os 30 mais recentes — sem ele a pasta só
cresce. Medido: com o limite em 2, quatro backups deixam dois no disco.

### Atualizar

A imagem é marcada sem o `v` que a release tem. O PKVault traz o próprio PKHeX (26.8.26 na 2.3.3), então o suporte a um jogo novo chega com uma release do PKVault. A página consulta o GitHub em busca de release nova a partir do seu navegador; é a única chamada para fora.

### Backup

Os backups do próprio app ficam no mesmo volume, então este copia eles também.

### Remover

O nó da tailnet não é removido por aqui — isso é no admin do Tailscale.
