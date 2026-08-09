# Ferramentas

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
só o que está atrasado.

```bash
qh-updates
```

O repositório no GitHub é derivado do nome da imagem quando dá, e o
`install.ini` traz um override de `[upstream]` quando não dá — a imagem quase
nunca tem o nome do repositório (`dockurr/windows` contra `dockur/windows`).

Release no GitHub não é imagem publicada: a release pode sair horas antes de o
registry ter a tag. Se ele apontar uma versão que você ainda não consegue
puxar, esperar.
