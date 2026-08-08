# ntfy — Podman Quadlet (rootless)

**[🇬🇧 Read in English](./README.md)**

Deploy do [ntfy](https://github.com/binwiederhier/ntfy) (servidor de
notificações push) via Podman Quadlet, usando a imagem oficial
`docker.io/binwiederhier/ntfy`.

## Por que ele existe aqui

Este repositório tem três serviços cujo trabalho é *avisar de alguma
coisa* — [uptime-kuma](../uptime-kuma/README.pt-BR.md) (serviço caiu), [wud](../wud/README.pt-BR.md)
(imagem nova disponível) e [zerobyte](../zerobyte/README.pt-BR.md) (backup falhou) — e
até agora nenhum tinha pra onde mandar o alerta. Os três suportam ntfy
nativamente. Ver "Ligando os alertas" abaixo.

Do lado do celular, o app do ntfy assina os tópicos e recebe push sem
depender de servidor de terceiro (nem FCM, se você usar a build do
F-Droid).

## Arquitetura

Container único, Go, SQLite embutido. Dois volumes:

| Volume | Pra quê |
| --- | --- |
| `/var/cache/ntfy` | cache de mensagens (`cache.db`) e anexos |
| `/var/lib/ntfy` | banco de usuários e permissões (`user.db`) |

**É o serviço mais endurecido do repositório**, junto com
[uptime-kuma](../uptime-kuma/README.pt-BR.md) e [homebox](../homebox/README.pt-BR.md): `ReadOnly=true`,
`DropCapability=ALL` e `User=1000`.

### O truque que evitou uma capability

Por padrão o ntfy escuta na **porta 80 dentro do container**, e porta
<1024 exige `NET_BIND_SERVICE` — é exatamente o caso do
[vaultwarden](../vaultwarden/README.pt-BR.md), que precisa dessa capability por isso.
Aqui, `NTFY_LISTEN_HTTP=:2586` move o listener pra uma porta alta e a
necessidade some: o container roda com **zero** capabilities.

Vale como método geral ([convenções, regra 20](../../docs/pt-BR/convencoes.md)): antes de conceder uma
capability, ver se dá pra remover a necessidade dela.

## Segurança: o servidor nasce aberto

Sem configuração, **qualquer um que alcance a porta publica e assina
qualquer tópico**. Um servidor de notificação aberto é um relay de spam
esperando pra acontecer.

A unit já vem com `NTFY_AUTH_DEFAULT_ACCESS=deny-all`, testado na
prática: requisição anônima leva `403`, e só usuário criado com
`ntfy user add` passa. Os usuários são **imperativos**, como os
`podman secret` deste repositório — não versionar, criar no passo 4 da
instalação.

## Arquivos

```
ntfy.container   # unit principal
.env.example     # URL canônica, retenção e limites de anexo
```

## Pré-requisitos

- Podman rootless com systemd `--user` funcionando

## Instalação

```bash
python3 install.py ntfy            # dry-run: mostra o que vai fazer
python3 install.py ntfy --apply
```

Só na rede local, `--access local`; na tailnet e na LAN, `--access
both`. Acrescentar `--href-local` faz o link do dashboard apontar pra LAN. O script cria os diretórios, grava o
`.env`, gera os secrets, ajusta o dono dos volumes, sobe o serviço e
imprime o endereço no fim — ver
[Instalando e operando](../../docs/pt-BR/instalacao.md) no README
raiz.

Acessar `http://<ip-do-host>:8098` (ou via [tsdproxy](../tsdproxy/README.pt-BR.md) em
`https://ntfy.<your-tailnet>.ts.net`).

<details>
<summary><b>Instalação manual</b> (avançado) — os mesmos passos, um a um</summary>


```bash
# 1. Baixar a unit (sem precisar clonar o repositório)
mkdir -p ~/.config/containers/systemd
wget -P ~/.config/containers/systemd/ \
  https://raw.githubusercontent.com/wallacepnts/quadlet-homelab/main/apps/ntfy/ntfy.container

# 2. Diretórios + dono correspondente ao User=1000 da unit.
#    `podman unshare` roda o chown DENTRO do user namespace, que é onde
#    o 1000 do container existe (no host isso vira 100999).
mkdir -p ~/.config/containers/volumes/ntfy/{cache,lib}
podman unshare chown -R 1000:1000 ~/.config/containers/volumes/ntfy

# 3. Variáveis — editar NTFY_BASE_URL com o seu domínio da tailnet
mkdir -p ~/.config/containers/env
wget -O ~/.config/containers/env/ntfy.env \
  https://raw.githubusercontent.com/wallacepnts/quadlet-homelab/main/apps/ntfy/.env.example

# 4. Subir
systemctl --user daemon-reload
systemctl --user start ntfy

# 5. Criar o usuário administrador (imperativo, não versionado). A senha
#    vai por variável de ambiente pra não ficar no histórico do shell.
read -rs NTFY_PASSWORD && export NTFY_PASSWORD
podman exec -e NTFY_PASSWORD ntfy ntfy user add --role=admin admin
unset NTFY_PASSWORD
```

Acessar `http://<ip-do-host>:8098` (ou via [tsdproxy](../tsdproxy/README.pt-BR.md) em
`https://ntfy.<your-tailnet>.ts.net`).

**`NTFY_BASE_URL` importa.** O ntfy grava links de anexo e de web push
com base nela; apontar pro IP:porta faz os links não abrirem de fora do
host. Usar o endereço da tailnet.

</details>

## Testando

```bash
# deve dar 403 — servidor fechado, como esperado
curl -s -o /dev/null -w '%{http_code}\n' -d teste http://127.0.0.1:8098/alertas

# com credencial, publica e lê de volta
curl -u admin:<senha> -d "funcionou" http://127.0.0.1:8098/alertas
curl -u admin:<senha> 'http://127.0.0.1:8098/alertas/json?poll=1'
```

## Ligando os alertas dos outros serviços

Um usuário separado por serviço, com acesso só ao tópico dele, é melhor
que reusar o admin — se um vazar, o estrago é um tópico.

```bash
read -rs NTFY_PASSWORD && export NTFY_PASSWORD
podman exec -e NTFY_PASSWORD ntfy ntfy user add alertas
unset NTFY_PASSWORD
podman exec ntfy ntfy access alertas 'uptime-kuma' write-only
podman exec ntfy ntfy access alertas 'wud' write-only
podman exec ntfy ntfy access alertas 'backup' write-only
# e leitura pra você, no celular
podman exec ntfy ntfy access admin '*' read-write
```

Um detalhe de endereço vale pros três: em rootless, os containers deste
repositório não compartilham rede bridge, então **não** se resolvem pelo
nome do container. O endereço que funciona de dentro de qualquer um deles
é o da tailnet (`https://ntfy.<your-tailnet>.ts.net`, via
[tsdproxy](../tsdproxy/README.pt-BR.md), com TLS de verdade) — confirmado resolvendo de
dentro do uptime-kuma. `http://<ip-do-host>:8098` também serve, em texto
claro.

- **[uptime-kuma](../uptime-kuma/README.pt-BR.md)** — Configurações → Notificações →
  novo, tipo `ntfy`. Servidor `https://ntfy.<your-tailnet>.ts.net`,
  tópico `uptime-kuma`, usuário/senha acima.
- **[wud](../wud/README.pt-BR.md)** — trigger nativo, por variável de ambiente no
  `wud.env`:
  ```bash
  WUD_TRIGGER_NTFY_ALERTAS_URL=https://ntfy.<your-tailnet>.ts.net
  WUD_TRIGGER_NTFY_ALERTAS_TOPIC=wud
  WUD_TRIGGER_NTFY_ALERTAS_AUTH_USER=alertas
  WUD_TRIGGER_NTFY_ALERTAS_AUTH_PASSWORD=<senha>
  ```
- **[zerobyte](../zerobyte/README.pt-BR.md)** — nas notificações do job, webhook
  `POST` pra `https://ntfy.<your-tailnet>.ts.net/backup` com header
  `Authorization: Basic <base64 de alertas:senha>`.

## Auto-update

Sem `AutoUpdate=` — tag explícita (`v2.27.0`), bump manual (regra 9 do
convenções). O `wud.tag.include` restringe a `vX.Y.Z`.

## Backup & Recuperação

```bash
systemctl --user stop ntfy
tar -czf ntfy-backup-$(date +%Y%m%d-%H%M%S).tar.gz \
  -C ~/.config/containers/volumes ntfy
systemctl --user start ntfy
```

Só `lib/user.db` importa de verdade (usuários e permissões) — o cache de
mensagens é descartável por definição.

## Comandos úteis

```bash
systemctl --user status ntfy
podman logs -f ntfy
podman exec ntfy ntfy user list
podman exec ntfy ntfy access
curl -s http://127.0.0.1:8098/v1/health
```

## Créditos

Deploy Quadlet baseado no [ntfy](https://github.com/binwiederhier/ntfy)
de [binwiederhier](https://github.com/binwiederhier)
(Apache-2.0/GPL-2.0).
