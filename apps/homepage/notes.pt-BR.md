Abrir `http://<ip-do-host>:3000` ou `https://homepage.<your-tailnet>.ts.net`.

### Widgets

Nenhum vem configurado. Para transformar o card numa leitura ao vivo — a fila,
o espaço livre — acrescente as labels na unit do próprio serviço:

```ini
Label=homepage.widget.type=sonarr
Label=homepage.widget.url=http://sonarr:8989
Label=homepage.widget.key={{HOMEPAGE_VAR_SONARR_KEY}}
```

A URL é o nome do container: todo serviço entra na `tsdproxy-net`, então a
Homepage chega nele sem sair para a LAN.

O `{{HOMEPAGE_VAR_X}}` é trocado pela variável de ambiente de mesmo nome, lida
do `.env` **deste** serviço. Use para toda chave: mantém o segredo fora do
arquivo de unit, o que num repositório público é a diferença entre uma senha e
uma senha publicada.

A [lista de widgets](https://gethomepage.dev/widgets/) diz o que cada tipo
precisa. A maioria pede chave de API que o app só emite depois do primeiro uso.

### Atualizar

`AutoUpdate=registry` ligado: a imagem é atualizada sozinha.
