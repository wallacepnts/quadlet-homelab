# Stirling-PDF — Podman Quadlet (rootless)

**[🇬🇧 Read in English](./README.md)**

Deploy do [Stirling-PDF](https://github.com/Stirling-Tools/Stirling-PDF)
(juntar, dividir, converter, OCR, assinar e comprimir PDF, tudo local)
via Podman Quadlet, usando a imagem oficial
`docker.io/stirlingtools/stirling-pdf`.

## Arquitetura

Container único (Spring Boot + LibreOffice + Tesseract embutidos). Três
volumes:

| Volume | Pra quê |
| --- | --- |
| `/configs` | settings.yml, banco de usuários, chaves de sessão |
| `/usr/share/tessdata` | idiomas extras de OCR (baixados por você) |
| `/logs` | log da aplicação |

Nada sai da máquina — é o ponto do projeto: substitui os sites de "PDF
online" onde você faz upload do documento pra um terceiro.

### Sobre a variante da imagem

O upstream publica três: padrão, `-fat` (traz tudo pré-instalado, ~4 GB)
e `-ultra-lite` (só as operações básicas, sem OCR/conversão de Office).
Este repositório usa **a padrão**, e o `wud.tag.include` na unit existe
justamente pra impedir que o [wud](../wud/README.pt-BR.md) sinalize uma tag `-fat` como
"atualização" da que estamos usando.

### Sobre as capabilities

Este é o serviço que mais precisou de capability no repositório: cinco.
O entrypoint roda `setpriv` pra trocar de usuário e faz `chown` em
`/pipeline` e `/configs` no start, e o kit usual do repo
(`CHOWN,SETUID,SETGID`) não basta — sem `DAC_OVERRIDE` e `FOWNER` a
imagem morre com `setpriv: setresuid failed: Operation not permitted`.
`ReadOnly=true` também foi recusado pelo mesmo motivo. Está medido, não
copiado (ver CLAUDE.md, "Hardening de serviço novo").

## Arquivos

```
stirling-pdf.container   # unit principal
.env.example             # variáveis de configuração
```

## Pré-requisitos

- Podman rootless com systemd `--user` funcionando

## Instalação

```bash
python3 install.py stirling-pdf            # dry-run: mostra o que vai fazer
python3 install.py stirling-pdf --apply
```

Só na rede local, `--access local`; na tailnet e na LAN, `--access
both`. Acrescentar `--href-local` faz o link do dashboard apontar pra LAN. O script cria os diretórios, grava o
`.env`, gera os secrets, ajusta o dono dos volumes, sobe o serviço e
imprime o endereço no fim — ver
[Instalando e operando](../../docs/pt-BR/instalacao.md) no README
raiz.

Acessar `http://<ip-do-host>:8095` (ou via [tsdproxy](../tsdproxy/README.pt-BR.md) em
`https://stirling-pdf.<your-tailnet>.ts.net`).

<details>
<summary><b>Instalação manual</b> (avançado) — os mesmos passos, um a um</summary>


```bash
# 1. Baixar as units (sem precisar clonar o repositório)
mkdir -p ~/.config/containers/systemd
wget -P ~/.config/containers/systemd/ \
  https://raw.githubusercontent.com/wallacepnts/quadlet-homelab/main/apps/stirling-pdf/stirling-pdf.container

# 2. Diretórios de dados — bind mount exige que já existam antes do start
mkdir -p ~/.config/containers/volumes/stirling-pdf/{config,tessdata,logs}

# 3. Variáveis de ambiente
mkdir -p ~/.config/containers/env
wget -O ~/.config/containers/env/stirling-pdf.env \
  https://raw.githubusercontent.com/wallacepnts/quadlet-homelab/main/apps/stirling-pdf/.env.example

# 4. Subir
systemctl --user daemon-reload
systemctl --user start stirling-pdf
```

Acessar `http://<ip-do-host>:8095` (ou via [tsdproxy](../tsdproxy/README.pt-BR.md) em
`https://stirling-pdf.<your-tailnet>.ts.net`).

**Primeiro login:** `admin` / `stirling`. O `.env.example` já vem com
`SECURITY_ENABLE_LOGIN=true`, então a UI não fica aberta — **trocar a
senha no primeiro acesso** (Configurações → Conta).

</details>

## OCR em português

A imagem padrão vem com o inglês. Pra OCR em português, baixar o dado de
treino do Tesseract pro volume `tessdata`:

```bash
wget -P ~/.config/containers/volumes/stirling-pdf/tessdata/ \
  https://github.com/tesseract-ocr/tessdata/raw/main/por.traineddata
systemctl --user restart stirling-pdf
```

O idioma aparece na lista da ferramenta de OCR depois do restart.

## Auto-update

Sem `AutoUpdate=` — tag explícita (`2.14.3`), bump manual (regra 9 do
convenções). O `wud.tag.include` restringe o aviso do [wud](../wud/README.pt-BR.md) a
`X.Y.Z` puro, filtrando as variantes `-fat`/`-ultra-lite`.

## Backup & Recuperação

```bash
systemctl --user stop stirling-pdf
tar -czf stirling-pdf-backup-$(date +%Y%m%d-%H%M%S).tar.gz \
  -C ~/.config/containers/volumes stirling-pdf
systemctl --user start stirling-pdf
```

Backup pequeno de propósito: os PDFs processados não ficam no servidor,
o resultado vai direto pro download do navegador.

## Comandos úteis

```bash
systemctl --user status stirling-pdf
podman logs -f stirling-pdf
curl -s http://127.0.0.1:8095/api/v1/info/status   # {"version":"...","status":"UP"}
```

## Créditos

Deploy Quadlet baseado no
[Stirling-PDF](https://github.com/Stirling-Tools/Stirling-PDF) da
[Stirling-Tools](https://github.com/Stirling-Tools) (MIT).
