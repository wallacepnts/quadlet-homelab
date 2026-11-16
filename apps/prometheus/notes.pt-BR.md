Abra `http://<ip-do-host>:9090` ou `https://prometheus.<your-tailnet>.ts.net`.
Em Status → Targets você vê o que ele coleta e se cada um respondeu.

### Acrescentando alvos

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

### Backup

Para o serviço, empacota a config e o histórico, e religa. A frio de propósito:
o TSDB é um banco como outro qualquer, e copiá-lo em uso dá um arquivo que só
falha na hora de restaurar.
