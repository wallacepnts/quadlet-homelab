# Auto-update

Nada neste repositório atualiza sozinho. Toda imagem é fixada — numa tag de
versão, ou num digest onde o projeto não publica versão (monica-next, os
toolboxes do Arch e do Fedora, mdrop, duas do immich) — e o `check.py` recusa
unit com `AutoUpdate=` ou com tag flutuante (`latest`, `main`, um major sozinho
como `16` ou `17-alpine`). Regra 9 das [convenções](./convencoes.md).

Uma atualização é um commit, depois um comando no host:

```bash
qh-updates                     # o que está atrasado, contra a página de releases de cada projeto
qh-updates --bump --apply      # reescreve o Image= e as tabelas do README
qh <app> --update --apply      # leva para o host
```

## Por que nada atualiza sozinho

- **A versão no host é a versão no repositório.** Com tag fixa, a unit e o
  README dizem o que está rodando. Com `latest` a resposta é o que foi publicado
  por último, num momento que ninguém escolheu.
- **Quem decide o que a tag flutuante significa é o projeto.** O `latest` do
  gluetun é construído do branch principal, não das releases: passar para a
  `v3.41.3` mudou o build, não só o nome. O `16` do Postgres anda a cada versão
  menor.
- **Algumas atualizações precisam ser lidas antes.** Migração de schema sem
  volta, variável renomeada, um padrão que apaga dados — o Gitea 28 remove
  execuções de Actions com mais de 400 dias se ninguém disser o contrário. As
  notas da release são lidas antes do bump, não depois de o container ter subido
  nele.
- **O rollback nunca foi rede de proteção.** O `AutoUpdate=registry` só volta
  um container cujo healthcheck falha; um app que sobe e fica errado em silêncio
  continua na versão nova.

## Só num host

O repositório não traz isso. Um host que queira para um serviço edita a própria
cópia da unit — tag flutuante mais `AutoUpdate=registry`, e
`systemctl --user enable --now podman-auto-update.timer` uma vez — e o
`qh <app> --update` mostra essa edição antes de sobrescrevê-la.
