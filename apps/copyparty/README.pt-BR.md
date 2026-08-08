# Copyparty — Podman Quadlet (rootless)

**[🇬🇧 Read in English](./README.md)**

Deploy do [Copyparty](https://github.com/9001/copyparty) (servidor de
arquivos com upload pelo navegador) via Podman Quadlet, usando a imagem
oficial `ghcr.io/9001/copyparty-ac`.

Upload direto do navegador ou do celular, com retomada de transferência,
thumbnail, busca, e também WebDAV, FTP e SMB no mesmo processo. Preenche
o que o [ownCloud](../owncloud/README.pt-BR.md) (sincronização) e o
[Syncthing](../syncthing/README.pt-BR.md) (replicação) não fazem: "manda esse arquivo
pra cá agora, de qualquer aparelho".

## Arquitetura

Container único, Python, **sem banco** — o índice fica em SQLite gerado
sozinho dentro do volume servido. Aceita o nível mais forte de hardening
do repositório (`ReadOnly=true`, `DropCapability=ALL`, `User=1000`),
testado exercitando o app.

Dois volumes: `/cfg` (o `copyparty.conf`) e `/w` (a raiz servida).

### Tmpfs de 256M, não 64M

O upload em pedaços passa por `/tmp` antes de virar arquivo final. Os
64M do padrão deste repositório estouram em arquivo grande — mesma
lógica do `karakeep-chrome` e do vaultzap ([convenções, regra 20](../../docs/pt-BR/convencoes.md)).

### Variante da imagem

O upstream publica três: `copyparty-min` (só o básico), `copyparty-im`
(imagem e áudio) e `copyparty-ac` (**a usada aqui**: thumbnail, busca por
metadados e conversão de mídia). Trocar pra `min` corta uns 100 MB se
você não precisa de thumbnail.

## Segurança

**A config guarda as senhas em texto claro**, por isso ela mora no volume
e não é versionada — o repositório traz só o `.example` com o campo
marcado pra trocar.

O `.example` já define acesso **fechado**: sem uma conta, não se lista
nem se baixa nada. Verificado na prática — requisição anônima a um
arquivo devolve `403` e o índice não mostra o nome do arquivo. A raiz `/`
responde `200` porque serve a tela de login; isso não é acesso.

Pra abrir uma pasta pra visitante (o caso "upload pra mim sem conta"),
o Copyparty tem `accs` por caminho — ver a
[documentação de accounts e volumes](https://github.com/9001/copyparty#accounts-and-volumes).

## Arquivos

```
copyparty.container       # unit principal
copyparty.conf.example    # contas e permissões por caminho
```

## Instalação

```bash
python3 install.py copyparty            # dry-run: mostra o que vai fazer
python3 install.py copyparty --apply
```

Só na rede local, `--access local`; na tailnet e na LAN, `--access
both`. Acrescentar `--href-local` faz o link do dashboard apontar pra LAN. O script cria os diretórios, grava o
`.env`, gera os secrets, ajusta o dono dos volumes, sobe o serviço e
imprime o endereço no fim — ver
[Instalando e operando](../../docs/pt-BR/instalacao.md) no README
raiz.

Acessar `http://<ip-do-host>:3923` (ou via [tsdproxy](../tsdproxy/README.pt-BR.md) em
`https://copyparty.<your-tailnet>.ts.net`).

<details>
<summary><b>Instalação manual</b> (avançado) — os mesmos passos, um a um</summary>


```bash
# 1. Baixar a unit (sem precisar clonar o repositório)
mkdir -p ~/.config/containers/systemd
wget -P ~/.config/containers/systemd/ \
  https://raw.githubusercontent.com/wallacepnts/quadlet-homelab/main/apps/copyparty/copyparty.container

# 2. Diretórios
mkdir -p ~/.config/containers/volumes/copyparty/{cfg,data}

# 3. Config — TROCAR a senha antes de subir
wget -O ~/.config/containers/volumes/copyparty/cfg/copyparty.conf \
  https://raw.githubusercontent.com/wallacepnts/quadlet-homelab/main/apps/copyparty/copyparty.conf.example
${EDITOR:-vi} ~/.config/containers/volumes/copyparty/cfg/copyparty.conf

# 4. Dono correspondente ao User=1000 da unit
podman unshare chown -R 1000:1000 ~/.config/containers/volumes/copyparty

# 5. Subir
systemctl --user daemon-reload
systemctl --user start copyparty
```

Acessar `http://<ip-do-host>:3923` (ou via [tsdproxy](../tsdproxy/README.pt-BR.md) em
`https://copyparty.<your-tailnet>.ts.net`).

</details>

## WebDAV

O mesmo endereço serve WebDAV, sem configuração extra — dá pra montar
como unidade de rede no celular ou no gerenciador de arquivos do desktop,
usando a mesma conta do `copyparty.conf`.

## Auto-update

Sem `AutoUpdate=` — tag explícita (`1.20.20`), bump manual (regra 9 do
convenções). Os arquivos servidos são seus; revisão manual antes de
trocar de versão.

## Backup & Recuperação

```bash
systemctl --user stop copyparty
tar -czf copyparty-backup-$(date +%Y%m%d-%H%M%S).tar.gz \
  -C ~/.config/containers/volumes copyparty
systemctl --user start copyparty
```

`data/` são os arquivos; `cfg/` são as contas. O índice se reconstrói
sozinho.

## Comandos úteis

```bash
systemctl --user status copyparty
podman logs -f copyparty
# testar que anônimo é barrado (deve dar 403)
curl -s -o /dev/null -w '%{http_code}\n' http://127.0.0.1:3923/algum-arquivo
```

## Créditos

Deploy Quadlet baseado no [Copyparty](https://github.com/9001/copyparty)
de [9001](https://github.com/9001) (MIT).
