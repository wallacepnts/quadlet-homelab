# wger — Podman Quadlet (rootless)

**[🇬🇧 Read in English](./README.md)**

Deploy do [wger](https://github.com/wger-project/wger) (planejamento e
acompanhamento de treinos) via Podman Quadlet, usando a imagem oficial
`docker.io/wger/server`.

Rotinas, registro de séries e cargas, medidas corporais, peso, e um banco
público de exercícios com imagem e vídeo. Substituiu o Wingfit neste
repositório.

## Arquitetura

**Container único.** Isto é uma divergência consciente do projeto: o
`docker-compose.yml` de produção do wger sobe **seis** containers — `web`,
`nginx`, Postgres, Redis, `celery_worker` e `celery_beat`.

Pra um usuário só, isso é caro demais. A unit daqui usa o mesmo
`wger/server`, com três mudanças ([regra 22](../../docs/pt-BR/convencoes.md)):

| Peça do compose oficial | Aqui | Como |
| --- | --- | --- |
| Postgres | **SQLite** | `PS_DATABASE_URI=sqlite:////home/wger/db/database.sqlite` |
| Redis | cache em memória | `DJANGO_CACHE_BACKEND=…LocMemCache` |
| celery worker + beat | nada | `USE_CELERY=False` |
| nginx | o próprio servidor | serve estático direto |

O caminho do SQLite não é invenção: é o mesmo `PS_DATABASE_URI` que o
compose `dev-sqlite` do projeto usa, na mesma imagem. Testado até o fim —
as migrações do Django rodam e o app responde.

**O que se perde sem Celery**: a sincronização automática, em background,
do banco público de exercícios e ingredientes. Dá pra puxar sob demanda
(ver abaixo). Se você usa muito a busca de ingredientes, vale reconsiderar.

Hardening: aceita `ReadOnly=true` e `DropCapability=ALL`. **Não tem
`User=`** porque a imagem já roda como uid 1000 (usuário `wger`) —
declarar de novo seria redundante.

## Arquivos

```
wger.container   # unit principal
.env.example     # banco, hosts, cadastro, sincronização
```

## Instalação

```bash
python3 install.py wger            # dry-run: mostra o que vai fazer
python3 install.py wger --apply
```

Só na rede local, `--access local`; na tailnet e na LAN, `--access
both`. Acrescentar `--href-local` faz o link do dashboard apontar pra LAN. O script cria os diretórios, grava o
`.env`, gera os secrets, ajusta o dono dos volumes, sobe o serviço e
imprime o endereço no fim — ver
[Instalando e operando](../../docs/pt-BR/instalacao.md) no README
raiz.

Acessar `http://<ip-do-host>:8102` (ou via [tsdproxy](../tsdproxy/README.pt-BR.md) em
`https://wger.<your-tailnet>.ts.net`).

<details>
<summary><b>Instalação manual</b> (avançado) — os mesmos passos, um a um</summary>


```bash
# 1. Baixar a unit (sem precisar clonar o repositório)
mkdir -p ~/.config/containers/systemd
wget -P ~/.config/containers/systemd/ \
  https://raw.githubusercontent.com/wallacepnts/quadlet-homelab/main/apps/wger/wger.container

# 2. Diretórios + dono correspondente ao uid 1000 da imagem
mkdir -p ~/.config/containers/volumes/wger/{db,static,media}
podman unshare chown -R 1000:1000 ~/.config/containers/volumes/wger

# 3. Variáveis — trocar <your-tailnet> em ALLOWED_HOSTS e CSRF_TRUSTED_ORIGINS
mkdir -p ~/.config/containers/env
wget -O ~/.config/containers/env/wger.env \
  https://raw.githubusercontent.com/wallacepnts/quadlet-homelab/main/apps/wger/.env.example
${EDITOR:-vi} ~/.config/containers/env/wger.env

# 4. SECRET_KEY — assina sessão e cookie
mkdir -p ~/.config/containers/secrets/wger
openssl rand -hex 32 > ~/.config/containers/secrets/wger/secret-key.txt
chmod 600 ~/.config/containers/secrets/wger/secret-key.txt
podman secret create wger-secret-key ~/.config/containers/secrets/wger/secret-key.txt

# 5. Subir. O primeiro start roda TODAS as migrações do Django e coleta
#    os estáticos — leva minutos, daí TimeoutStartSec=300.
systemctl --user daemon-reload
systemctl --user start wger
podman logs -f wger    # acompanhar até parar de aplicar migração
```

Acessar `http://<ip-do-host>:8102` (ou via [tsdproxy](../tsdproxy/README.pt-BR.md) em
`https://wger.<your-tailnet>.ts.net`).

</details>

## Criando a sua conta

O `.env.example` já vem com `ALLOW_REGISTRATION=False`. Pra criar o
primeiro usuário, o caminho é o `manage.py` — não precisa abrir o
cadastro:

```bash
podman exec -it wger python3 manage.py createsuperuser
```

## Sincronizando exercícios e ingredientes

Sem Celery isso não roda sozinho. Puxar quando quiser:

```bash
podman exec wger python3 manage.py sync-exercises
podman exec wger python3 manage.py download-exercise-images
podman exec wger python3 manage.py sync-ingredients        # grande, demora
```

Vale um `systemd --user` timer se você quiser periodicidade — mesmo
padrão dos sidecars descritos no [zerobyte](../zerobyte/README.pt-BR.md).

## Auto-update

Sem `AutoUpdate=` — tag explícita (`2.6.0`), bump manual (regra 9 do
convenções). Dois motivos extras aqui: treino registrado é dado real, e
o wger é Django, então subir de versão significa rodar migração — que
não volta atrás. Backup antes.

O upstream publica `-dev` e `-alpha` junto das estáveis (`2.6-dev`,
`2.7.0-alpha1`), daí o `wud.tag.include` restringindo a `X.Y.Z`.

## Backup & Recuperação

```bash
systemctl --user stop wger
tar -czf wger-backup-$(date +%Y%m%d-%H%M%S).tar.gz \
  -C ~/.config/containers/volumes wger
systemctl --user start wger
```

`db/` é o banco todo; `media/` são as imagens que você subiu. `static/`
se regenera no start. O secret precisa de backup separado — sem a mesma
`SECRET_KEY`, todas as sessões caem.

## Comandos úteis

```bash
systemctl --user status wger
podman logs -f wger
podman exec wger python3 manage.py showmigrations | tail -20
```

## Créditos

Deploy Quadlet baseado no [wger](https://github.com/wger-project/wger)
(AGPL-3.0).
