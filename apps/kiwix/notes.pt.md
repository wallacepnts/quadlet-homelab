**Ele não começa vazio.** Sem nenhum `.zim` no volume ele sai, então a instalação o deixa parado. Coloque uma biblioteca em `~/.config/containers/volumes/kiwix/data` e inicie:

```bash
cd ~/.config/containers/volumes/kiwix/data
wget https://download.kiwix.org/zim/wikipedia/wikipedia_pt_all_nopic_2026-07.zim
podman unshare chown 1001:1001 *.zim
systemctl --user start kiwix
```

Catálogo: [library.kiwix.org](https://library.kiwix.org). Todo `.zim` da pasta é servido; um novo só precisa de reinício. As bibliotecas ficam fora do backup (dá para baixar de novo).
