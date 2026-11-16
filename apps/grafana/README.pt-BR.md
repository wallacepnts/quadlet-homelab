# Grafana

<img src="https://cdn.jsdelivr.net/gh/homarr-labs/dashboard-icons/svg/grafana.svg" width="64" height="64" alt="">

**[🇺🇸 Read in English](./README.md)**

Painéis sobre dados que moram em outro lugar. O Grafana não guarda métrica
nenhuma — ele consulta uma fonte e desenha o resultado, então serve na medida
do que você apontar para ele.

## Primeiro acesso

A instalação exibe o usuário e a senha no final. Abra
`http://<ip-do-host>:3004` ou `https://grafana.<your-tailnet>.ts.net`.

## Arquivos

```
grafana.container   unit
.env.example        ambiente
install.ini         a receita da senha
```

Dados em `~/.config/containers/volumes/grafana/data`, na porta **3004**. A
configuração dele — usuários, painéis, fontes de dados — é SQLite nesse
diretório.

O `User=472` é o uid com que a imagem roda, e declarar isso é o que faz a
instalação ajustar o dono do volume. Sem ele, o Grafana sobe e não consegue
escrever o banco.

## Para onde apontar

Sozinho, o Grafana não mostra nada — ele não guarda métrica nenhuma, então a
primeira coisa depois de entrar é acrescentar uma fonte em Connections → Data
sources.

O **[Prometheus](../prometheus/README.pt-BR.md)** está neste repositório e é a
escolha natural. A URL dele é o nome do container, porque os dois entram na
`tsdproxy-net`:

```
http://prometheus:9090
```

Repare que ele coleta só a si mesmo de saída, então um Grafana novo sobre um
Prometheus novo desenha uma linha sobre o Prometheus. Acrescentar alvos é
trabalho no Prometheus, não no Grafana.

Outras fontes que fazem sentido aqui:

- O **[Beszel](../beszel/README.pt-BR.md)** já coleta CPU, RAM, disco e
  containers deste host e desenha sozinho. Se for só isso que você quer, o
  Grafana mais o Prometheus acrescentam dois serviços em vez de tirar um.
- Um **InfluxDB** em outro ponto da rede.
- **SQLite ou Postgres** de outro serviço, pelo plugin correspondente, quando a
  pergunta é sobre o dado do app e não sobre a máquina.

## Atualizar

Repare na imagem: a `grafana/grafana` é a compilação OSS e é a que acompanha as
releases. A `grafana/grafana-oss` é um espelho atrasado, e a
`grafana-enterprise` é outro produto.

## Backup

Para o serviço, empacota os dados, o `.env` e o segredo, e religa. O banco
guarda os painéis que você montou, que é a parte que daria trabalho refazer.

## Créditos

[Grafana](https://github.com/grafana/grafana) — AGPL-3.0

[Documentação oficial](https://grafana.com/docs/grafana/latest/)
