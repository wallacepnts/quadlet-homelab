# O manifesto do app: `apps/<app>/app.json`

Tudo o que um app diz de si mesmo mora num arquivo só, ao lado das units. É o modelo da
[loja de apps do CasaOS](https://github.com/IceWhaleTech/CasaOS-AppStore) — lá um app é um arquivo compose com
um bloco `x-casaos` que guarda os metadados —, num JSON nosso, ao lado das units do Quadlet em vez de dentro
delas.

Uma pasta é, portanto, as units, o `.env.example` se houver, este arquivo e o logo. Não há README por app, nem
`install.ini`: a tabela de serviços dos READMEs raiz é gerada a partir dos manifestos, e o painel
mostra as notas. As descrições e as notas são escritas em inglês e português.

```json
{
  "title": "Memos",
  "short_desc": { "en": "Quick notes.", "pt": "Notas rápidas." },
  "description": { "en": "…", "pt": "…" },
  "author": "usememos",
  "source": "https://github.com/usememos/memos",
  "docs": "https://www.usememos.com/docs",
  "category": "Productivity",
  "units": { "memos": { "upstream": "usememos/memos" } }
}
```

e, ao lado, o logo e as capturas de tela como arquivos comuns:

```
apps/memos/
├── memos.container
├── app.json
├── notes.en.md              # só para app que precisa: o que fazer primeiro, e o notes.pt.md ao lado
├── icon.svg                 # o logo: icon.svg, .png, .webp ou .jpg, até 512 KB
└── screenshots/             # opcional: 1.png, 2.png ... até seis, até 1 MB cada
```

## As notas

`notes.en.md` e `notes.pt.md` guardam o que a pessoa precisa fazer no primeiro acesso, ou o que pode machucá-la: desligar o
cadastro, trocar uma senha padrão, uma biblioteca que precisa ser posta no lugar. **Só um app que precisa tem**, sempre nos
dois idiomas, com até 2.500 caracteres cada (o `check.py` confere os dois). O que for maior, ou sobre como a unit é feita,
vai em `docs/` (o endurecimento medido está em `docs/hardening.md`). O painel mostra na tela do app.

## Os campos

| Campo | Obrigatório | Significado |
| --- | --- | --- |
| `title` | sim | O nome mostrado na loja e na tabela de serviços. |
| `short_desc` | sim | `{en, pt}`: uma frase curta e simples em cada idioma, até 70 caracteres, sem travessão nem parênteses (*Um servidor de mídia para a sua coleção.*). É a descrição na tabela e no cartão. Ressalvas vão nas notas. |
| `description` | sim | `{en, pt}`: o que o app é, em poucas linhas. O painel mostra ao abrir o app. |
| `author` | não | Quem faz o projeto (o dono de `source`). |
| `source` | não | O repositório do projeto, uma URL https. O painel o liga, e as issues e releases vêm dele. |
| `website` | não | A página do projeto, uma URL https. |
| `docs` | não | A documentação do projeto, uma URL https. |
| `architectures` | não | `["amd64", "arm64"]`: onde a imagem roda, quando se sabe (o painel também pergunta ao registry). |
| `category` | não | Um dos grupos de `qhui.GRUPOS` (as categorias da loja). Infraestrutura sem lugar entre elas (homepage, postfix, toolbx) não tem. |
| `min_podman` | não | `"6.1"`: um piso acima da 6.0 que todo app já exige, para uma unit que usa uma chave Quadlet mais nova. Nunca abaixo da 6.0 (o `check.py` recusa). |
| `requires_https` | não | `true`: o app quebra em HTTP puro (um cofre, um service worker). O painel avisa quando ele é acessado só pela rede local. |
| `no_gui` | não | `true`: o app não tem interface web (um runner, um relay de e-mail, uma caixa de ferramentas); a loja não mostra endereço nem o botão Abrir, qualquer que seja a porta que ele publica. |
| `deprecated` | não | Texto: por que foi descontinuado. A loja não oferece instalar. |
| `secrets` | por `Secret=` | `{"<secret>": "rand-hex 32"}`: como cada secret é feito (`rand-hex N`, `rand-base64 N`, `rand-urlsafe N`, `rand-alnum N`, `shell <cmd>`, `manual <texto>`). |
| `validate` | não | `{"<secret>": "shell <cmd>"}`: uma conferência de um secret `manual` que só o outro lado sabe julgar. O valor chega por stdin. |
| `config` | não | `{"<arquivo na pasta>": "<onde cai no host>"}`: arquivos auxiliares que o `qh` copia uma vez e nunca sobrescreve. |
| `vars` | por `${VAR}` em `Volume=` | `{"MEDIA_DATA_DIR": "~/data"}`: as variáveis do systemd que uma unit usa, e o padrão que a instalação oferece. |
| `ask` | não | `{"<segredo manual ou nome de vars>": {"type": "password", "label": {"en": "…", "pt": "…"}, "hint": "…", "min": 12, "max": 64, "regex": "…", "pattern_error": "…", "required": true}}`: como o formulário de instalação pergunta, como o `form_fields` do Runtipi. `type` é `text` (padrão), `password`, `email`, `number`, `url` ou `path`; `label`, `hint`, `placeholder` e `pattern_error` são um texto ou um par `{en, pt}`; `min`/`max` são um tamanho (uma faixa em `number`); `regex` precisa casar o valor inteiro. O navegador confere enquanto se digita e o servidor confere de novo antes de instalar. |
| `login` | não | `{"user": "admin", "password": "<secret>"}`, ou `{"credentials": "<secret>"}` quando um secret guarda `usuário:senha`: o que a instalação imprime. |
| `choices` | não | `{"VERSION": {"question": "…", "options": [{"value": "11", "label": "Windows 11"}, "10"]}}`: uma escolha numa lista fechada que só importa na primeira instalação. Uma opção é `{value, label}` ou só o valor. A primeira é o padrão. |
| `options` | não | `{"database": {"question": "…", "default": "sqlite", "values": {"sqlite": {"label": "SQLite"}, "postgres": {"label": "PostgreSQL", "units": ["app-postgres"], "env": {"DB_HOST": "…"}, "secrets": ["app-db-password"]}}}}`: uma escolha que o desenvolvedor oferece na primeira instalação. Um valor cita as `units` opcionais que liga, as variáveis `env` que acrescenta ao `.env` e os `secrets` de que precisa (cada um com receita em `secrets`). Uma unit que nenhum valor cita fica sempre ligada. No mínimo dois valores; `default` é um deles. |
| `widgets` | não | `[{"type": "immich"}, {"type": "sonarr", "unit": "media-stack-sonarr"}]`: alguns números de dentro do app, mostrados no azulejo e no painel dele (fotos no Immich, consultas bloqueadas no AdGuard…). `type` é um que a loja sabe ler (`svcwidgets.TYPES`: immich, adguard, paperless, uptime-kuma, sonarr, radarr, jellyfin); `unit` só numa pasta de vários. A chave de cada um é digitada no painel e fica no servidor, nunca no manifesto. |
| `icon` | não | `{"bg": "#12352a", "fit": 1.2, "tone": "dark"}`: como o logo fica na placa dele no painel, cada chave opcional. `bg` é a cor da placa (para um logo que não aparece na automática); `fit` (0,8 a 1,4) escala o logo, que o painel mede sozinho se faltar; `tone` é `light`, `color`, `dark` ou `full` (o logo preenche a placa). |
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
