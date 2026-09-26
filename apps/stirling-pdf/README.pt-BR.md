# Stirling-PDF

<img src="https://cdn.jsdelivr.net/gh/homarr-labs/dashboard-icons/svg/stirling-pdf.svg" width="64" height="64" alt="">

**[🇺🇸 Read in English](./README.md)**

Manipulação de PDF local — juntar, dividir, converter, OCR e assinar, no lugar dos sites de "PDF online".

## Instalar

```bash
qh stirling-pdf            # mostra o plano
qh stirling-pdf --apply
```

Abrir `http://<ip-do-host>:8095` ou `https://stirling-pdf.<your-tailnet>.ts.net`.

<details>
<summary><b>Instalação manual</b></summary>

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

</details>

## Arquivos

```
stirling-pdf.container
.env.example
install.ini
```

## Atualizar

```bash
qh stirling-pdf --update --apply
```

Fixado em `3.0.0`. Nada atualiza sozinho — versão nova entra quando você
roda o comando acima.

## O que mudou na 3.0

**Telemetria.** Sem configuração, a 3.0 pergunta ao admin no primeiro login se
pode mandar dados de uso (PostHog e Scarf). O `.env` já vem com
`SYSTEM_ENABLEANALYTICS=false`, então ela nunca pergunta e nunca envia. Uma
instalação de antes da 3.0 mantém o `.env` antigo no `--update` — acrescente
essa linha à mão em `~/.config/containers/env/stirling-pdf.env`.

**Uma cota de uso.** O novo "Processor" em lote, a API e os recursos de IA são
gratuitos até 1.000 PDFs por mês. O editor em si — abrir um PDF e usar uma
ferramenta nele — continua gratuito e sem limite, que é para o que este serviço
está aqui.

## Backup

```bash
qh stirling-pdf --backup --apply --out ~/backups
```

Ele para o serviço, empacota os dados, o `.env` e os secrets, e sobe de novo.
A frio de propósito: copiar banco vivo dá um arquivo que só falha na hora de
restaurar.

Pra restaurar, por cima dos dados atuais:

```bash
qh stirling-pdf --restore ~/backups/stirling-pdf-20260809-1200.tar.gz --apply
```

Ele pede que você digite `stirling-pdf` pra confirmar, porque os dados atuais são
apagados antes de o arquivo ser extraído.

## Remover

```bash
qh stirling-pdf --remove --apply           # para e tira, mantendo os dados
qh stirling-pdf --remove --purge --apply   # e apaga volumes, secrets e .env
```

O `--purge` também pede o nome digitado. O nó da tailnet não é desregistrado
por isso — isso é no admin do Tailscale.

## Comandos

```bash
systemctl --user status stirling-pdf
podman logs -f stirling-pdf
```

## Créditos

[Stirling-Tools/Stirling-PDF](https://github.com/Stirling-Tools/Stirling-PDF) — MIT

[Documentação oficial](https://stirling.com)
