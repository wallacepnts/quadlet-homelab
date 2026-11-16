# Stirling-PDF

<img src="https://cdn.jsdelivr.net/gh/homarr-labs/dashboard-icons/svg/stirling-pdf.svg" width="64" height="64" alt="">

**[🇺🇸 Read in English](./README.md)**

Manipulação de PDF local — juntar, dividir, converter, OCR e assinar, no lugar dos sites de "PDF online".

## Primeiro acesso

Abrir `http://<ip-do-host>:8095` ou `https://stirling-pdf.<your-tailnet>.ts.net`.

## Arquivos

```
stirling-pdf.container
.env.example
install.ini
```

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

## Remover

O nó da tailnet não é desregistrado ao remover um app: isso é no admin do Tailscale.

## Créditos

[Stirling-Tools/Stirling-PDF](https://github.com/Stirling-Tools/Stirling-PDF) — MIT

[Documentação oficial](https://stirling.com)
