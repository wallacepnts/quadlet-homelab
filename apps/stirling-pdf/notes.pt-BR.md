Abrir `http://<ip-do-host>:8095` ou `https://stirling-pdf.<your-tailnet>.ts.net`.

### O que mudou na 3.0

**Telemetria.** Sem configuração, a 3.0 pergunta ao admin no primeiro login se
pode mandar dados de uso (PostHog e Scarf). O `.env` já vem com
`SYSTEM_ENABLEANALYTICS=false`, então ela nunca pergunta e nunca envia. Uma
instalação de antes da 3.0 mantém o `.env` antigo no `--update` — acrescente
essa linha à mão em `~/.config/containers/env/stirling-pdf.env`.

**Uma cota de uso.** O novo "Processor" em lote, a API e os recursos de IA são
gratuitos até 1.000 PDFs por mês. O editor em si — abrir um PDF e usar uma
ferramenta nele — continua gratuito e sem limite, que é para o que este serviço
está aqui.
