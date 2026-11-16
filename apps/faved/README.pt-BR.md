# Faved

<img src="https://cdn.jsdelivr.net/gh/selfhst/icons/svg/faved.svg" width="64" height="64" alt="">

**[🇺🇸 Read in English](./README.md)**

Gerenciador de favoritos com tags aninhadas. PHP, SQLite e Apache — sem fila,
sem motor de busca, sem navegador headless: uma prateleira de links, e rápido
por causa disso.

Ao lado do [karakeep](../karakeep/README.pt-BR.md), que também guarda
favoritos, a diferença é o propósito. O karakeep arquiva a página, extrai o
texto e passa um modelo por cima, e paga isso em três containers. O Faved
guarda o link e as suas tags, num só.

## Primeiro acesso

Abrir `https://faved.<your-tailnet>.ts.net` e criar a primeira conta — que é
também o passo de configuração, já que o banco SQLite é escrito no cadastro.

## Arquivos

```
faved.container   unit
```

Sem `.env`: tudo o que o container precisa está na unit, e o resto se configura
pela interface. O banco é o arquivo único dentro de
`~/.config/containers/volumes/faved/storage`.

## Endurecimento

O ladder inteiro, medido: `ReadOnly=true` com tmpfs em `/tmp`, `/var/run` e
`/var/log/apache2`, todas as capacidades descartadas menos a
`NET_BIND_SERVICE`, e `User=33`.

A capacidade existe porque o Apache escuta na porta 80 **dentro** do container,
que é privilegiada. O `User=33` é o www-data, o usuário para o qual a própria
imagem desce — sem ele o volume pertence ao root e o app devolve página vazia
depois de falhar em silêncio ao gravar: `touch: cannot touch
'/var/www/html/storage/...': Permission denied`. O `qh` faz o `podman unshare
chown` por você porque a unit declara `User=`.

## Backup

Para o serviço, empacota a pasta storage e sobe de novo. Aquela pasta é tudo —
os links, as tags e as contas.

## Créditos

[denho/faved](https://github.com/denho/faved) — MIT.

[Documentação oficial](https://faved.to/)
