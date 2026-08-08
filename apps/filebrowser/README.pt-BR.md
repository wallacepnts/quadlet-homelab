# FileBrowser Quantum — Podman Quadlet (rootless)

**[🇺🇸 Read in English](./README.md)**

Deploy do [gtsteffaniak/filebrowser](https://github.com/gtsteffaniak/filebrowser)
via Podman Quadlet, usando a imagem oficial
`ghcr.io/gtsteffaniak/filebrowser`.

Um gerenciador de arquivos web sobre um diretório que você escolhe: navegar,
buscar, pré-visualizar, renomear, subir, baixar, compartilhar por link e editar
texto ali mesmo. O Quantum é uma reescrita do filebrowser/filebrowser original,
com índice de busca de verdade, prévias de mídia e configuração por fonte.

## Pra que serve, ao lado do [copyparty](../copyparty/)

Os dois colocam um diretório no navegador, e não são a mesma ferramenta:

- **copyparty** é a ponta de *transferência* — upload retomável, dedup, um
  ponto de entrega pra quem não é você.
- **FileBrowser** é o *gerenciador* — busca indexada na árvore inteira,
  miniaturas, editor, WebDAV e compartilhamentos.

Rodar os dois faz sentido. Apontar os dois pro mesmo diretório também faz —
eles não brigam por ele —, mas só um dos dois deve ser o que você entrega pras
outras pessoas.

## Arquitetura

Um container só, dois volumes:

| Volume | Guarda |
| --- | --- |
| `/home/filebrowser/data` | `config.yaml`, `database.db`, o cache de miniaturas |
| `/srv` | os arquivos que ele gerencia — os seus vão aqui |

A porta **8014** do host mapeia pra **8080** lá dentro. Essa porta interna não é
a padrão do upstream, e o motivo importa — ver abaixo.

## Três coisas que foram medidas, e por isso a unit é assim

Nenhuma delas aparece no compose do upstream. Cada uma veio de um start que
falhou.

**`UserNS=keep-id` é obrigatório.** A imagem roda com uid 1000 fixo e nunca faz
`chown`. Sem o keep-id os bind mounts pertencem a um subuid, e o app não
consegue abrir o banco que ele mesmo acabou de criar:

```
[FATAL] could not open database: open /home/filebrowser/data/database.db: permission denied
```

**A porta interna teve que sair da 80.** O upstream escuta na 80. Sob keep-id o
processo também roda com o seu uid sem privilégio dentro do namespace, então
não consegue abrir porta abaixo de 1024:

```
[FATAL] Server error: listen tcp 0.0.0.0:80: bind: permission denied
```

O `server.port` do config publicado aqui é `8080` por isso, e o healthcheck, a
label do tsdproxy e o `PublishPort` seguem ele. Mudar um significa mudar os
quatro.

**Faltar o `config.yaml` é fatal, não é aviso.** O app lê a config de *dentro*
do diretório de dados, não de onde a imagem deixa o modelo dela:

```
[FATAL] config file /home/filebrowser/data/config.yaml does not exist, please
create it or set the FILEBROWSER_CONFIG environment variable to a valid config
file path
```

É por isso que o `install.ini` copia o `config.yaml.example` pro volume. O
caminho não dá pra deduzir da unit, então está escrito lá explicitamente.

## Entrando

O usuário é **`admin`** e não é configurável por variável de ambiente — só pelo
`auth.adminUsername` no `config.yaml`. A senha vem do secret
`filebrowser-admin-password`:

```bash
podman secret inspect --showsecret filebrowser-admin-password
```

O segundo secret, `filebrowser-jwt-secret`, assina o cookie de sessão. Ele
serve pra alguma coisa em vez de ser decoração, e isso foi medido: com ele, a
sessão sobrevive a um `systemctl --user restart filebrowser`; sem ele o app
gera uma chave nova a cada start e todo mundo é deslogado.

Rotacionar ele de propósito é a forma de derrubar todas as sessões de uma vez.

<details>
<summary><b>Se você for scriptar contra a API</b> — a chamada de login não é o que se imagina</summary>


O endpoint de login recebe o usuário na query string e a senha num **header
`X-Password`**, URL-encoded. Um corpo JSON é recusado em silêncio com `401`,
que se parece exatamente com senha errada:

```bash
curl -c jar -X POST 'http://127.0.0.1:8014/api/auth/login?username=admin' \
  -H "X-Password: $(podman secret inspect --showsecret --format '{{.SecretData}}' filebrowser-admin-password)"
curl -b jar 'http://127.0.0.1:8014/api/users?id=self'
```

O cookie de sessão é o `_quantum_jwt`.

</details>

## Arquivos

```
filebrowser.container   # unit principal
config.yaml.example     # o config do upstream, com duas linhas alteradas
.env.example            # onde o app procura esse config
install.ini             # as duas receitas de secret + o override de upstream
```

O `config.yaml.example` é o padrão publicado pelo upstream com exatamente duas
edições: `server.port` `80` → `8080`, e um `server.cacheDir` apontando pro
volume de dados. As duas estão explicadas acima e na seção de Hardening. Todo o
resto — a fonte `/srv`, os métodos de autenticação, os padrões de usuário — é do
upstream, então vale um diff a cada bump de versão.

## Instalação

```bash
python3 install.py filebrowser            # dry-run: mostra o que vai fazer
python3 install.py filebrowser --apply
```

Depois é colocar arquivos em
`~/.config/containers/volumes/filebrowser/files/` e abrir
`https://filebrowser.<your-tailnet>.ts.net`.

<details>
<summary><b>Instalação manual</b> (avançado) — os mesmos passos, um a um</summary>


```bash
# 1. Baixar a unit (sem precisar clonar o repositório)
mkdir -p ~/.config/containers/systemd
wget -P ~/.config/containers/systemd/ \
  https://raw.githubusercontent.com/wallacepnts/quadlet-homelab/main/apps/filebrowser/filebrowser.container

# 2. Diretórios
mkdir -p ~/.config/containers/volumes/filebrowser/{data,files}
mkdir -p ~/.config/containers/env

# 3. O config — o app não sobe sem ele
wget -O ~/.config/containers/volumes/filebrowser/data/config.yaml \
  https://raw.githubusercontent.com/wallacepnts/quadlet-homelab/main/apps/filebrowser/config.yaml.example

# 4. Ambiente
wget -O ~/.config/containers/env/filebrowser.env \
  https://raw.githubusercontent.com/wallacepnts/quadlet-homelab/main/apps/filebrowser/.env.example

# 5. Secrets
podman secret create filebrowser-admin-password - <<< "$(python3 -c 'import secrets,string;a=string.ascii_letters+string.digits;print("".join(secrets.choice(a) for _ in range(20)))')"
podman secret create filebrowser-jwt-secret - <<< "$(python3 -c 'import secrets;print(secrets.token_hex(32))')"

# 6. Subir
systemctl --user daemon-reload
systemctl --user start filebrowser
```

</details>

## Adicionando mais diretórios

O config publicado aqui declara uma fonte só, `/srv`. Pra expor outro
diretório, acrescente um `Volume=` na unit e uma entrada correspondente em
`server.sources`:

```ini
Volume=%h/Documentos:/docs:Z
```

```yaml
server:
  sources:
    - path: "/srv"
    - path: "/docs"
```

Cada fonte ganha o próprio índice, então uma árvore grande custa memória e uma
varredura na primeira execução. Acompanhe o `podman logs filebrowser` pelo
`initializing index` pra ver quando termina.

## Segurança

**Está na tailnet por padrão**, e diferente da maioria das coisas daqui ele
também tem um login próprio de verdade. Essa é a forma certa pra este serviço:
ele entrega acesso de leitura *e escrita* a uma árvore de diretórios, e os
compartilhamentos geram links que funcionam pra quem tiver o link.

Se essa troca não for o que você quer, instalar com `--access local` — as
labels do tsdproxy são comentadas em vez de apagadas, então mudar de ideia
depois é um `--update` com outro modo
([Instalando e operando](../../docs/pt-BR/instalacao.md)).

Vale saber: o `/srv` é o mundo inteiro do app, e é um bind mount de um diretório
na sua home. Ele não escapa desse mount, mas tudo que está lá dentro é
totalmente gravável, inclusive apagável. Aponte pra um diretório que você
aceite perder, ou mantenha backup.

## Hardening

A escada inteira da [regra 20](../../docs/pt-BR/convencoes.md) se sustenta
aqui, o que é incomum — a maioria das imagens desiste um degrau antes.

| Ajuste | Situação |
| --- | --- |
| `NoNewPrivileges=true`, `PidsLimit=256` | aplicados, sem precisar medir |
| `DropCapability=ALL` | **funciona** — medido: `200` no `/health`, login e upload ok |
| `ReadOnly=true` + `Tmpfs=/tmp:size=64M` | **funciona, depois de mover o `cacheDir`** — ver abaixo |
| `UserNS=keep-id` | **obrigatório**, e não é hardening — é o que torna os volumes graváveis |
| `User=` | **desnecessário** — a imagem já roda com uid não-root |

O `ReadOnly=true` falha com o config do upstream, porque o `cacheDir` dele é o
caminho *relativo* `tmp`, que cai dentro da imagem somente-leitura:

```
[FATAL] cacheDir failed to create cache directory: mkdir tmp: read-only file system
```

Apontar pra `/home/filebrowser/data/cache` resolve e ainda é melhor: as
miniaturas sobrevivem a um restart em vez de serem geradas de novo. Essa é a
segunda das duas edições no `config.yaml.example`.

O `Tmpfs=/tmp` fica mesmo com o cache tendo saído de lá — a geração de prévia
escreve arquivos transitórios pelo diretório temporário padrão do Go. 64M dá
conta disso; se você for pré-visualizar vídeo grande, meça com
`podman exec filebrowser df -h /tmp` antes de aumentar.

**O teste que vale é exercitar o app, não ver o container rodando.** Cada
degrau acima foi conferido com um login, uma listagem de diretório e um upload
— o `/health` sozinho responde `200` num container em que toda operação de
arquivo está falhando.

## Auto-update

Sem `AutoUpdate=` — tag explícita (`1.5.1-stable`), bump na mão
([regra 9](../../docs/pt-BR/convencoes.md)). Dois motivos pra manter manual
aqui: o `config.yaml` é versionado neste repositório, então uma mudança de
schema do upstream pede um diff e não um restart, e o índice de busca é
reconstruído quando o formato dele muda.

A label `wud.tag.include` filtra pelas tags `-stable`, porque o registry também
carrega `-beta` e builds por commit que ordenam como mais novos.

O `install.ini` carrega um override de `[upstream]`: a imagem é
`gtsteffaniak/filebrowser`, e sem essa linha o `updates.py` procuraria releases
no nome errado.

## Backup & recuperação

```bash
systemctl --user stop filebrowser
tar -czf filebrowser-backup-$(date +%Y%m%d-%H%M%S).tar.gz \
  -C ~/.config/containers/volumes filebrowser
systemctl --user start filebrowser
```

A frio de propósito: o `database.db` é um banco vivo com usuários,
compartilhamentos e configurações, e copiar com o app escrevendo dá um arquivo
que só se revela corrompido na hora de restaurar.

Pra guardar só os metadados e não os arquivos em si — costuma ser bem menor, e
os arquivos provavelmente já têm backup em outro lugar:

```bash
tar -czf filebrowser-data-$(date +%Y%m%d-%H%M%S).tar.gz \
  -C ~/.config/containers/volumes/filebrowser data
```

O cache de miniaturas vai junto e é regenerável; excluir com
`--exclude=data/cache` está ok.

## Comandos úteis

```bash
systemctl --user status filebrowser
podman logs -f filebrowser
podman exec filebrowser df -h /tmp                    # dimensionar o tmpfs
du -sh ~/.config/containers/volumes/filebrowser/data/cache   # cache de miniaturas
```

## Créditos

Deploy Quadlet baseado no
[gtsteffaniak/filebrowser](https://github.com/gtsteffaniak/filebrowser)
(Apache-2.0), que por sua vez é uma reescrita do
[filebrowser/filebrowser](https://github.com/filebrowser/filebrowser). Este
repositório não tem afiliação com nenhum dos dois projetos.
