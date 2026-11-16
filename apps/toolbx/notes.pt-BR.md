### Atualizar

Cada shell tem a própria tag — a tabela acima lista todas. O Arch é a exceção,
pinado por digest porque a única tag dele é `latest`.

### Backup

Ele para as quatro, empacota os quatro `/work` e religa. Não há `.env` nem
segredo aqui para empacotar. Dá para fazer backup de um shell só — `qh
toolbx-fedora --backup --apply` — porque nenhum compartilha diretório com os
outros.
A frio de propósito: copiar banco vivo dá um arquivo que só falha na hora de
restaurar.

### Remover

O `--purge` também pede o nome digitado, e apaga o `/work` das quatro. Não há
nó de tailnet a desregistrar: nenhuma delas é publicada.
