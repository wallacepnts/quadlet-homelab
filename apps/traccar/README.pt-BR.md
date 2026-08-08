# Traccar — Podman Quadlet (rootless)

**[🇬🇧 Read in English](./README.md)**

Deploy do [Traccar](https://github.com/traccar/traccar) (plataforma de
rastreamento de GPS) via Podman Quadlet, usando a imagem oficial
`docker.io/traccar/traccar`.

Mapa ao vivo, histórico de trajeto, geocercas, relatórios e alertas —
com o app oficial no celular ou com rastreador dedicado. Convive com o
[OwnTracks](../owntracks/README.pt-BR.md), que é mais simples e MQTT-nativo; o Traccar
tem a parte de relatório e geocerca que o OwnTracks não tem.

## Arquitetura

Container único, JVM, **banco H2 embutido** em `data/` — é o default do
Traccar, sem serviço de banco separado ([regra 22](../../docs/pt-BR/convencoes.md)).

Aceita o nível mais forte de hardening do repositório (`ReadOnly=true`,
`DropCapability=ALL`, `User=1000`), com um detalhe que só apareceu
testando: **`podman diff` mostra que o Traccar cria `/opt/traccar/override`
no start**, e sem um `Tmpfs=` ali o `ReadOnly` derruba o serviço. É onde
ficam sobrescritas do frontend, conteúdo descartável.

### Portas

| Porta host | Pra quê |
| --- | --- |
| `8099` | interface web (8082 dentro do container) |
| `5056` | protocolo OsmAnd, TCP e UDP (5055 dentro) |

A 5055 do host já é do [seerr](../media-stack/README.pt-BR.md), então o protocolo sai na
**5056**. No app Traccar Client, informar a porta 5056 junto do endereço.

O Traccar fala ~150 protocolos, cada um numa porta entre 5000 e 5150. A
imagem oficial manda publicar a faixa inteira; aqui publica-se só a do
OsmAnd, que é o que o app oficial usa. Rastreador dedicado de outra marca
precisa da porta correspondente adicionada na unit.

## Arquivos

```
traccar.container      # unit principal
traccar.xml.example    # config — banco H2 e porta do protocolo
```

## Instalação

```bash
python3 install.py traccar            # dry-run: mostra o que vai fazer
python3 install.py traccar --apply
```

Só na rede local, `--access local`; na tailnet e na LAN, `--access
both`. Acrescentar `--href-local` faz o link do dashboard apontar pra LAN. O script cria os diretórios, grava o
`.env`, gera os secrets, ajusta o dono dos volumes, sobe o serviço e
imprime o endereço no fim — ver
[Instalando e operando](../../docs/pt-BR/instalacao.md) no README
raiz.



<details>
<summary><b>Instalação manual</b> (avançado) — os mesmos passos, um a um</summary>


```bash
# 1. Baixar a unit (sem precisar clonar o repositório)
mkdir -p ~/.config/containers/systemd
wget -P ~/.config/containers/systemd/ \
  https://raw.githubusercontent.com/wallacepnts/quadlet-homelab/main/apps/traccar/traccar.container

# 2. Diretórios + dono correspondente ao User=1000 da unit
mkdir -p ~/.config/containers/volumes/traccar/{data,logs,conf}

# 3. Config — precisa EXISTIR antes do start (é bind mount de arquivo;
#    se não existir, o Podman cria um diretório no lugar e o Traccar quebra)
wget -O ~/.config/containers/volumes/traccar/conf/traccar.xml \
  https://raw.githubusercontent.com/wallacepnts/quadlet-homelab/main/apps/traccar/traccar.xml.example

podman unshare chown -R 1000:1000 ~/.config/containers/volumes/traccar

# 4. Subir
systemctl --user daemon-reload
systemctl --user start traccar
```

</details>

## Criando o primeiro usuário

**O Traccar não tem mais admin padrão.** Versões antigas criavam
`admin`/`admin`; as atuais não criam ninguém, e o primeiro usuário
cadastrado vira administrador.

E há uma armadilha: **`web.registration` não é chave de configuração do
Traccar.** Ela circula por aí em tutoriais, mas o Traccar ignora — a
única chave com esse nome no `Keys.java` é `openid.allowRegistration`. O
flag de cadastro mora **no banco**, na linha da tabela `tc_servers`, e
nasce desligado. Mexer no XML depois do primeiro start não muda nada.

Isso é seguro por padrão, e o bootstrap funciona assim (testado):

```bash
# Com ZERO usuários, o POST é liberado e o primeiro vira admin
curl -X POST http://127.0.0.1:8099/api/users \
  -H 'Content-Type: application/json' \
  -d '{"name":"Seu Nome","email":"voce@exemplo.com","password":"SUA-SENHA"}'
```

A partir do segundo, a mesma chamada responde `SecurityException:
Registration disabled`. Pra liberar cadastro de propósito, é na própria
interface, logado como admin: Configurações → Servidor → Registro.

Acessar `http://<ip-do-host>:8099` (ou via [tsdproxy](../tsdproxy/README.pt-BR.md) em
`https://traccar.<your-tailnet>.ts.net`).

## Ligando o celular

App **Traccar Client** (Android/iOS):

| Campo | Valor |
| --- | --- |
| Endereço | `<ip-do-host>` ou o nome da tailnet |
| Porta | `5056` |
| Identificador | o mesmo que você cadastrar como "identificador" do dispositivo na web |

Cadastrar o dispositivo na interface web primeiro (botão `+` na lista de
dispositivos), usando exatamente o identificador do app.

## Auto-update

Sem `AutoUpdate=` — tag explícita (`6.14.5`), bump manual (regra 9 do
convenções). Histórico de posição é dado real e o H2 migra de schema
entre versões: backup antes.

## Backup & Recuperação

```bash
systemctl --user stop traccar
tar -czf traccar-backup-$(date +%Y%m%d-%H%M%S).tar.gz \
  -C ~/.config/containers/volumes traccar
systemctl --user start traccar
```

`data/database.mv.db` é o banco inteiro (usuários, dispositivos,
posições). `logs/` é descartável.

## Comandos úteis

```bash
systemctl --user status traccar
podman logs -f traccar
curl -s http://127.0.0.1:8099/api/server | python3 -m json.tool
```

## Créditos

Deploy Quadlet baseado no [Traccar](https://github.com/traccar/traccar)
de [Anton Tananaev](https://github.com/tananaev) (Apache-2.0).
