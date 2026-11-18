Ele pede o token de registro. Pegue-o no Gitea, em **Administração do site → Actions → Runners → Criar novo runner**, ou:

```bash
podman exec -u git gitea gitea actions generate-runner-token
```

O token é gasto no primeiro registro; depois o runner usa o arquivo `.runner` do volume.

Os labels são lidos **uma vez**, no registro: o `.env` nomeia uma imagem pequena (`GITEA_RUNNER_LABELS=alpine:docker://docker.io/library/alpine:3`, então o workflow diz `runs-on: alpine`). Para mudá-los, apague o `.runner` do volume e registre de novo com um token novo. Ao remover, apague o runner no Gitea também.
