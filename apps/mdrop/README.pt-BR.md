# mdrop — Podman Quadlet (rootless)

**[🇬🇧 Read in English](./README.md)**

Deploy do [mdrop](https://github.com/samapriya/mdrop) (interface web para
o [MarkItDown](https://github.com/microsoft/markitdown) da Microsoft) via
Podman Quadlet, usando a imagem oficial `docker.io/samapriya/mdrop`.

Arrasta o arquivo, recebe Markdown. Converte PDF, Word, Excel,
PowerPoint, imagem (com OCR) e áudio (com transcrição).

## Por que este e não o markitdown direto

O [markitdown](https://github.com/microsoft/markitdown) não dá pra
implantar como serviço neste repositório, por três motivos:

- a Microsoft **não publica imagem** — o upstream manda construir
  localmente, o que quebra o modelo daqui (unit baixada por `wget`
  referenciando imagem publicada e pinada);
- o `ENTRYPOINT` é `markitdown`: é uma **CLI**, não um servidor;
- a variante servidor (`markitdown-mcp`) é documentada pelo próprio
  upstream como local-use-only, com *"DO NOT bind the server to other
  interfaces"* — porque `convert_to_markdown(uri)` aceita `file:` (lê
  arquivo arbitrário de dentro do container) e `http:` (SSRF a partir da
  sua rede).

O mdrop resolve os três: publica imagem, é um servidor HTTP de verdade, e
a interface só aceita **upload**, não URI arbitrária.

## Arquitetura

Container único (FastAPI/uvicorn). **Sem volume, sem banco, sem sessão.**
A área de conversão é um `Tmpfs` — o arquivo que você envia fica em RAM e
nunca toca o disco do host. Confirmado com `podman inspect`: o container
não tem mount nenhum.

Consequência prática: **não há backup a fazer**, e reinstalar é o
"restore".

### Pinado por digest

O upstream publica só `latest` e `main`, sem tag versionada e sem release
no GitHub. Como a regra 9 pede versão fixa, a unit pina pelo **digest** —
mesmo tratamento que o Postgres e o valkey do [immich](../immich/README.pt-BR.md)
recebem. Por isso também não tem `wud.watch`: não há tag pra comparar.

Pra atualizar, conferir o projeto e trocar o digest:

```bash
podman pull docker.io/samapriya/mdrop:latest
podman image inspect docker.io/samapriya/mdrop:latest --format '{{index .RepoDigests 0}}'
```

## Arquivos

```
mdrop.container   # unit principal
```

## Instalação

```bash
python3 install.py mdrop            # dry-run: mostra o que vai fazer
python3 install.py mdrop --apply
```

Só na rede local, `--access local`; na tailnet e na LAN, `--access
both`. Acrescentar `--href-local` faz o link do dashboard apontar pra LAN. O script cria os diretórios, grava o
`.env`, gera os secrets, ajusta o dono dos volumes, sobe o serviço e
imprime o endereço no fim — ver
[Instalando e operando](../../docs/pt-BR/instalacao.md) no README
raiz.

Acessar `http://<ip-do-host>:8292` (ou via [tsdproxy](../tsdproxy/README.pt-BR.md) em
`https://mdrop.<your-tailnet>.ts.net`).

<details>
<summary><b>Instalação manual</b> (avançado) — os mesmos passos, um a um</summary>


```bash
# 1. Baixar a unit (sem precisar clonar o repositório)
mkdir -p ~/.config/containers/systemd
wget -P ~/.config/containers/systemd/ \
  https://raw.githubusercontent.com/wallacepnts/quadlet-homelab/main/apps/mdrop/mdrop.container

# 2. Subir — sem mkdir, sem secret, sem env
systemctl --user daemon-reload
systemctl --user start mdrop
```

Acessar `http://<ip-do-host>:8292` (ou via [tsdproxy](../tsdproxy/README.pt-BR.md) em
`https://mdrop.<your-tailnet>.ts.net`).

</details>

## Segurança

**Não tem autenticação** — o próprio README do projeto diz isso e
recomenda VPN ou proxy de autenticação na frente. Aqui a tailnet cumpre o
papel de VPN; pra exigir login, o caminho é o
[Authentik](../authentik/README.pt-BR.md).

O desenho ajuda: nada é gravado, nada é logado além de nome e tamanho do
arquivo, e não há URI arbitrária — só upload. Ainda assim, o que você
converte passa pelo processo, então vale o mesmo cuidado do
[stirling-pdf](../stirling-pdf/README.pt-BR.md): é justamente pra não mandar documento
pra site de terceiro que ele existe.

### O tamanho do `/tmp/mdrop`

`1G` em RAM, como o compose oficial. É teto, não reserva — só ocupa o que
o arquivo em conversão usa. Baixar se você só converte documento pequeno,
ou se a máquina for apertada de memória; a [regra 20](../../docs/pt-BR/convencoes.md) explica
por que `Tmpfs` sem `size=` é perigoso.

## Auto-update

Sem `AutoUpdate=` e sem `wud.watch` — ver "Pinado por digest" acima.

## Backup & Recuperação

Nenhum. Não há estado.

## Comandos úteis

```bash
systemctl --user status mdrop
podman logs -f mdrop
# converter pela linha de comando
curl -F "file=@documento.pdf" http://127.0.0.1:8292/convert
```

## Créditos

Deploy Quadlet baseado no [mdrop](https://github.com/samapriya/mdrop) de
[samapriya](https://github.com/samapriya) (MIT), que embrulha o
[MarkItDown](https://github.com/microsoft/markitdown) da Microsoft.
