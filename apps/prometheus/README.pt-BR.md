# Prometheus

<img src="https://cdn.jsdelivr.net/gh/homarr-labs/dashboard-icons/svg/prometheus.svg" width="64" height="64" alt="">

**[🇺🇸 Read in English](./README.md)**

Pergunta as métricas de cada alvo em intervalo e guarda o histórico. É a fonte
de dados que o [Grafana](../grafana/README.pt-BR.md) desenha — o Grafana não
guarda nada, este guarda tudo.

## Primeiro acesso

Abra `http://<ip-do-host>:9090` ou `https://prometheus.<your-tailnet>.ts.net`.
Em Status → Targets você vê o que ele coleta e se cada um respondeu.

## Arquivos

```
prometheus.container   unit
config/prometheus.yml  a lista de coleta, para dentro do volume
install.ini            onde esse arquivo vai, e onde o updates.py procura
```

Config e histórico em `~/.config/containers/volumes/prometheus/`, na porta
**9090**. Não há `.env`: está tudo no YAML.

O `User=65534` é o `nobody`, uid com que a imagem roda. Declarar isso é o que
faz a instalação ajustar o dono do volume — sem ele, o Prometheus sobe e não
consegue escrever o banco.

## Acrescentando alvos

A config que vem coleta uma coisa só: o próprio Prometheus. Isso prova que o
arquivo está sendo lido e já dá uma consulta funcionando. O resto você
acrescenta:

```yaml
  - job_name: node
    static_configs:
      - targets: ["node-exporter:9100"]
```

Os alvos são alcançados pelo **nome do container**, porque todo serviço daqui
entra na `tsdproxy-net`. Sem IP, sem porta do host.

Um serviço só entra aqui se já falar o formato de exposição — a maioria dos
deste repositório não fala. O que costuma faltar primeiro é um `node-exporter`
para a própria máquina, e ele não vem aqui.

Depois de editar:

```bash
qh prometheus --update --apply
```

## Backup

Para o serviço, empacota a config e o histórico, e religa. A frio de propósito:
o TSDB é um banco como outro qualquer, e copiá-lo em uso dá um arquivo que só
falha na hora de restaurar.

## Créditos

[Prometheus](https://github.com/prometheus/prometheus) — Apache-2.0

[Documentação oficial](https://prometheus.io/docs/introduction/overview/)
