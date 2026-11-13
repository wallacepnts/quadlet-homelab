# Ferramentas

Os três falam português quando o sistema fala, como o `qh`. O `QH_LANG=en` ou
`QH_LANG=pt` força um dos dois, e o `NO_COLOR=1` desliga a cor — que já sai
desligada sozinha sempre que a saída não é um terminal.

## `qh-check`

Lê todas as units de `apps/` e reprova o que falha em silêncio. Roda também no
CI a cada push, então erro aqui reprova o build.

```bash
qh-check
```

O que ele pega: unit com basename diferente do app, dois serviços publicando a
mesma porta do host, `Secret=` sem receita no `install.ini`, serviço faltando na
tabela de serviços do README, README de serviço cuja linha de versão não bate
mais com as units, `PodmanArgs=` levando o que o Quadlet já tem chave para ou um
espaço que ele não sobrevive, linha do
[`endurecimento.md`](./endurecimento.md) que não bate mais com a unit, `$` em
`HealthCmd` sem o escape duplo, barra invertida em valor de `Label=`, valor com espaço sem aspas, `Notify=healthy`
sem `HealthCmd`, e unit fora do layout padrão — os blocos descritos na
[referência](./referencia.md#anatomia-de-um-container). Esse ele também conserta:

```bash
qh-check --format      # reescreve todas as units no layout; só ordem e linhas em branco
```

Pra dispensar uma regra de propósito, a unit diz isso e o motivo é obrigatório:

```ini
# check: ignore ports vm-windows and vm-windows-arm never run together
```

## `qh-updates`

Compara cada tag de `Image=` com a última release do projeto no GitHub e mostra
só o que está desatualizado. O `--all` acrescenta o que está em dia e o que não
deu pra comparar.

```bash
qh-updates
```

O repositório no GitHub é derivado do nome da imagem quando dá, e o
`install.ini` traz um override de `[upstream]` quando não dá — a imagem quase
nunca tem o nome do repositório (`dockurr/windows` contra `dockur/windows`).

O `--bump` pega o que ele encontrou: reescreve o `Image=` e todo lugar que o
espelha — a linha `Fixado em` do README de cada serviço nos dois idiomas, e a
página por unit e a coluna Versão de uma pasta que documenta suas units em
separado. A tabela de serviços do README raiz não tem versão. Sem `--apply`, só
mostra o plano.

O `--host` compara o que está instalado nesta máquina, não o que o repositório
fixa, então dá pra saber o que está atrás do upstream antes mesmo do bump no
repositório. O `--json` imprime cada linha em JSON, que é o que a loja lê.

```bash
qh-updates --host            # o instalado aqui, contra a release de cada projeto
```

```bash
qh-updates --bump            # o que ele pegaria
qh-updates --bump --apply    # pegar
```

Ele recusa major, listando para você pegar um de cada vez com `--major`. A regra
9 das [convenções](./convencoes.md) é que versão se escolhe, não se recebe: o wud
9 sai no boot sem um administrador que antes não existia, o wger 2.7 converte
dados antigos com uma configuração que precisa estar certa antes e não pode
mudar depois. A recusa é filtro, não garantia — versão de calendário não tem
major, então 2026.8 para 2026.9 lê como minor e trouxe oito mudanças
incompatíveis. Ler as notas da release continua sendo o trabalho.

Secundário rastreado por `compose:` sobe para o que aquele compose declara,
digest incluído. Quando o compose roda duas imagens de mesmo nome — o do Postiz tem
`postgres:17-alpine` para o app e `postgres:16` para o Temporal — compara-se a que
tem a tag com a mesma forma da fixada. Pegar a primeira fazia o banco do Temporal
aparecer como um major atrasado.

Antes de perguntar se existe imagem mais nova, ele pergunta se a fixada ainda
existe, e reporta como sumida a que não. Duas chegaram lá por caminhos
diferentes: a imagem do Chrome que o karakeep usava foi retirada do registry, e
o digest do arch-toolbox foi coletado debaixo de uma imagem rolling. As duas
seguiam rodando da cópia local enquanto toda instalação nova falhava.

Release no GitHub não é imagem publicada: a release pode sair horas antes de o
registry ter a tag. Esse caso é reportado à parte — a tag é conferida no
registry antes de a atualização ser dada como disponível.

Secundário segue a versão que o compose do próprio app valida, não o upstream
dele — o Postgres do compose do immich se move quando o immich o move:

```ini
[upstream]
immich-postgres = compose:immich-app/immich:docker/docker-compose.yml
authentik-postgres = compose:https://goauthentik.io/docker-compose.yml
```

O compose é lido na versão em que a unit principal está fixada, que é a versão
pra qual você iria. URL direta também vale, pra projeto que publica o compose no
site em vez de no repositório.

Quando os dois lados fixam por digest, são os digests que se comparam — uma tag
como a `valkey:9` do immich se lê igual em duas releases enquanto a imagem
embaixo dela muda, e comparar tag ali só diria "em dia". Quando o compose não
fixa nada, isso é reportado como tal em vez de virar "em dia", que seria uma
comparação que nunca aconteceu.

Imagem que não versiona por release do GitHub — tag de distribuição, projeto
que só publica tags git, imagem versionada à parte do repositório — compara
com o registry:

```ini
[upstream]
netbootxyz = registry
```

Ele lista as tags do registry e pega a mais nova com o mesmo formato da nossa:
com `1.30.4-alpine` instalada, as candidatas são `\d+.\d+.\d+-alpine`, então
`-perl` e `latest` nunca vencem.

Um padrão depois dos dois-pontos estreita essa lista onde o formato sozinho não
dá conta — o nginx deixa a stable nas minors pares e a mainline nas ímpares, e
publica `-alpine` para as duas:

```ini
[upstream]
nginx = registry:^1\.\d*[02468]\.\d+-alpine$
```

Um valor é especial. O `registry:latest` pergunta em qual tag numerada o
`latest` resolve hoje, e compara com ela. Serve para projeto que numera também
as prereleases: o Fedora publica lado a lado a release estável, a branched e a
rawhide, todas numeradas, então o número mais alto é sempre a resposta errada —
o `46` é idêntico byte a byte à `rawhide`, enquanto o `latest` é a `44`.

```ini
[upstream]
toolbx-fedora = registry:latest
```

E `-` diz que não há o que comparar — a imagem Arch do toolbx só publica
`latest`, então ela é fixada por digest e tag nenhuma responderia por ela.

Tag flutuante (`latest`, major solto) não tem versão pra comparar, então a
comparação é por digest: se a tag hoje aponta pra outro lugar que a imagem
deste host, ele diz. Isso exige podman e a imagem já baixada.

## `qh-store`

Uma loja de apps web sobre o `qh`. Ela mostra o catálogo (`qh --catalog`), e
cada ação roda um comando do `qh`: primeiro o plano em simulação, depois
`qh <app> --apply` (e também `--update` e `--remove`), além de
iniciar/parar/reiniciar e logs de cada unit. Ela nunca roda `--purge`: dados
continuam sendo apagados só no terminal. Cada unit instalada mostra a tag dela
ao lado da última release do projeto (`qh-updates --host`, consultado em
segundo plano e guardado por seis horas), então dá pra ver o que está atrás sem
depender de um bump neste repositório. O que o terminal perguntaria durante
uma instalação, o formulário pergunta antes: secrets `manual` e `[vars]` ainda
não definidas. Eles são gravados com as mesmas funções e a mesma checagem
`[validate]` que o `qh` usa.

Ela roda no host como serviço `systemd --user`, não como Quadlet. O trabalho
dela é comandar o systemd e o podman como você, então um container precisaria
do seu home, do socket do podman e do barramento do systemd. É o mesmo acesso,
só que menos visível. Pelo mesmo motivo a unit não tem `NoNewPrivileges=`: o
podman rootless precisa do `newuidmap` com setuid.

A unit chama `~/.local/bin/qh-store`, o link que o `bootstrap.sh` cria; um clone de
antes da loja precisa rodar o `bootstrap.sh` de novo, ou o `ln -s` na mão.

```bash
systemctl --user enable --now ~/quadlet-homelab/store/qh-store.service
cat ~/.config/quadlet-homelab/store-token       # o login
```

Ela escuta em `127.0.0.1:8484`, então só esta máquina alcança. Para abrir de
outro computador, use `ssh -L 8484:127.0.0.1:8484 <host>`. Para acessar pela
tailnet, faça ela escutar no endereço da tailnet do host e publique pelo
`lists.yaml` do tsdproxy, do mesmo jeito que o Cockpit:

```bash
systemctl --user edit qh-store      # [Service]  Environment=QH_STORE_LISTEN=<tailscale-ip>:8484
```

```yaml
qh-store:
  ports:
    443/https:
      targets:
        - http://<tailscale-ip>:8484
```

Quem tiver o token instala e remove serviços como você. Trate-o como uma chave
SSH. Para revogar, apague o arquivo e reinicie o serviço.

`qh-store --prefix /tmp/test` aponta a loja para um sandbox, como o
`qh --prefix`. O `qh-store --selftest` cobre o login, as checagens das
requisições e uma instalação completa em sandbox.
