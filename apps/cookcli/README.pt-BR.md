# CookCLI — Podman Quadlet (rootless)

**[🇬🇧 Read in English](./README.md)**

Deploy do [CookCLI](https://github.com/cooklang/cookcli) (servidor de
receitas em [CookLang](https://cooklang.org)) via Podman Quadlet, usando a
imagem oficial `ghcr.io/cooklang/cookcli`.

## Arquitetura

Container único, Rust. **Sem banco de dados, e isso é o ponto**: as
receitas *são* arquivos `.cook` numa pasta. Você escreve num editor de
texto, versiona em git, e o servidor só lê e renderiza — com lista de
compras e escalonamento de porções calculados na hora.

```cook
---
title: Café com leite
servings: 1
---

Esquente o @leite{200%ml} e misture com o @café{50%ml}.
```

É o oposto de um gerenciador com banco e formulário: aqui a receita é
texto sob controle de versão, editável em qualquer editor.

### `UserNS=keep-id`, e não `User=`

A imagem **recusa subir** quando o uid do processo não bate com o dono da
pasta de receitas — ela para e imprime literalmente:

```
cookcli:
  user: "1000:1000"  # <-- change to match your host user
```

O degrau `User=1000` passa no teste de hardening, mas está fora de
propósito aqui: a pasta de receitas é **área de edição sua**, e com
`User=` ela passaria a pertencer a um subuid que você não consegue
escrever. É o mesmo trade-off do `inbox` do [vaultzap](../vaultzap/README.pt-BR.md).

`UserNS=keep-id` resolve os dois lados: o processo roda com o seu uid, a
pasta continua sua, e o cookcli fica satisfeito. Não é hardening (regra 20
das convenções), é escolha de dono.

### Sem healthcheck, e por quê

A imagem traz só o binário `cook` e o `dash` — nenhum `wget`, `curl`, `nc`
ou `python3` pra fazer uma requisição de dentro. Sem cliente HTTP não há
healthcheck honesto, então a unit não tem `HealthCmd` nem
`Notify=healthy` (que exigiria um, pela regra 14). O que sobra é o ciclo
do container: o `cook server` é o PID 1, e se morrer o `Restart=always`
sobe de novo.

## Arquivos

```
cookcli.container      # unit principal
aisle.conf.example     # seções do mercado, pra lista de compras
pantry.conf.example    # o que já tem em casa, subtraído da lista
```

## Instalação

```bash
python3 install.py cookcli            # dry-run: mostra o que vai fazer
python3 install.py cookcli --apply
```

Só na rede local, `--access local`; na tailnet e na LAN, `--access
both`. Acrescentar `--href-local` faz o link do dashboard apontar pra LAN. O script cria os diretórios, grava o
`.env`, gera os secrets, ajusta o dono dos volumes, sobe o serviço e
imprime o endereço no fim — ver
[Instalando e operando](../../docs/pt-BR/instalacao.md) no README
raiz.

Acessar `http://<ip-do-host>:9080` (ou via [tsdproxy](../tsdproxy/README.pt-BR.md) em
`https://cookcli.<your-tailnet>.ts.net`).

<details>
<summary><b>Instalação manual</b> (avançado) — os mesmos passos, um a um</summary>


```bash
# 1. Baixar a unit (sem precisar clonar o repositório)
mkdir -p ~/.config/containers/systemd
wget -P ~/.config/containers/systemd/ \
  https://raw.githubusercontent.com/wallacepnts/quadlet-homelab/main/apps/cookcli/cookcli.container

# 2. A pasta das receitas. NÃO fazer chown aqui: ela é sua, e o keep-id da
#    unit é justamente o que faz o container aceitar isso.
mkdir -p ~/.config/containers/volumes/cookcli/recipes

# 3. Subir
systemctl --user daemon-reload
systemctl --user start cookcli
```

Acessar `http://<ip-do-host>:9080` (ou via [tsdproxy](../tsdproxy/README.pt-BR.md) em
`https://cookcli.<your-tailnet>.ts.net`).

</details>

## Escrevendo receitas

Um arquivo `.cook` por receita, dentro de `recipes/`. Subpasta vira
categoria. O servidor recarrega sozinho — não precisa reiniciar.

```bash
cat > ~/.config/containers/volumes/cookcli/recipes/pao-de-queijo.cook <<'EOF'
---
title: Pão de queijo
servings: 12
---

Misture @polvilho azedo{500%g} com @queijo meia-cura ralado{300%g}.
Asse por ~{25%minutos} no #forno{} a 200°C.
EOF
```

`@ingrediente{quantidade%unidade}`, `#equipamento{}`, `~{tempo}`. A
sintaxe inteira está na [especificação](https://cooklang.org/docs/spec/).

**Versionar em git é o uso natural**: a pasta é só texto.

## Fotos nas receitas

Por **convenção de nome**, sem nada a configurar: a imagem tem o mesmo
nome do arquivo `.cook`, na mesma pasta.

```
recipes/
├── bolo.cook
├── bolo.jpg        ← vira a foto do bolo
├── pao-de-queijo.cook
└── pao-de-queijo.png
```

Extensões que funcionam, testadas nesta versão: **`.jpg`, `.jpeg`,
`.png`, `.webp`**. O `.gif` é ignorado em silêncio — a receita aparece sem
foto e nada acusa.

Não precisa reiniciar: solte o arquivo na pasta e recarregue a página. A
imagem passa a ser servida em `/api/static/<nome>.<ext>`.

**Uma foto por receita.** Testei a convenção de imagem por passo
(`bolo.0.jpg`, `bolo.1.jpg`) e esta versão do servidor **não a expõe** —
os arquivos ficam na pasta sem aparecer, e o campo de imagem da receita
volta vazio. Se quiser ilustrar passos, o caminho é embutir a imagem no
texto da receita como Markdown.

## O que mais cabe numa receita

Testado nesta versão contra a instância rodando — a
[lista canônica da spec](https://github.com/cooklang/spec/blob/main/proposals/0007-canonical-metadata.md)
tem 16 campos, e **a interface mostra 12**:

| Aparece na página | Aceito mas **não** exibido |
| --- | --- |
| `description`, `author`, `source`, `course`, `cuisine`, `difficulty`, `tags`, `servings`, `prep time`, `cook time` | `introduction`, `diet`, `time required`, `locale` |

Os quatro da direita não somem — voltam na API, então servem pra
organização e pra ferramenta externa. Só não têm lugar na tela. Repare que
`time required` é ignorado quando existem `prep time` e `cook time`.

Além dos metadados, duas construções da própria sintaxe rendem bastante:

- **Seções**: `== Preparo ==` quebra a receita em blocos com título.
- **Notas**: linha começando com `>` vira um bloco destacado, fora da
  lista de passos — bom pra dica, substituição de ingrediente, aviso.

O [`bolo-de-cenoura.cook.example`](./bolo-de-cenoura.cook.example) deste
diretório usa **todos** os recursos da sintaxe de uma vez, e o
[`calda-de-chocolate.cook.example`](./calda-de-chocolate.cook.example)
existe pra demonstrar a referência entre receitas. Ver "A receita de
referência" abaixo.

### A receita de referência

O `bolo-de-cenoura.cook.example` exercita a spec inteira. Cada linha dele
foi verificada contra a API desta versão:

| Recurso | Sintaxe |
| --- | --- |
| ingrediente com nome composto | `@farinha de trigo{}` |
| quantidade e unidade | `@óleo{200%ml}` |
| **preparo curto** | `@cenoura{3}(média, em rodelas)` |
| utensílio | `#liquidificador{}` |
| **timer nomeado** | `~forno{40%minutos}` |
| seção | `= Massa`, `== Forno ==` |
| nota | linha iniciada por `>` |
| comentário de linha | `-- some da página` |
| comentário em bloco | `[- também some -]` |
| quebra de linha dentro do passo | barra invertida no fim da linha |
| **referência a outra receita** | `@./molhos/calda-de-chocolate{200%ml}` |

Dois que valem destaque porque não são óbvios:

**O preparo curto vai pra lista de ingredientes, não pro texto.** Escrever
`@cenoura{3}(média, em rodelas)` faz o "(média, em rodelas)" aparecer ao
lado da cenoura na lista — é o que permite deixar tudo picado antes de
começar.

**A referência entre receitas soma na lista de compras.** O bolo referencia
a calda, e a lista de compras dele traz chocolate e creme de leite, que só
existem na calda:

```
[hortifruti]   cenoura        3
[laticínios]   creme de leite 50 ml
               ovo            3
[mercearia]    chocolate      150 g
               fermento em pó 1 colher de sopa
               óleo           200 ml
```

Farinha, açúcar e manteiga não aparecem porque estão no `pantry.conf`. A
referência aceita `{2}` (dobra a receita inteira), `{4%servings}` (lê o
`servings` do destino) e `{200%ml}` (lê o `yield`) — a calda declara
`yield: 200%ml` justamente pra isso.

**Escala funciona no arquivo inteiro**: `cook recipe read bolo-de-cenoura.cook:2`
dobra tudo, inclusive o que vem da receita referenciada.

### Cardápios: arquivos `.menu`

Um `.menu` é um arquivo Cooklang que usa **seções como dias** e
referências pra puxar as receitas. O
[`semana.menu.example`](./semana.menu.example) deste diretório é um.

```cooklang
---
title: Cardápio da semana
servings: 4
---

== Segunda (2026-08-10) ==

@./cafe-com-leite{2}
@./bolo-de-cenoura{4%servings}

== Terça (2026-08-11) ==

@./bolo{1}
```

A data entre parênteses em `YYYY-MM-DD` é reconhecida — a API devolve um
campo `date` separado, e aplicações usam isso pra destacar o dia de hoje.

O ganho de verdade é a lista de compras da semana inteira, somando tudo e
já descontando a despensa:

```bash
podman exec cookcli sh -c 'cd /recipes && cook shopping-list semana.menu'
```

**Onde ele aparece**: não há rota `/menus` na interface — o `.menu` entra
na lista junto das receitas e abre em `/recipe/<nome>`, renderizando os
dias, as datas e as referências com a escala. A API tem rota própria
(`/api/menus`), mas a UI não.

### Duas armadilhas de referência entre receitas

**1. A referência usa o NOME DO ARQUIVO, não o título.** Escrever
`@./bolo simples{1}` pra uma receita cujo arquivo é `bolo.cook` falha com
`Invalid recipe path: bolo simples`. Pior: **a interface renderiza o
cardápio normalmente**, mostrando "bolo simples (×1)" — só a lista de
compras acusa.

**2. Não use unidade na referência: use `{N}` ou `{N%servings}`.** O
`yield` não é suportado nesta versão — a própria calda gera
`Unsupported value for key: 'yield'`. E o pior é a inconsistência: a mesma
referência `@./molhos/calda-de-chocolate{200%ml}` resolve como **×1**
quando a lista sai da receita, e como **×200** quando sai de um cardápio
que referencia essa receita. Descobri isso porque a lista da semana pediu
**15 kg de chocolate**.

Com `{1}`, os números fecham: a lista da semana pede 225 g de chocolate —
150 g da calda referenciada direto no cardápio, mais 75 g do bolo, que
entra em meia receita por causa do `{4%servings}` contra os `servings: 8`
dele.

### Vídeo e foto de ingrediente: não dá

Três coisas que **não** existem, todas verificadas:

- **Vídeo não tem campo nem convenção.** Um `receita.mp4` ao lado do
  `.cook` fica na pasta sem ser referenciado — apesar de ser *servido* em
  `/api/static/receita.mp4`, porque a pasta inteira é estática. Ou seja: o
  arquivo é alcançável por URL, mas nada na interface aponta pra ele.
- **Foto por ingrediente não existe** na spec nem no servidor.
- **Markdown e HTML no texto do passo não são renderizados.** Testei
  `![foto](...)`, `[link](...)` e `<img src=...>`: os três aparecem como
  texto puro na página. Então não dá pra contornar embutindo mídia no
  passo.

Some-se a isso o que já estava documentado: **imagem por passo**
(`bolo.0.jpg`) também não é exposta. Na prática, o CookCLI aceita **uma
foto por receita** e mais nada de mídia.

### `image:` no metadado ganha do arquivo

Se a receita tiver `image: https://...` no frontmatter, esse valor
**substitui** a convenção de arquivo — mesmo existindo um `receita.jpg` na
pasta, é a URL que vale. Útil pra apontar pra foto hospedada em outro
lugar; traiçoeiro se você largar a URL lá e depois não entender por que o
arquivo local é ignorado.

## Lista de compras: `aisle.conf` e `pantry.conf`

Dois arquivos opcionais em `recipes/config/` que transformam a lista de
compras de "despejo de ingredientes" em algo utilizável:

| Arquivo | Faz |
| --- | --- |
| `aisle.conf` | agrupa por seção do mercado, na ordem em que você anda pelos corredores |
| `pantry.conf` | o que você já tem em casa — o CookCLI **subtrai** da lista |

```bash
mkdir -p ~/.config/containers/volumes/cookcli/recipes/config
wget -O ~/.config/containers/volumes/cookcli/recipes/config/aisle.conf \
  https://raw.githubusercontent.com/wallacepnts/quadlet-homelab/main/apps/cookcli/aisle.conf.example
wget -O ~/.config/containers/volumes/cookcli/recipes/config/pantry.conf \
  https://raw.githubusercontent.com/wallacepnts/quadlet-homelab/main/apps/cookcli/pantry.conf.example
```

Não precisa reiniciar — o servidor relê os dois. Conferir com:

```bash
podman exec cookcli sh -c 'cd /recipes && cook doctor'
```

### A quarta, e a que engana mais: `WorkingDir`

Se a página **Preferences** disser

```
Aisle Configuration: Not configured
Pantry Configuration: Not configured
```

os arquivos estão lá e o servidor está olhando no lugar errado. O cookcli
procura `./config/` **relativo ao diretório de trabalho do processo**, não
à pasta de receitas — e o do container é `/`, então ele olha em `/config`.
A unit resolve com `WorkingDir=/recipes`.

O que torna isso traiçoeiro é o silêncio: nada falha, o servidor sobe
normal, a lista de compras só sai sem categoria e sem descontar a
despensa. E o `cook doctor` **não** reproduz o problema, porque você o
roda com `cd /recipes` — foi exatamente assim que eu validei os arquivos e
achei que estava tudo certo.

### Três armadilhas, todas encontradas testando

**1. `aisle.conf` não aceita comentário.** Não é TOML nem INI: é um
formato próprio, e toda linha fora de uma seção `[...]` é lida como
ingrediente. Um cabeçalho com `#` vira
`Ingredient found before any category`, uma vez por linha. Por isso o
`aisle.conf.example` daqui começa direto no `[hortifruti]`, com a
explicação neste README.

**2. `pantry.conf` é TOML, e acento quebra.** Nome de seção ou de item com
acento ou espaço **precisa de aspas** — `[armário]` derruba o arquivo
inteiro com `Failed to parse pantry file`, e a lista sai como se você não
tivesse nada em casa. Use `[armario]` sem acento na seção, e
`"açúcar" = ...` com aspas no item.

**3. A unidade precisa bater pra subtração acontecer.** Receita pedindo
`300%g` de farinha com a despensa dizendo `1%kg` gera
`Unit mismatch for 'farinha de trigo'` e o item **continua na lista**. Por
isso o exemplo guarda farinha e açúcar em `g`, não em `kg`.

Com os dois no lugar, uma receita de bolo que pede farinha, açúcar, ovos,
manteiga e fermento produz só o que falta:

```
[laticínios]
ovo            3
[other]
fermento em pó 10 g
```

### Sintaxe das receitas: use frontmatter

O `>>` para metadados **está deprecado** — o CookCLI avisa
`The '>>' syntax for metadata is deprecated, use a YAML frontmatter`.
Escrever assim:

```cook
---
title: Bolo simples
servings: 8
---

Misture @farinha de trigo{300%g} com @açúcar{200%g} e @ovos{3}.
```

## Segurança

**Não tem autenticação.** Quem alcança a porta lê e edita as receitas pela
UI. Na tailnet isso é aceitável; para colocar login na frente, o caminho é
o [Authentik](../authentik/README.pt-BR.md).

## Auto-update

Sem `AutoUpdate=` — tag explícita (`0.32.1`), bump manual (regra 9 do
convenções). O post oficial de self-hosting ainda cita a `0.23.0`, bem
atrás — conferir sempre a página de releases, não o tutorial.

## Backup & Recuperação

```bash
tar -czf cookcli-backup-$(date +%Y%m%d-%H%M%S).tar.gz \
  -C ~/.config/containers/volumes cookcli
```

Nem precisa parar o serviço: são arquivos de texto que o servidor só lê.
Se a pasta estiver em git, o backup já é o `push`.

## Comandos úteis

```bash
systemctl --user status cookcli
podman logs -f cookcli
podman exec cookcli cook recipe read /recipes/pao-de-queijo.cook
```

## Créditos

Deploy Quadlet baseado no [CookCLI](https://github.com/cooklang/cookcli)
do projeto [CookLang](https://cooklang.org) (MIT).
