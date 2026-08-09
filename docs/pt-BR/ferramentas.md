# Ferramentas

Os dois falam português quando o sistema fala, como o `qh`. O `QH_LANG=en` ou
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
tabela de versões do README, `$` em `HealthCmd` sem o escape duplo, barra
invertida em valor de `Label=`, valor com espaço sem aspas, e `Notify=healthy`
sem `HealthCmd`.

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

Imagem que não versiona por release do GitHub — tag de distribuição, projeto
que só publica tags git, imagem versionada à parte do repositório — compara
com o registry:

```ini
[upstream]
nginx = registry
```

Ele lista as tags do registry e pega a mais nova com o mesmo formato da nossa:
com `1.30.4-alpine` instalada, as candidatas são `\d+.\d+.\d+-alpine`, então
`-perl` e `latest` nunca vencem.

Tag flutuante (`latest`, major solto) não tem versão pra comparar, então a
comparação é por digest: se a tag hoje aponta pra outro lugar que a imagem
deste host, ele diz. Isso exige podman e a imagem já baixada.
