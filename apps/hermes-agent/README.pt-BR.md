# Hermes Agent — Podman Quadlet (rootless)

**[🇺🇸 Read in English](./README.md)**

Deploy do [Hermes Agent](https://github.com/NousResearch/hermes-agent) (Nous
Research) via Podman Quadlet, usando a imagem oficial
`docker.io/nousresearch/hermes-agent`.

Um agente de IA pessoal que guarda habilidades e memórias entre sessões, e
expõe uma **API compatível com a da OpenAI** — então o [n8n](../n8n/), o
[Open WebUI](../openwebui/) ou o [Home Assistant](../home-assistant/) apontam
pra ele do mesmo jeito que apontariam pra qualquer outro endpoint de modelo.

**Ler a seção de segurança antes de expor este aqui.** Não é um app web com um
agente pendurado: o container traz `docker-cli`, `git`, `ssh`, `ripgrep` e um
navegador Playwright/Chromium, e o dashboard dirige tudo isso. Quem alcança o
dashboard executa comandos dentro do container.

## Arquitetura

Um container só rodando `gateway run`, com **s6-overlay como PID 1**
supervisionando os processos lá dentro. Um volume, `/opt/data`, com tudo:
config, chaves de provedor, sessões, habilidades e memórias. A instalação em
`/opt/hermes` é somente-leitura em runtime e não guarda estado — a imagem é
descartável, o volume não.

Duas portas:

| Porta | O quê |
| --- | --- |
| `8642` | o gateway compatível com a OpenAI (`/v1/...`, mais um `/health` sem autenticação) |
| `9119` | o dashboard web |

Só a **9119 vai pra tailnet** via [tsdproxy](../tsdproxy/). O gateway fica na
porta do host, onde os outros containers alcançam — um agente que guarda as
suas chaves de provedor não precisa de uma segunda porta pública.

## Arquivos

```
hermes-agent.container    # unit principal
.env.example              # usuário do dashboard, CORS
install.ini               # receitas dos secrets
```

## Instalação

```bash
python3 install.py hermes-agent            # dry-run: mostra o que vai fazer
python3 install.py hermes-agent --apply
```

Só na rede local, `--access local`; na tailnet e na LAN, `--access both`.
Somando `--href-local`, o link do dashboard aponta pra LAN. O script cria os
diretórios, escreve o `.env`, gera os secrets, ajusta o dono dos volumes, sobe
o serviço e imprime o endereço no fim — ver
[Instalando e operando](../../docs/pt-BR/instalacao.md).

### Depois, rodar o assistente de setup, uma vez

O agente ainda não tem chave de provedor nenhuma, então não responde nada. O
assistente é interativo e escreve dentro do volume:

```bash
podman exec -it hermes-agent hermes setup
```

Ele pergunta o provedor (Anthropic, OpenAI, …) e a chave, e guarda em
`/opt/data`. É por isso que essas chaves **não** são `podman secret` aqui: são
suas, não são geradas, e o fluxo do próprio upstream já as coloca no volume que
o backup cobre.

Abrir o dashboard em `https://hermes.<your-tailnet>.ts.net` e entrar com
`admin` mais a senha gerada:

```bash
podman secret inspect --showsecret hermes-agent-dashboard-password
```

<details>
<summary><b>Instalação manual</b> (avançado) — os mesmos passos, um a um</summary>


```bash
# 1. Baixar a unit (sem precisar clonar o repositório)
mkdir -p ~/.config/containers/systemd
wget -P ~/.config/containers/systemd/ \
  https://raw.githubusercontent.com/wallacepnts/quadlet-homelab/main/apps/hermes-agent/hermes-agent.container

# 2. Diretórios
mkdir -p ~/.config/containers/volumes/hermes-agent/data
mkdir -p ~/.config/containers/env

# 3. Ambiente
wget -O ~/.config/containers/env/hermes-agent.env \
  https://raw.githubusercontent.com/wallacepnts/quadlet-homelab/main/apps/hermes-agent/.env.example

# 4. Secrets
podman secret create hermes-agent-api-key - <<< "$(python3 -c 'import secrets;print(secrets.token_urlsafe(32))')"
podman secret create hermes-agent-dashboard-password - <<< "$(python3 -c 'import secrets;print(secrets.token_urlsafe(24))')"
podman secret create hermes-agent-dashboard-secret - <<< "$(openssl rand -hex 32)"

# 5. Subir e rodar o assistente
systemctl --user daemon-reload
systemctl --user start hermes-agent
podman exec -it hermes-agent hermes setup
```

</details>

## Segurança

O dashboard é o console do agente. Três coisas ficam entre ele e a tailnet, e
as três estão ligadas por padrão aqui:

1. **Basic auth** — `HERMES_DASHBOARD_BASIC_AUTH_USERNAME` no `.env`, senha e
   segredo do cookie como `podman secret`. O upstream deixa os três sem valor,
   o que publica o dashboard sem login nenhum.
2. **`API_SERVER_KEY`** no gateway, pra 8642 não ser um proxy de modelo aberto
   faturando na sua conta do provedor.
3. **O gateway não está na tailnet** — só o dashboard é proxiado.

Tailnet não é autenticação: ela estreita quem pode bater na porta, não quem
entra. Todo dispositivo da sua tailnet, e tudo que roda nesses dispositivos,
alcança a porta 9119.

O `/health` da 8642 é sem autenticação de propósito — é o que o `HealthCmd`
chama, e responde antes de o gateway ter qualquer chave configurada.

## Hardening — o que foi medido e o que ficou em aberto

A imagem sobe como **root de propósito**: o hook de estágio 2 do s6-overlay
roda `usermod`/`groupmod` pra remapear o UID, faz chown de `/opt/data`, semeia
a config, e só então cai pro usuário `hermes` (UID 10000) via `s6-setuidgid`.
Esse único fato elimina boa parte da escada da
[regra 20](../../docs/pt-BR/convencoes.md):

| Ajuste | Situação |
| --- | --- |
| `NoNewPrivileges=true` | ligado — cair de root pra 10000 não precisa de privilégio novo |
| `PidsLimit=2048` | ligado — supervisão do s6 mais Playwright/Chromium, não os 256 de praxe |
| `ShmSize=1g` | ligado — o upstream exige pras ferramentas de navegador (`--shm-size=1g`) |
| `Memory=4G` | ligado — o upstream recomenda 2–4 GB |
| `ReadOnly=true` | **não tentado** — s6-overlay como PID 1, o caso que a regra 20 nomeia |
| `User=` | **não tentado** — a imagem larga o privilégio sozinha; forçar um uid quebra o chown antes do `s6-setuidgid` |
| `DropCapability=ALL` | **ainda não tentado** — ver abaixo |

`DropCapability=ALL` é o que vale testar. O start precisa no mínimo de `CHOWN`,
`DAC_OVERRIDE`, `FOWNER`, `SETGID` e `SETUID`, e provavelmente de `KILL` (o s6
supervisiona processos de outro uid). Ninguém mediu isso aqui, então a unit sai
sem a linha em vez de sair com um chute. Pra descobrir — e lembrar do
`systemctl --user reset-failed hermes-agent` entre as tentativas, senão o rate
limit faz uma config boa parecer quebrada:

```bash
podman run --rm -d --name t --cap-drop=ALL \
  --cap-add=CHOWN --cap-add=DAC_OVERRIDE --cap-add=FOWNER \
  --cap-add=SETGID --cap-add=SETUID --cap-add=KILL \
  --shm-size=1g -v /tmp/hermes-test:/opt/data:Z \
  docker.io/nousresearch/hermes-agent:v2026.8.3 gateway run
sleep 60
podman exec t curl -sf -o /dev/null -w "%{http_code}\n" http://127.0.0.1:8642/health
podman logs t | tail -30
podman rm -f t
```

`200` quer dizer que o app está vivo, não só o container. Registrar o resultado
aqui de qualquer jeito — capability testada e recusada vale tanto quanto uma
que funcionou.

## Auto-update

Sem `AutoUpdate=` — tag explícita (`v2026.8.3`), bump na mão
([regra 9](../../docs/pt-BR/convencoes.md)). As tags são versão de calendário e
o upstream também publica `latest` e `main`, daí o
`wud.tag.include=^v[0-9]+.[0-9]+.[0-9]+$` na unit. Algumas releases têm um
quarto componente (`v2026.7.7.2`) e não vão casar — conferir
[a página de releases](https://github.com/NousResearch/hermes-agent/releases)
quando o `updates.py` ficar quieto por muito tempo.

Migração de schema da config roda no start (`HERMES_SKIP_CONFIG_MIGRATION`
desliga), então fazer o backup abaixo antes de qualquer bump.

## Backup & recuperação

```bash
systemctl --user stop hermes-agent
tar -czf hermes-agent-backup-$(date +%Y%m%d-%H%M%S).tar.gz \
  -C ~/.config/containers/volumes hermes-agent
systemctl --user start hermes-agent
```

**O arquivo contém as suas chaves de API de provedor em texto claro** — o
`hermes setup` escreve elas em `/opt/data`. Tratar o tarball como se fosse as
próprias chaves; ele não pertence ao mesmo lugar dos backups dos outros
serviços, a não ser que esse lugar seja criptografado (ver
[zerobyte](../zerobyte/), que usa Restic).

## Comandos úteis

```bash
systemctl --user status hermes-agent
podman logs -f hermes-agent
podman exec -it hermes-agent hermes setup      # assistente, primeira vez
podman exec hermes-agent hermes --version
curl -H "Authorization: Bearer $KEY" http://127.0.0.1:8642/v1/models
```

## Créditos

Deploy Quadlet baseado no [Hermes Agent](https://github.com/NousResearch/hermes-agent)
da [Nous Research](https://nousresearch.com) (MIT).
