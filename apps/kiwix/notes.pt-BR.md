**Ele não sobe vazio.** Sem nenhum `.zim` no volume, o `kiwix-serve` responde
`Unable to add the ZIM file '*.zim' to the internal library` e sai — então a
instalação deixa o serviço posto e parado. Ponha uma biblioteca em
`~/.config/containers/volumes/kiwix/data` e inicie:

```bash
cd ~/.config/containers/volumes/kiwix/data
wget https://download.kiwix.org/zim/wikipedia/wikipedia_pt_all_nopic_2026-07.zim
podman unshare chown 1001:1001 *.zim
systemctl --user start kiwix
```

O catálogo está em [library.kiwix.org](https://library.kiwix.org).

### Como ele sabe o que servir

```ini
Exec=*.zim
```

Não é truque de shell que por acaso funciona: o `start.sh` da própria imagem
monta `kiwix-serve --port=$PORT $@` e executa **sem aspas**, a partir de
`/data`. O glob é expandido ali, então todo `.zim` do volume é servido e um
arquivo novo só precisa de um restart.

### Baixar no start

O `DOWNLOAD=<url>` no `.env` busca um arquivo para dentro do volume antes de
servir. Útil para o primeiro, e vício ruim depois: ele roda a cada start, e uma
Wikipedia completa tem 100 GB. Com uma biblioteca no lugar, ponha as próximas
na pasta na mão.

### Atualizar

As bibliotecas têm calendário próprio, que é o seu: baixe o `.zim` novo, apague o velho, reinicie.

### Backup

De propósito fora dos jobs de backup: um `.zim` é arquivo público que você
baixa de novo, e copiar dezenas de gigabytes de Wikipedia para um repositório
Restic custaria muito mais que buscar outra vez.
