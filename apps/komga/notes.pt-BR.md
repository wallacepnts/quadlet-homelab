Abrir `https://komga.<your-tailnet>.ts.net` e criar a primeira conta — é essa a
configuração. Depois acrescente uma biblioteca apontando para `/books`.

### Onde os quadrinhos ficam

```ini
Volume=${MEDIA_DATA_DIR}/comics:/books:ro,Z
```

O `${MEDIA_DATA_DIR}` é a mesma raiz que o
media-stack usa, vinda do
`~/.config/environment.d` — uma variável, vários serviços, que é a regra 19 das
convenções.

Montado **somente-leitura**: o Komga indexa, lê e não escreve nada onde estão
os seus arquivos. Apagar pela interface fica desligado por consequência, que é
a troca certa para uma biblioteca que você organiza por fora.

### Memória

`JAVA_TOOL_OPTIONS=-Xmx1g` no `.env`, porque senão a JVM se serve de um quarto
da RAM do host, e varrer uma biblioteca grande é justamente quando ela faz
isso. Numa máquina com setenta outros containers, esse teto é a diferença entre
uma varredura lenta e uma máquina começando a matar processos.

### Backup

Empacota o `config/`: os bancos, o índice e as miniaturas. Perdê-lo perde o
progresso de leitura e os metadados que você corrigiu, não os quadrinhos.

### Remover

Nenhum dos dois toca nos quadrinhos: eles vivem fora do volume.
