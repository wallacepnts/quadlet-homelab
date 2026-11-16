A instalação exibe o usuário e a senha no final. Abra
`http://<ip-do-host>:3004` ou `https://grafana.<your-tailnet>.ts.net`.

### Para onde apontar

Sozinho, o Grafana não mostra nada — ele não guarda métrica nenhuma, então a
primeira coisa depois de entrar é acrescentar uma fonte em Connections → Data
sources.

O **Prometheus** está neste repositório e é a
escolha natural. A URL dele é o nome do container, porque os dois entram na
`tsdproxy-net`:

```
http://prometheus:9090
```

Repare que ele coleta só a si mesmo de saída, então um Grafana novo sobre um
Prometheus novo desenha uma linha sobre o Prometheus. Acrescentar alvos é
trabalho no Prometheus, não no Grafana.

Outras fontes que fazem sentido aqui:

- O **Beszel** já coleta CPU, RAM, disco e
  containers deste host e desenha sozinho. Se for só isso que você quer, o
  Grafana mais o Prometheus acrescentam dois serviços em vez de tirar um.
- Um **InfluxDB** em outro ponto da rede.
- **SQLite ou Postgres** de outro serviço, pelo plugin correspondente, quando a
  pergunta é sobre o dado do app e não sobre a máquina.

### Atualizar

Repare na imagem: a `grafana/grafana` é a compilação OSS e é a que acompanha as
releases. A `grafana/grafana-oss` é um espelho atrasado, e a
`grafana-enterprise` é outro produto.

### Backup

Para o serviço, empacota os dados, o `.env` e o segredo, e religa. O banco
guarda os painéis que você montou, que é a parte que daria trabalho refazer.
