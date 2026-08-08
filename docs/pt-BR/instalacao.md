# Instalando e operando serviços

Tudo pelo [`install.py`](../../install.py): instalar, atualizar, backup,
restaurar e remover. Ele deriva os passos da própria unit — ver
["A unit já é o manifesto"](#instalando-um-serviço) abaixo.

## Instalando um serviço

Cada README de serviço traz os `wget`/`mkdir`/`podman secret` na mão, e
continua valendo. O `install.py` faz a mesma coisa lendo a unit:

```bash
python3 install.py --list
python3 install.py traccar                 # dry-run: só mostra o que faria
python3 install.py traccar --apply
python3 install.py traccar --update        # rebaixa as units e reinicia
python3 install.py traccar --reinstall     # sobrescreve env, config e secrets
python3 install.py traccar --reinstall --ask-secrets   # ...e digitar você mesmo
python3 install.py traccar --remove        # para e tira as units, mantém dados
python3 install.py traccar --remove --purge   # + apaga volumes, secrets e env
python3 install.py traccar --backup --out ~/backups   # dados, a frio
python3 install.py traccar --restore ~/backups/traccar-....tar.gz
python3 install.py traccar --apply --access both     # local + tailnet
python3 install.py traccar --apply --prefix /tmp/teste   # sandbox
```

Todos os modos são **dry-run por padrão**; `--apply` executa.

**Vários de uma vez**, e `--all` pra agir sobre os 48:

```bash
python3 install.py memos ntfy homebox --apply
python3 install.py --all --update --apply     # depois de uma leva de bumps
python3 install.py memos ntfy --backup --apply --out ~/backups
```

**Uma unit só de uma stack** — nomear a unit em vez da pasta. Útil quando a
pasta tem vários serviços e você quer só um deles:

```bash
python3 install.py media-stack-jellyfin --apply   # só o Jellyfin, não as outras 11
python3 install.py toolbx-ubuntu --apply          # só a caixa do Ubuntu
python3 install.py immich-postgres --update       # uma peça de uma stack
```

O basename é inequívoco pela [regra 1](./convencoes.md) — um basename, uma
unit, no repositório inteiro — então não há o que desambiguar, e o `check.py`
reprova o build se isso deixar de valer. O que o filtro mantém: os volumes, o
env file e os secrets daquela unit, e **todo `.network` da pasta**, porque o
`Network=` nomeia o arquivo e o Quadlet não gera a unit sem ele. O destino
continua sendo a subpasta da stack.

Isso vale só pra instalação, `--reinstall` e `--update`. O `--backup`, o
`--restore` e o `--remove` agem sobre a raiz de volume do serviço, que as units
de uma stack compartilham — um `--remove --purge` numa unit apagaria os dados da
stack inteira — então esses recusam nome de unit e pedem o da pasta.

Cada serviço sai separado por uma linha, e no fim vem o placar
(`3/3 ok`, ou a lista do que falhou). Os nomes são conferidos **antes** de
começar — descobrir no meio que o terceiro não existe deixaria o trabalho
pela metade. `--restore` é a exceção e aceita um serviço só, porque o
`.tar.gz` é de um serviço. Com `--purge`, cada um pede a sua confirmação
digitada, de propósito.

**`--update` é o único que você usa toda semana.** Ele é o `wget -O` por
cima descrito no ciclo de vida, virado script: bump de versão no
repositório não muda o arquivo já instalado no host, e é isso que ele
resolve. Não toca em volume, `.env` nem secret.

**Instalar por cima para antes de fazer qualquer coisa.** Se as units já
estão no host, a instalação simples recusa e mostra os dois caminhos — do
contrário ela reescreveria as units e reiniciaria sem tocar em env, config
e secrets, que é um `--update` com o nome errado:

```
filebrowser: already installed — 1 of 1 unit(s) in ~/.config/containers/systemd
  --update     re-copies the units and restarts, keeping data, env and secrets
  --reinstall  installs again, OVERWRITING env, config and secrets
```

Uma stack diz `1 of 6` quando só parte das units está lá, então serviço
meio instalado aparece em vez de ser completado em silêncio.

**O que sobrevive numa instalação que roda de verdade.** Depois de um
`--remove` (que mantém os dados), instalar de novo encontra o `.env`, o
arquivo de config e os secrets ainda no lugar e mantém eles, com aviso —
guardam senha, token e o cadastro já fechado. Pra sobrescrever de
propósito, `--reinstall`.

**`--remove` mantém os dados** e diz quanto ficou guardado; `--purge`
apaga volumes, secrets e `.env`, e exige que você **digite o nome do
serviço** pra confirmar. Nos dois casos ele lembra que o tsdproxy não
desregistra o nó da tailnet — isso é no admin do Tailscale.

**`--backup` para o serviço antes de empacotar**, e religa depois. A
frio de propósito: copiar SQLite ou Postgres com o processo escrevendo é
a receita clássica de arquivo que só se revela corrompido na hora de
restaurar — o mesmo alerta que o [zerobyte](../../apps/zerobyte/README.pt-BR.md) faz. Vão
pro `.tar.gz` os volumes, os secrets e o `.env`; os dois últimos são
minúsculos e são o que falta pro backup ser restaurável, porque sem eles
o dado volta mas o serviço não sobe. A linha de restauração sai impressa
no fim:

```
tar xzf homebox-20260807-184209.tar.gz -C ~/.config/containers
```

Ele **não substitui** o [zerobyte](../../apps/zerobyte/README.pt-BR.md), que é o backup
agendado e cifrado pra fora da máquina. Este é o "antes de bumpar a
versão", que é justamente quando o ciclo de vida deste README manda ter
um.

**`--restore` é troca, não mistura.** Ele apaga a raiz do volume antes de
extrair — sem isso `tar x` sobrescreveria o que está no arquivo e
deixaria o resto, e um `-wal` do estado atual em cima de um `.db` antigo
é justamente como se corrompe um SQLite. Só apaga as raízes que o arquivo
traz, pra um backup parcial não levar embora o que não sabe repor.

Antes de qualquer coisa ele confere se o `.tar.gz` é **daquele serviço**
(restaurar o backup do homebox sobre o traccar apagaria os dois de uma
vez) e pede o nome digitado pra confirmar, como o `--purge`. Depois de
extrair, reaplica o dono nos serviços com `User=` — arquivo vindo de
outra máquina carrega um subuid que pode não ser o daqui.


**O download da imagem aparece, não fica escondido.** O `install.py` puxa cada
imagem ele mesmo, antes do start, pra saída de progresso do próprio podman
chegar no seu terminal:

```
  -> podman pull docker.io/dockurr/windows:6.04

Trying to pull docker.io/dockurr/windows:6.04...
Copying blob sha256:55afa1ecc21d...  [====================>-------]  312.4MiB / 487.1MiB
```

Deixar o start puxar por baixo dos panos também funciona, mas o systemd manda
esse download pro journal — o que numa imagem de vários gigabytes são vários
minutos calados, idênticos a um script travado. Imagem que já está no host é
pulada, então o passo só aparece quando há mesmo o que baixar. O `--update`
também puxa: tag trocada é justamente o download que vale acompanhar.

**O start também se narra.** Unit com `Notify=healthy` segura o systemd até o
healthcheck passar — até o `TimeoutStartSec`, o que numa VM que antes baixa um
sistema convidado são minutos. Pra essas units o passo de restart segue o log
do container enquanto espera, e para quando o systemd volta:

```
  -> systemctl --user restart qemu  (follows the log while it starts)

❯ Booting image using QEMU v10.0.11...
Welcome to Alpine Linux 3.24
```

Unit sem `Notify=healthy` volta na hora e não ganha follow — não há o que
narrar. Hoje são dois serviços nesse grupo.

### Perguntar em vez de assumir: `[choices]`

Alguns valores de `.env` são escolha de uma lista conhecida, e só valem no
primeiro start — a edição do Windows é baixada uma vez e nunca mais revista.
Entregar um padrão que o usuário depois precisa achar e editar é a pior das
duas opções, então o `install.ini` pode declarar a pergunta:

```ini
[choices]
VERSION =
    Which Windows to install (downloaded on first boot)
    11: Windows 11 Pro — 7.9 GB
    10: Windows 10 Pro — 5.7 GB
    xp: Windows XP Professional — 0.6 GB
```

Pasta com vários serviços independentes precisa de uma pergunta por unit, e o
`[choices.<unit>]` dá isso — o `apps/vm` pergunta um `VERSION` pro Windows e
outro pro macOS, gravando cada resposta no `.env` da unit dela:

```ini
[choices.vm-windows]
VERSION =
    Which Windows to install (downloaded on first boot)
    11: Windows 11 Pro — 7.9 GB

[choices.vm-macos]
VERSION =
    Which macOS to install (downloaded on first boot)
    15: macOS 15 Sequoia
```

A primeira linha é a pergunta, as demais são `valor: rótulo` (o rótulo é
opcional quando o valor já se explica), e a primeira opção é o padrão. Na
instalação:

```
  Which Windows to install (downloaded on first boot)
    1) 11        Windows 11 Pro — 7.9 GB  (default)
    2) 10        Windows 10 Pro — 5.7 GB
    3) xp        Windows XP Professional — 0.6 GB
  number or value [11]:
```

Um número, o próprio valor, ou Enter pro padrão. Resposta fora da lista é
**aceita como veio** em vez de recusada — o `VERSION` também aceita a URL de
uma ISO sua, e lista nem sempre é exaustiva.

A resposta é escrita no `.env` que esta execução acabou de copiar,
substituindo a linha correspondente **inclusive quando ela está comentada**,
que é como os `.example` carregam configuração opcional. Ele nunca toca num
`.env` que já existia: aquele arquivo é seu, e uma pergunta que o reescrevesse
em silêncio seria uma armadilha. Sem terminal — `--prefix`, script, CI — nada é
perguntado; os padrões ficam e um aviso diz qual arquivo editar.

### Local, tailnet ou os dois

O acesso local **funciona nos três modos**, porque toda unit publica porta
no host — e o [tsdproxy](../../apps/tsdproxy/README.pt-BR.md) depende justamente dessa porta
pra alcançar o serviço. O que o `--access` decide é se o serviço registra
um nó na tailnet:

```bash
python3 install.py memos --apply --access local     # só na LAN
python3 install.py memos --apply --access tailnet   # padrão
python3 install.py memos --apply --access both
```

| | registra nó na tailnet? | `homepage.href` |
| --- | --- | --- |
| `local` | não — as labels de `tsdproxy.*` são comentadas | `http://<ip-da-lan>:<porta>` |
| `tailnet` *(padrão)* | sim | `https://<app>.<tailnet>.ts.net` |
| `ambos` | sim | `https://<app>.<tailnet>.ts.net` |

O link do dashboard segue o que faz sentido pra cada modo: em `local` só
existe o endereço da LAN; em `tailnet` e `ambos` o link é o nome da
tailnet, **que funciona de qualquer lugar** — é o endereço certo pra
clicar tanto de casa quanto de fora.

Quem preferir o link curto, direto pra LAN sem o salto pelo proxy,
acrescenta `--href-local`:

```bash
python3 install.py memos --apply --access both --href-local
# na tailnet, mas o dashboard aponta pra http://192.168.1.12:5230
```

**Uma flag, um significado**: `--access` decide o nó na tailnet,
`--href-local` decide o link do dashboard. `--local` é só um atalho de
`--access local` — e combinar os dois dá erro em vez de adivinhar.

Em `--access local` as labels de tsdproxy são **comentadas, não apagadas**:
a unit continua dizendo o que existiria, e mudar de ideia é rodar
`--update` com outro modo.

**`--prefix` é sandbox de verdade**: além de redirecionar os caminhos, ele
*não* executa `systemctl` nem `podman`, só anuncia. Sem isso um
`--remove --prefix /tmp/teste` derrubaria o serviço real, porque o
prefixo não muda o nome da unit.

**A unit já é o manifesto.** O que um README manda fazer está quase todo
declarado no próprio `.container`, só que em texto corrido:

| Diretiva | Vira |
| --- | --- |
| `Volume=` | `mkdir -p` do caminho no host |
| `EnvironmentFile=` | destino do `.env.example` |
| `Secret=` | os `podman secret create` |
| `User=` | o `podman unshare chown -R` do volume |
| quantidade de arquivos Quadlet | solto vs. subpasta em `systemd/` |

O que sobra é pouco, e mora em `apps/<app>/install.ini`: a **receita de
cada segredo** (o valor aleatório certo pra cada um, ou a instrução
quando ele não é gerável), o **destino de arquivo de config que cai
dentro de um volume de diretório** — dois casos hoje, donetick e
copyparty — e **valores de `.env` que são escolha de uma lista fixa**, que
o script pergunta.

```ini
[secrets]
homebox-api-key-pepper = rand-base64 48
monica-app-key = shell printf 'base64:%s' "$(openssl rand -base64 32)"
tsdproxy-authkey = manual auth key gerada no admin do Tailscale
```

Formas: `rand-hex N`, `rand-base64 N`, `rand-urlsafe N`, `rand-alnum N`,
`shell <comando>` e `manual <instrução>`. Os `manual` **não** são
inventados — chave de auth do Tailscale, hash argon2 do vaultwarden e
senha do vaultzap vêm de fora.

Num terminal, o `--apply` **pergunta o valor dos `manual` na hora**, com
a entrada escondida:

```
  vaultzap-basic-auth
  escolher `usuario:senha` e criar o secret à mão (ver README)
  valor (não aparece na tela):
```

Deixar em branco pula, e o valor fica pendente como antes. Fora de um
terminal (pipe, cron, `--prefix`) ele nunca trava esperando: volta a só
avisar. O arquivo é gravado **sem `\n` no fim** de propósito — vários apps
leem o valor cru, e a quebra de linha vira parte da senha.

O `check.py` confere que todo `Secret=` tem receita, então um serviço não
para no meio da instalação por falta dela.

No fim (e no dry-run) ele imprime **onde acessar**, também derivado da
unit: `tsdproxy.port.web` diz qual porta interna é a web — o que importa
em serviço que publica mais de uma, como o traccar com a do protocolo
OsmAnd —, o `PublishPort` correspondente dá a do host, e o
`homepage.href` já traz a URL da tailnet, só com o `${TAILNET}` por
resolver.

```
http://192.168.1.12:8099
https://traccar.your-tailnet.ts.net
```

Stack multi-container lista uma por unit. Sem tailnet, só a primeira
linha.

Quando o serviço tem login, o rodapé imprime **as credenciais**, em texto puro:

```
  user:     admin
  password: 7x63tlKq...
```

O `[login]` do `install.ini` nomeia o único secret que é senha digitada por
alguém. Só ele é impresso — chave de JWT e token de API ao lado também são
secrets, e ninguém vai digitar nenhum dos dois:

```ini
[login]
user = admin
password = filebrowser-admin-password
```

O `check.py` reprova o build se esse nome não for um `Secret=` declarado por
alguma unit, porque um erro de digitação ali sumiria com as credenciais em
silêncio em vez de dar erro. Serviço sem seção `[login]` não imprime nada aqui.

**A senha fica no seu scrollback**, o que vale saber antes de tirar screenshot
da instalação ou colar a saída em algum lugar.

Isso aparece no dry-run também — então um `install.py <app>` simples num serviço
já instalado também responde "qual era mesmo a minha senha", inclusive quando
ele recusa reinstalar.

**Pra escolher a senha em vez de aceitar a gerada**, `--ask-secrets`:

```bash
python3 install.py filebrowser --reinstall --ask-secrets --apply
```

Ele pergunta cada secret na vez, sem ecoar o que você digita, e **Enter aceita
o valor gerado** — dá pra digitar a única senha que você realmente usa pra
entrar e deixar a chave do JWT, o token de API e o resto aleatórios. Exige
terminal e `--apply`; sem os dois é erro, não uma volta silenciosa pra geração.

**Validado contra a instalação real**: rodar o `install.py --prefix` num
diretório vazio e comparar com o que está no host reproduz arquivo por
arquivo em 10 serviços conferidos. As duas diferenças que apareceram eram
deriva do host, não do script — uma delas um comentário obsoleto que
tinha sobrado de uma edição manual.

## Ciclo de vida

O [`install.py`](#instalando-um-serviço) cobre o ciclo inteiro, sempre com
dry-run por padrão — `--apply` é o que executa:

```bash
python3 install.py <app> --update              # rebaixa a unit e reinicia
python3 install.py <app> --reinstall           # sobrescreve .env, config e secrets
python3 install.py <app> --backup --out ~/backups
python3 install.py <app> --restore ~/backups/<app>-....tar.gz
python3 install.py <app> --remove              # mantém os dados
python3 install.py <app> --remove --purge      # apaga volumes, secrets e .env
```

Por baixo é systemd comum, e continua valendo pra inspecionar:

```bash
systemctl --user status <app>
journalctl --user -u <app> -f
podman exec -it <container> sh   # se a imagem tiver shell
systemctl --user daemon-reload   # depois de editar uma unit à mão
```

Servidor de verdade: `loginctl enable-linger <usuário>` — sem isso, os
serviços somem quando a sessão de login encerra.

### Serviço sozinho (a maioria)

Direto: `systemctl --user restart <app>`.

### Serviço com dependências (ex.: immich, owntracks, paperless-ngx)

- **Subir**: só o principal — `systemctl --user start <app>` já sobe as
  dependências primeiro, via `Requires=`.
- **Reiniciar tudo**: idem, `restart` no principal recria a cadeia certa.
- **Reiniciar só uma dependência** (ex.: só o banco, pra aplicar config):
  também **para** quem a requer (regra 8) — se a dependência cair num
  crash-loop nessa janela, quem dependia dela não volta sozinho depois.
  Nesse caso: esperar a dependência ficar `healthy` e só então
  `systemctl --user start <app>` manualmente.
- **Derrubar tudo de propósito**: parar todos de uma vez, não só o
  principal —
  ```bash
  systemctl --user stop <app> <app>-dependencia-1 <app>-dependencia-2
  ```
  (é o padrão usado nos passos de backup de cada README de serviço, por
  este exato motivo — parar só o principal deixa as dependências vivas
  gravando enquanto o backup roda.)

### Conferir depois

```bash
systemctl --user is-active <app>          # rápido, só o status
journalctl --user -u <app> -f              # logs em tempo real
podman ps --filter "name=<app>"            # confirma healthy de verdade
```

### Remover a unit (mantém os dados)

```bash
systemctl --user stop <app> [<dependencias>]
# Serviço solto (1 arquivo):
rm ~/.config/containers/systemd/<app>.container
# Serviço em subpasta (2+ arquivos — ver "Estrutura padrão"):
rm -r ~/.config/containers/systemd/<app>/
systemctl --user daemon-reload
systemctl --user reset-failed   # limpa estado de falha residual, se tiver
```

Depois do `daemon-reload` a unit some do `systemctl --user status`. Os
dados continuam em `volumes/<app>/` — dá pra reinstalar depois sem perder
nada.

### Apagar tudo (destrutivo — dados, segredos, config)

```bash
# 1. Confirmar que a unit já foi removida (passo acima)

# 2. Dados — IRREVERSÍVEL sem backup
rm -rf ~/.config/containers/volumes/<app>/

# 3. Env
rm -f ~/.config/containers/env/<app>.env

# 4. Secrets, se o serviço usava (a maioria hoje: beszel, gitea, immich,
#    karakeep, n8n, openwebui, owncloud, owntracks,
#    paperless-ngx, tsdproxy, vaultwarden, zerobyte — checar o README do
#    serviço se não tiver certeza)
podman secret rm <app>-nome-do-secret
rm -rf ~/.config/containers/secrets/<app>/
```

Duas pegadinhas específicas deste repositório:

- **tsdproxy não desregistra o nó da tailnet sozinho** — apagar o
  container não remove o dispositivo do admin do Tailscale (é assim que
  surgiram os duplicados `dash`/`dash-1` mencionados antes). Pra tirar de
  vez, remover manualmente em
  https://login.tailscale.com/admin/machines.
- **Homepage não precisa de limpeza** — só lê labels de containers vivos
  via socket; some da lista sozinha assim que o container deixa de
  existir.

