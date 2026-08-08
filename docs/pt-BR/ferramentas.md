# Ferramentas do repositório

Dois scripts sem dependência, que rodam no CI a cada push
([`check.yml`](../../.github/workflows/check.yml)).

## Conferindo o repositório (`check.py`)

[![check](https://github.com/wallacepnts/quadlet-homelab/actions/workflows/check.yml/badge.svg)](https://github.com/wallacepnts/quadlet-homelab/actions/workflows/check.yml)

Roda sozinho a cada push e pull request
([`.github/workflows/check.yml`](../../.github/workflows/check.yml)) — num
runner pelado, sem podman e sem systemd, porque o `check.py` é leitura de
arquivo e o `install.py --prefix` não executa nada no host.

O job faz três coisas além da conferência:

- **monta o plano de instalação dos 48 serviços**, o que pega o que a
  análise estática não vê: `Secret=` sem receita no `install.ini` e
  `.example` sem destino;
- **roda o `test_install.py`**, que exercita o ciclo de vida inteiro numa
  sandbox — instalar, editar arquivo do usuário, backup, restaurar,
  recusar restore inválido, remover e purgar, com 23 asserts sobre o que
  aconteceu no disco;
- **roda os `--selftest`** dos dois scripts antes de tudo, porque parser
  quebrado torna o resto sem valor.

O `test_install.py` foi escrito depois de um code review achar quatro
defeitos no `--restore` que a verificação manual tinha deixado passar.
Reintroduzindo cada um deles de propósito, o teste pega os quatro.


As regras deste README que mais quebram são as que **não dão erro
visível**: o Quadlet gera a unit, o `podman inspect` não reclama, e o
defeito só aparece meses depois. O `check.py` confere essas, sem
dependência nenhuma além do Python da distro:

```bash
python3 check.py            # 0 se passar, 1 se houver erro
python3 check.py --selftest # testa o parser do próprio script
```

| Confere | Regra |
| --- | --- |
| basename de unit repetido entre pastas | 1 |
| `$` simples em `HealthCmd` | 7 |
| `Label=` com espaço sem aspas | 12 |
| `localhost` em `HealthCmd` | 13 |
| `Notify=healthy` sem `HealthCmd=` | 14 |
| `Label=` com barra invertida | 18 |
| nome real da tailnet em qualquer lugar do repo | — |
| **colisão de porta publicada** | — |
| tabela de versões vs. a tag em `Image=` | — |
| pasta em `apps/` sem linha na tabela, e vice-versa | — |

Os dois últimos blocos são o que a disciplina humana não estava dando
conta. Na primeira execução ele achou **quatro colisões de porta que
estavam no repositório desde julho** — adguardhome×gitea, nginx×owntracks,
freshrss×owntracks e beszel×calibre-web-automated. Nenhuma tinha aparecido
porque os pares nunca subiram ao mesmo tempo; a segunda unit simplesmente
falharia ao subir. Em cada par, quem chegou depois cedeu a porta.

**Dispensando uma regra**: quando a violação é intencional, a própria unit
diz por quê — o motivo mora ao lado do que ele justifica, como o resto dos
comentários daqui:

```ini
# check: ignora portas — alternativa EXCLUSIVA ao deluge publicando direto:
# ou roda o gluetun, ou roda o deluge sozinho. Nunca os dois.
```

A checagem de tailnet é a única isentada **por linha**, não por arquivo — uma
fixture de teste precisa conter um nome que pareça real pra checagem ter o que
testar:

```python
assert lab("https://traccar.some-real-name.ts.net") == ["some-real-name"]  # check: ignore tailnet
```

Avisos (não falham a execução) cobrem o que é convenção e não invariante:
`.network` em serviço single-container, e container principal sem
`wud.watch` nem `AutoUpdate=`.

## Checando versões (`updates.py`)

Automatiza a regra que mais dá trabalho manter: **a fonte é a página
oficial do projeto no GitHub, não a lista de tags do registry**. São 74
tags `Image=` neste repositório.

```bash
python3 updates.py            # só o que está atrasado
python3 updates.py --all    # inclui o que está em dia
```

Consulta o redirect de `github.com/<org>/<repo>/releases/latest`, que
devolve a tag sem gastar rate limit da API. Roda semanal no CI
([`updates.yml`](../../.github/workflows/updates.yml)) e joga o resultado no
resumo do job.

**O repositório no GitHub sai da imagem quando dá**: `ghcr.io/<org>/<x>`
espelha o dono, e `lscr.io/linuxserver/<x>` vira `linuxserver/docker-<x>`.
Quando não dá, declara-se em `apps/<app>/install.ini`:

```ini
[upstream]
vaultwarden = dani-garcia/vaultwarden
immich-postgres = -          # `-` = não comparar
```

O `-` é tão importante quanto o resto, e é onde mora o conhecimento que a
ferramenta sozinha não tem:

- **imagem-base de infra** (Postgres, Redis, Mosquitto, nginx) segue o
  compose do app, não o upstream dela;
- **componente pinado pelo app**: o Meilisearch do karakeep e o Gotenberg
  do paperless-ngx são a versão que o compose oficial *daquele app*
  valida — o upstream deles estar à frente não é atraso;
- **versionamento que não é do projeto**: a imagem do netboot.xyz
  versiona `0.7.6-nbxyzNN` (build do LinuxServer) enquanto as releases do
  repositório são do menu (`3.0.2`). Comparar os dois é exatamente o
  falso positivo que a regra 9 alerta.

Comparação usa só o prefixo comum de versão, senão a release
`4.0.19.2979-ls320` do LinuxServer diria que a imagem pinada em `4.0.19`
está atrasada.

**Release do GitHub não é imagem publicada.** O ghost anunciou a `v6.57.0`
e o Docker Hub ainda só tinha `6.56.0-alpine` — conferir se a tag existe
na variante que a unit usa antes de trocar o `Image=`, senão o serviço
não sobe:

```bash
podman manifest inspect docker.io/library/ghost:6.57.0-alpine
```

