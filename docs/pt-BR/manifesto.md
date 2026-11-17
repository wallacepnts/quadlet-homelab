# O manifesto do app: `apps/<app>/app.json`

Tudo o que um app diz de si mesmo mora num arquivo só, ao lado das units. É o modelo da
[loja de apps do CasaOS](https://github.com/IceWhaleTech/CasaOS-AppStore) — lá um app é um arquivo compose com
um bloco `x-casaos` que guarda os metadados —, num JSON nosso, ao lado das units do Quadlet em vez de dentro
delas.

Uma pasta é, portanto, as units, o `.env.example` se houver, este arquivo e o logo. Não há README por app, nem
`install.ini`, nem `notes.md`: a tabela de serviços dos READMEs raiz é gerada a partir dos manifestos, e o painel
mostra as notas. As descrições são escritas em inglês e português; as notas, uma vez, em inglês.

```json
{
  "title": "Memos",
  "short_desc": { "en": "Quick notes.", "pt": "Notas rápidas." },
  "description": { "en": "…", "pt": "…" },
  "author": "usememos",
  "source": "https://github.com/usememos/memos",
  "docs": "https://www.usememos.com/docs",
  "category": "Productivity",
  "notes": "The first user to sign up becomes admin…",
  "units": { "memos": { "upstream": "usememos/memos" } }
}
```

e, ao lado, o logo e as capturas de tela como arquivos comuns:

```
apps/memos/
├── memos.container
├── app.json
├── icon.svg                 # o logo: icon.svg, .png, .webp ou .jpg, até 512 KB
└── screenshots/             # opcional: 1.png, 2.png ... até seis, até 1 MB cada
```

## Os campos

| Campo | Obrigatório | Significado |
| --- | --- | --- |
| `title` | sim | O nome mostrado na loja e na tabela de serviços. |
| `short_desc` | sim | `{en, pt}`: uma frase curta e simples em cada idioma, até 70 caracteres, sem travessão nem parênteses (*Um servidor de mídia para a sua coleção.*). É a descrição na tabela e no cartão. Ressalvas vão em `notes`. |
| `description` | sim | `{en, pt}`: o que o app é, em poucas linhas. O painel mostra ao abrir o app. |
| `author` | não | Quem faz o projeto (o dono de `source`). |
| `source` | não | O repositório do projeto, uma URL https. O painel o liga, e as issues e releases vêm dele. |
| `website` | não | A página do projeto, uma URL https. |
| `docs` | não | A documentação do projeto, uma URL https. |
| `architectures` | não | `["amd64", "arm64"]`: onde a imagem roda, quando se sabe (o painel também pergunta ao registry). |
| `category` | não | Um dos grupos de `qhui.GRUPOS` (as categorias da loja). Infraestrutura sem lugar entre elas (homepage, postfix, toolbx) não tem. |
| `min_podman` | não | `"5.4"`: um piso acima do 5.0 que o `Notify=healthy` já exige. |
| `deprecated` | não | Texto: por que foi descontinuado. A loja não oferece instalar. |
| `notes` | não | Markdown: o que fazer no primeiro acesso e o que o app tem de estranho. O painel mostra. |
| `secrets` | por `Secret=` | `{"<secret>": "rand-hex 32"}`: como cada secret é feito (`rand-hex N`, `rand-base64 N`, `rand-urlsafe N`, `rand-alnum N`, `shell <cmd>`, `manual <texto>`). |
| `validate` | não | `{"<secret>": "shell <cmd>"}`: uma conferência de um secret `manual` que só o outro lado sabe julgar. O valor chega por stdin. |
| `config` | não | `{"<arquivo na pasta>": "<onde cai no host>"}`: arquivos auxiliares que o `qh` copia uma vez e nunca sobrescreve. |
| `vars` | por `${VAR}` em `Volume=` | `{"MEDIA_DATA_DIR": "~/data"}`: as variáveis do systemd que uma unit usa, e o padrão que a instalação oferece. |
| `login` | não | `{"user": "admin", "password": "<secret>"}`, ou `{"credentials": "<secret>"}` quando um secret guarda `usuário:senha`: o que a instalação imprime. |
| `choices` | não | `{"VERSION": {"question": "…", "options": [{"value": "11", "label": "Windows 11"}, "10"]}}`: uma escolha numa lista fechada que só importa na primeira instalação. Uma opção é `{value, label}` ou só o valor. A primeira é o padrão. |
| `backup` | não | `{"mode": "stop", "exclude": ["upload/thumbs"]}`: parar o serviço durante a cópia, e as pastas que se refazem sozinhas. |
| `units` | não | Por unit, abaixo. |

## `units`

Uma entrada por `.container` que precise, com a chave sendo o basename da unit:

| Campo | Significado |
| --- | --- |
| `upstream` | De onde vem a versão dela: `owner/repo` (uma release do GitHub), `registry:<regex>`, `compose:<owner>/<repo>:<arquivo>` (um apoio fixado no que o compose do app valida), ou `-` (nada comparável). Omitido, é derivado do nome da imagem onde a convenção vale (`ghcr.io/<org>/<repo>`, `docker.io/<org>/<repo>`). |
| `image` | O formato da tag quando não é só a versão: `v{version}`, `{version}-alpine`, `{version:2}`. Uma unit cujo `Image=` **não tem tag** acompanha uma release, o `qh` fixa a última release no host (veja [auto-update](./auto-update.md)), e o formato é `{version}` a menos que isto diga outro. |
| `login`, `choices` | Como acima, para uma pasta de serviços independentes que não dividem um só. |

## Gerado, não escrito

A tabela de serviços do `README.md` e do `docs/pt-BR/README.md`, entre os marcadores `services:begin` e
`services:end`, vem de `title`, do arquivo do logo e de `short_desc` (a tabela em português usa o `pt`). O `python3 check.py --readme` a reescreve, e o
`check.py` reprova quando ela está desatualizada.

## O que o formato do CasaOS tem e este não

O CasaOS traz `developer`, `tips.before_install`, `port_map`, `index`, `scheme`,
`thumbnail`, `release_notes`, e uma descrição para cada porta,
volume e variável de ambiente. Aqui as arquiteturas vêm do registry, a porta e o endereço das units, as notas de
versão do GitHub, e as notas cobrem as `tips`. A licença ficou de fora de propósito, e os comentários
também: o porquê de uma receita ter a forma que tem pertence a `docs/`, não ao manifesto.

## Conferir

O `python3 check.py` valida cada manifesto: os campos obrigatórios, o arquivo do logo, a
categoria, o formato de cada objeto, uma chave desconhecida no topo (um erro de digitação), e as regras de cada
parte (uma receita para cada `Secret=`, um `login` que cita um secret de verdade, um padrão em `vars` para cada
`${VAR}` num `Volume=`, o formato para cada unit sem tag). O `python3 manifest.py --selftest` testa o leitor.
