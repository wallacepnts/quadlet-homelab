Ele pede o token de registro. Pegue no Gitea, em **Administração do site →
Actions → Runners → Criar novo Runner**, ou pela linha de comando:

```bash
podman exec -u git gitea gitea actions generate-runner-token
```

O token se gasta no primeiro registro. Depois disso o runner usa o arquivo
`.runner` do volume e nunca mais o lê.

### Os labels decidem quanto custa um job

O `runs-on:` de um workflow casa com um label, e um label nomeia uma imagem.
Registrar sem escolher faz o runner pedir `ubuntu-latest` e as irmãs — imagens
feitas para parecer um worker do GitHub, medidas em gigabytes, baixadas no
primeiro job. O `.env` nomeia imagens pequenas no lugar:

```ini
GITEA_RUNNER_LABELS=alpine:docker://docker.io/library/alpine:3
```

Aí o workflow diz `runs-on: alpine`. Os labels são lidos **uma vez**, no
registro: mudá-los depois exige apagar o `.runner` do volume e registrar de
novo com um token novo.

### Dois ajustes que não são o padrão do upstream

O `config.yaml` daqui difere do exemplo distribuído em dois pontos, ambos
medidos e não adivinhados:

- **`cache.dir: /data/cache`.** O padrão é `$HOME/.cache/actcache`, que fica
  dentro da imagem — e a unit a monta somente-leitura. O runner então sobe,
  responde ao health check, e registra `cannot init cache server, it will be
  disabled`. Saudável e pela metade, que é a falha em que este repositório vive
  esbarrando. Apontar para o volume resolve e ainda mantém o cache entre
  reinícios.
- **`metrics.enabled: true`.** Desligado no upstream. O `Notify=healthy` exige
  um `HealthCmd` (regra 14 das convenções), e o `/healthz` em `127.0.0.1:9101`
  é a única coisa que o runner serve. Fica no loopback: a porta não é publicada
  e não há autenticação na frente dela.

### Atualizar

O projeto mudou de nome: era publicado como `gitea/act_runner`, que parou na
`0.6.1`, e hoje é `gitea/runner` com versionamento próprio. Ele também vive no
`gitea.com` e não no GitHub, então o `install.ini` compara com o registry em
vez de uma página de releases que não existe.

### Backup

Vale pouco: o volume guarda um registro que se refaz em um minuto e um cache
que existe para ser descartado. Restaurar o `.runner` noutra máquina dá dois
runners reivindicando um registro só.

### Remover

O Gitea mantém o runner na lista dele de qualquer jeito — apague lá também, em
Administração do site → Actions → Runners.
