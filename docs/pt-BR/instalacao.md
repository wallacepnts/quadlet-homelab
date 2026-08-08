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

**Instalar por cima não apaga o que você editou.** `.env`, arquivo de
config e secret que já existem são mantidos, com aviso — eles guardam
senha, token e o cadastro já fechado. Pra sobrescrever de propósito,
`--reinstall`.

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
quando ele não é gerável) e o **destino de arquivo de config que cai
dentro de um volume de diretório** — dois casos hoje, donetick e
copyparty.

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

