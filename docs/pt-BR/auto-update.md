# Auto-update

Nada neste repositório atualiza sozinho. Toda imagem é fixada — numa tag de
versão, ou num digest onde o projeto não publica versão (monica-next, os
toolboxes do Arch e do Fedora, mdrop, duas do immich) — e o `check.py` recusa
unit com `AutoUpdate=` ou com tag flutuante (`latest`, `main`, um major sozinho
como `16` ou `17-alpine`). Regra 9 das [convenções](./convencoes.md).

## Onde a versão vive

A imagem do próprio app que acompanha uma release do GitHub **não tem tag no repositório**:

```ini
# apps/memos/memos.container
Image=docker.io/neosmemo/memos
# apps/memos/install.ini
[image]
memos = {version}              # ou v{version}, {version}-alpine, {version:2} ...
```

O `qh` preenche o formato com a última release quando instala, e grava o resultado onde só
aquele host enxerga — um drop-in do Quadlet, `memos.container.d/10-image.conf`, com um
`Image=repo:tag` e uma linha `# was:` com a que ele trocou. O host continua rodando uma tag
fixa e conhecida, e o `systemctl cat memos` a mostra; o repositório nunca precisa de bump por ela.

```bash
qh <app> --update --apply            # recopia a unit; mantém a versão fixada no host
qh <app> --update --latest --apply   # também leva cada imagem à última release
qh <app> --update --latest --major --apply   # ...inclusive um salto para um major novo
qh-updates --host                    # o que roda aqui, contra o que o upstream lançou
```

Um salto de major fica retido a menos que você diga: as notas da release se leem antes (veja
abaixo). Um host instalado antes de as versões saírem do repositório continua rodando o que
rodava: o primeiro `--update` grava no drop-in a tag que acha na unit instalada. Para voltar,
ponha a tag que quer no `Image=` do drop-in e reinicie.

O que mantém a tag na unit — e se muda por um commit — é a imagem que NÃO é a release do
próprio app: banco ou cache fixado no que o compose do app valida (`[upstream]` com
`compose:` ou `-`), imagem de distro acompanhada pelo registry (`registry:`) e tudo o que é
fixado por digest.

```bash
qh-updates                     # o que está atrasado, contra a página de releases de cada projeto
qh-updates --bump --apply      # para essas: reescreve o Image= e a linha Fixado em de cada README
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
