# homepage

<img src="https://cdn.jsdelivr.net/gh/homarr-labs/dashboard-icons/png/homepage.png" width="64" height="64" alt="">

**[🇺🇸 Read in English](./README.md)**

Dashboard que descobre e organiza containers por labels `homepage.*`.

> **As units deste repositório não carregam mais essas labels** (o catálogo da loja e o painel do
> `tsdproxy` assumiram o papel delas), então o Homepage sozinho lista só o que você der a ele: os
> serviços de `config/services.yaml`, ou labels que você acrescentar a uma unit, como no exemplo
> abaixo. Ele continua aqui para quem quer um painel feito à mão.

## Primeiro acesso

Abrir `http://<ip-do-host>:3000` ou `https://homepage.<your-tailnet>.ts.net`.

## Arquivos

```
homepage.container
.env.example
```

## Widgets

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

## Atualizar

`AutoUpdate=registry` ligado: a imagem é atualizada sozinha.

## Remover

O nó da tailnet não é desregistrado ao remover um app: isso é no admin do Tailscale.

## Créditos

[gethomepage/homepage](https://github.com/gethomepage/homepage) — GPL-3.0.

[Documentação oficial](https://gethomepage.dev)
