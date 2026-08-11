# Komga

<img src="https://cdn.jsdelivr.net/gh/selfhst/icons/svg/komga.svg" width="64" height="64" alt="">

**[🇺🇸 Read in English](./README.md)**

Biblioteca de quadrinhos e mangá: CBZ, CBR, PDF e EPUB, lidos no navegador ou
por qualquer leitor OPDS. Ele guarda a página em que você parou, por usuário,
então um volume começado no tablet continua do celular.

Ao lado do [calibre-web-automated](../calibre-web-automated/README.pt-BR.md) e
do [audiobookshelf](../audiobookshelf/README.pt-BR.md), a divisão é por
formato: livro lá, áudio lá, leitura página a página aqui.

## Instalação

```bash
qh komga            # mostra o plano
qh komga --apply
```

Abrir `https://komga.<your-tailnet>.ts.net` e criar a primeira conta — é essa a
configuração. Depois acrescente uma biblioteca apontando para `/books`.

<details>
<summary><b>Instalação manual (avançado)</b></summary>

```bash
mkdir -p ~/.config/containers/systemd ~/.config/containers/env
mkdir -p ~/.config/containers/volumes/komga/config
mkdir -p "$MEDIA_DATA_DIR/comics"

wget -P ~/.config/containers/systemd/ \
  https://raw.githubusercontent.com/wallacepnts/quadlet-homelab/main/apps/komga/komga.container
wget -O ~/.config/containers/env/komga.env \
  https://raw.githubusercontent.com/wallacepnts/quadlet-homelab/main/apps/komga/.env.example

# O container roda como uid 1000, que não é o seu depois do mapeamento
podman unshare chown -R 1000:1000 ~/.config/containers/volumes/komga

systemctl --user daemon-reload
systemctl --user start komga
```

</details>

## Arquivos

```
komga.container   unit
.env.example      ambiente
```

O `config/` guarda dois bancos SQLite — a biblioteca e a fila de tarefas —
mais o índice de busca Lucene e as miniaturas. É essa pasta que vai no backup;
os quadrinhos já são seus.

## Onde os quadrinhos ficam

```ini
Volume=${MEDIA_DATA_DIR}/comics:/books:ro,Z
```

O `${MEDIA_DATA_DIR}` é a mesma raiz que o
[media-stack](../media-stack/README.pt-BR.md) usa, vinda do
`~/.config/environment.d` — uma variável, vários serviços, que é a regra 19 das
convenções.

Montado **somente-leitura**: o Komga indexa, lê e não escreve nada onde estão
os seus arquivos. Apagar pela interface fica desligado por consequência, que é
a troca certa para uma biblioteca que você organiza por fora.

## Memória

`JAVA_TOOL_OPTIONS=-Xmx1g` no `.env`, porque senão a JVM se serve de um quarto
da RAM do host, e varrer uma biblioteca grande é justamente quando ela faz
isso. Numa máquina com setenta outros containers, esse teto é a diferença entre
uma varredura lenta e uma máquina começando a matar processos.

## Endurecimento

O ladder inteiro: `ReadOnly=true`, todas as capacidades descartadas,
`User=1000`. Medido com a aplicação de fato no ar — `Started ApplicationKt` no
log e `/actuator/health` respondendo 200 —, não só com o container rodando.

O `HealthStartPeriod=90s` não é folga: a JVM leva uns onze segundos para subir
aqui antes da primeira varredura, e biblioteca fria demora mais.

## Atualizar

```bash
qh komga --update --apply
```

Fixado em `1.26.1`.

## Backup

```bash
qh komga --backup --apply --out ~/backups
```

Empacota o `config/`: os bancos, o índice e as miniaturas. Perdê-lo perde o
progresso de leitura e os metadados que você corrigiu, não os quadrinhos.

Pra restaurar, por cima dos dados atuais:

```bash
qh komga --restore ~/backups/komga-20260811-1200.tar.gz --apply
```

## Remover

```bash
qh komga --remove --apply           # para e mantém os dados da biblioteca
qh komga --remove --purge --apply   # e apaga progresso e miniaturas
```

Nenhum dos dois toca nos quadrinhos: eles vivem fora do volume.

## Comandos

```bash
systemctl --user status komga
podman logs -f komga

du -sh ~/.config/containers/volumes/komga/config
```

## Créditos

[gotson/komga](https://github.com/gotson/komga) — MIT.

[Documentação oficial](https://komga.org/)
