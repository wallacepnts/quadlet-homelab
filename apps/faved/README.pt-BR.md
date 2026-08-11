# Faved

<img src="https://api.iconify.design/mdi/bookmark-multiple.svg?color=%23888888" width="64" height="64" alt="">

**[🇺🇸 Read in English](./README.md)**

Gerenciador de favoritos com tags aninhadas. PHP, SQLite e Apache — sem fila,
sem motor de busca, sem navegador headless: uma prateleira de links, e rápido
por causa disso.

Ao lado do [karakeep](../karakeep/README.pt-BR.md), que também guarda
favoritos, a diferença é o propósito. O karakeep arquiva a página, extrai o
texto e passa um modelo por cima, e paga isso em três containers. O Faved
guarda o link e as suas tags, num só.

## Instalação

```bash
qh faved            # mostra o plano
qh faved --apply
```

Abrir `https://faved.<your-tailnet>.ts.net` e criar a primeira conta — que é
também o passo de configuração, já que o banco SQLite é escrito no cadastro.

<details>
<summary><b>Instalação manual (avançado)</b></summary>

```bash
mkdir -p ~/.config/containers/systemd
mkdir -p ~/.config/containers/volumes/faved/storage

wget -P ~/.config/containers/systemd/ \
  https://raw.githubusercontent.com/wallacepnts/quadlet-homelab/main/apps/faved/faved.container

# O Apache desce para o www-data (uid 33), que não é você depois do mapeamento
podman unshare chown -R 33:33 ~/.config/containers/volumes/faved

systemctl --user daemon-reload
systemctl --user start faved
```

</details>

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

## Atualizar

```bash
qh faved --update --apply
```

Fixado em `2.10.0`.

## Backup

```bash
qh faved --backup --apply --out ~/backups
```

Para o serviço, empacota a pasta storage e sobe de novo. Aquela pasta é tudo —
os links, as tags e as contas.

Pra restaurar, por cima dos dados atuais:

```bash
qh faved --restore ~/backups/faved-20260811-1200.tar.gz --apply
```

## Remover

```bash
qh faved --remove --apply           # para e mantém os favoritos
qh faved --remove --purge --apply   # e apaga a pasta storage
```

## Comandos

```bash
systemctl --user status faved
podman logs -f faved
```

## Créditos

[denho/faved](https://github.com/denho/faved) — MIT.

[Documentação oficial](https://faved.to/docs/)
