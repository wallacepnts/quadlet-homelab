# Kiwix

<img src="https://cdn.jsdelivr.net/gh/homarr-labs/dashboard-icons/svg/kiwix.svg" width="64" height="64" alt="">

**[🇺🇸 Read in English](./README.md)**

A Wikipedia no seu disco, e tudo mais que o Kiwix empacota: Stack Overflow,
Projeto Gutenberg, palestras do TED, Wikcionário, manuais médicos e de reparo.
Servido por HTTP, com busca, e continua funcionando com a internet desligada.

Cada biblioteca é um arquivo `.zim` — um instantâneo comprimido e indexado.
Você escolhe quais manter, e elas custam o que custam: a Wikipedia em português
sem imagens fica em torno de 5 GB, com imagens perto de 40 GB.

## Instalação

```bash
qh kiwix            # mostra o plano
qh kiwix --apply
```

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

<details>
<summary><b>Instalação manual (avançado)</b></summary>

```bash
mkdir -p ~/.config/containers/systemd ~/.config/containers/env
mkdir -p ~/.config/containers/volumes/kiwix/data

wget -P ~/.config/containers/systemd/ \
  https://raw.githubusercontent.com/wallacepnts/quadlet-homelab/main/apps/kiwix/kiwix.container
wget -O ~/.config/containers/env/kiwix.env \
  https://raw.githubusercontent.com/wallacepnts/quadlet-homelab/main/apps/kiwix/.env.example

# O container roda como uid 1001, que não é o seu depois do mapeamento
podman unshare chown -R 1001:1001 ~/.config/containers/volumes/kiwix

systemctl --user daemon-reload
systemctl --user start kiwix
```

</details>

## Arquivos

```
kiwix.container   unit
.env.example      ambiente
```

O volume guarda os `.zim` e nada mais. É a única pasta deste repositório em que
o tamanho é o assunto — planeje o disco antes do primeiro download.

## Como ele sabe o que servir

```ini
Exec=*.zim
```

Não é truque de shell que por acaso funciona: o `start.sh` da própria imagem
monta `kiwix-serve --port=$PORT $@` e executa **sem aspas**, a partir de
`/data`. O glob é expandido ali, então todo `.zim` do volume é servido e um
arquivo novo só precisa de um restart.

## Baixar no start

O `DOWNLOAD=<url>` no `.env` busca um arquivo para dentro do volume antes de
servir. Útil para o primeiro, e vício ruim depois: ele roda a cada start, e uma
Wikipedia completa tem 100 GB. Com uma biblioteca no lugar, ponha as próximas
na pasta na mão.

## Endurecimento

O ladder inteiro: `ReadOnly=true`, todas as capacidades descartadas,
`User=1001` — o usuário `user` com que a própria imagem roda. Medido com uma
biblioteca de verdade baixada e servida, não só com o container de pé.

O `ReadOnly=true` não impede o download: o volume é bind mount, e o
somente-leitura vale para o sistema de arquivos do container.

## Atualizar

```bash
qh kiwix --update --apply
```

Fixado em `3.8.2`. As bibliotecas têm calendário próprio, que é o seu: baixe o
`.zim` novo, apague o velho, reinicie.

## Backup

De propósito fora dos jobs de backup: um `.zim` é arquivo público que você
baixa de novo, e copiar dezenas de gigabytes de Wikipedia para um repositório
Restic custaria muito mais que buscar outra vez.

## Remover

```bash
qh kiwix --remove --apply           # para e mantém as bibliotecas
qh kiwix --remove --purge --apply   # e apaga todos os .zim
```

## Comandos

```bash
systemctl --user status kiwix
podman logs -f kiwix

du -sh ~/.config/containers/volumes/kiwix/data
```

## Créditos

[kiwix/kiwix-tools](https://github.com/kiwix/kiwix-tools) — GPL-3.0.

[Documentação oficial](https://wiki.kiwix.org/)
