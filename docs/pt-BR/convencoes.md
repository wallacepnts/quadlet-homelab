# Convenções

As 22 regras deste repositório, cada uma com o caso real que a originou.
São o que o [`check.py`](../../check.py) confere automaticamente onde dá.

Regras a seguir em qualquer serviço novo neste repositório (Podman 5.8.3).

### 1. Nome de arquivo único em todo o repositório

O Quadlet nomeia a unit gerada pelo *basename* do arquivo, mesmo entre
subpastas diferentes de `~/.config/containers/systemd/`. Prefixar todo
arquivo com o nome do app: `any-sync-bundle-net.network`.

### 2. Secrets são imperativos

Extensões reconhecidas pelo Quadlet: `.container .volume .network .build
.pod .kube .artifact .image`. Fluxo de secret:

```bash
mkdir -p ~/.config/containers/secrets/<app>
echo -n "valor-secreto" > ~/.config/containers/secrets/<app>/senha.txt
chmod 600 ~/.config/containers/secrets/<app>/senha.txt
podman secret create <app>-senha ~/.config/containers/secrets/<app>/senha.txt
```

```ini
Secret=<app>-senha,target=/run/secrets/senha
```

### 3. `.network`: a chave é `NetworkName=`

```ini
[Network]
NetworkName=<app>-net
```

`Driver=bridge` é o default do Podman, só declarar se quiser deixar
explícito.

### 4. Units geradas por Quadlet: só `start`/`stop`/`restart`/`status`

O `[Install]` já é aplicado na hora da geração.

```bash
systemctl --user daemon-reload
systemctl --user start|stop|restart|status <nome>   # .service é opcional aqui
```

### 5. `Network=`/`Volume=` apontando pra outro arquivo Quadlet já injeta a dependência

```ini
Network=meu-app.network
```

adiciona `Requires=meu-app-network.service` + `After=` automaticamente no
service gerado — não declarar de novo em `[Unit]`.

### 6. Diretórios de bind mount precisam existir antes do primeiro start

`mkdir -p` todo caminho usado em `Volume=` antes de subir o serviço.

### 7. `$` em `HealthCmd` usa escape duplo

```ini
HealthCmd=CMD-SHELL test $$(comando) -eq 1
```

### 8. `Requires=` propaga parada

Parar/reiniciar uma dependência também para quem a requer. Se a
dependência falhar nessa janela, quem dependia dela não volta sozinho —
subir manualmente depois.

### 9. Tag flutuante exige `HealthCmd` real

`AutoUpdate=registry` só tem rollback automático em containers com
`HealthCmd` — que por sua vez exige shell/utilitário dentro da imagem.
Padrão deste repositório: tag explícita + bump manual por default;
auto-update é opt-in, só pra imagens com `HealthCmd` de verdade e sem
estado crítico de usuário.

### 10. `PublishPort=` não abre firewall

Porta liberada no firewall do host (`firewalld`/`ufw`/`iptables`) é passo
separado.

### 11. Créditos ao projeto original

Toda pasta de serviço baseado em outro projeto tem uma seção "Créditos" no
próprio README, linkando o repositório e o autor originais.

### 12. `Label=`/valores com espaço precisam de aspas

```ini
Label=homepage.description="Publica containers na tailnet automaticamente"
```

Sem aspas, o Quadlet corta o valor no primeiro espaço (vira só
`Publica`) — sem erro, sem aviso.

### 13. `HealthCmd` com `localhost`: usar `127.0.0.1`

Em `/etc/hosts` do container, `localhost` resolve pra IPv4 (`127.0.0.1`)
**e** IPv6 (`::1`). Se o processo só escutar em IPv4, um cliente que
prefira IPv6 (`wget`, `curl` sem `-4`) recebe "Connection refused" mesmo
com o serviço no ar — testar com o IP explícito evita o problema.

```ini
HealthCmd=CMD-SHELL wget -q --spider http://127.0.0.1:3000/ || exit 1
```

### 14. `Notify=healthy` exige `HealthCmd` no Quadlet, mesmo com HEALTHCHECK na imagem

Uma imagem já ter `HEALTHCHECK` embutido no Dockerfile não basta —
`Notify=healthy` sem `HealthCmd=` declarado no `.container` falha sempre
com `sdnotify policy "healthy" requires a healthcheck to be set`. Repetir
o mesmo comando da imagem em `HealthCmd=` resolve.

### 15. `Secret=nome,type=env,target=VAR` — segredo como env var, não arquivo

```ini
Secret=minha-app-senha,type=env,target=POSTGRES_PASSWORD
```

Alternativa ao `target=/caminho` (monta arquivo) quando o app espera a
variável de ambiente diretamente, não um arquivo em `/run/secrets/`. Segue
a mesma regra 2 — o secret precisa existir antes via `podman secret
create`.

### 16. Container que precisa ler volumes de outros containers: `SecurityLabelDisable=true`

```ini
SecurityLabelDisable=true
```

Todo volume deste repositório usa `:Z` (rótulo SELinux **privado**,
exclusivo do container dono). Um container terceiro tentando ler esses
caminhos — mesmo só com `:ro` — toma `Permission denied`, porque `:Z` é
exclusivo por design. Ferramentas que precisam enxergar dados de vários
containers ao mesmo tempo (ex.: backup, ver [zerobyte](../../apps/zerobyte/README.pt-BR.md))
precisam desligar a confinação SELinux pra esse container específico.
Trade-off consciente, não usar por padrão.

### 17. Mexer manualmente em arquivo criado por container: `podman unshare`, não `sudo`

Rootless Podman mapeia os uids internos do container pra uma faixa de
uids "fantasma" no host (via user namespace, configurado em
`/etc/subuid`/`/etc/subgid`). Um arquivo criado pelo container num bind
mount pertence a esse uid mapeado (ex.: `100100`), não ao seu usuário
(`1000`) — `cp`/`mv`/`rm` direto dá `Permission denied`, porque pro
sistema de arquivos vocês são usuários completamente diferentes.
`sudo` não resolve (troca pra root real, que também não é dono). O
comando certo roda dentro do mesmo namespace que o Podman usa:

```bash
podman unshare mv origem destino
podman unshare rm caminho/arquivo
podman unshare ls -la caminho/
```

Qualquer comando de manipulação de arquivo (`mv`, `cp`, `chown`, `rm`...)
pode ser prefixado com `podman unshare` quando o alvo está dentro de
`volumes/` e pertence ao container, não a você.

**Copiar um arquivo novo *pra dentro*** (não só mover o que já existe)
precisa de um passo a mais — testado na prática: `podman unshare cp`
copia certo (dá acesso de escrita na pasta), mas o arquivo novo fica com
o **seu** uid, diferente dos vizinhos. Ajustar o dono depois, usando
`--reference` pra não precisar adivinhar o número do uid mapeado (varia
por serviço):

```bash
podman unshare cp /origem/arquivo.txt ~/.config/containers/volumes/<app>/<pasta>/
podman unshare chown --reference="$HOME/.config/containers/volumes/<app>/<pasta>/algum-arquivo-existente" \
  ~/.config/containers/volumes/<app>/<pasta>/arquivo.txt
```

### 18. `Label=` não aceita barra invertida no valor

Diferente do `$$` da regra 7 (que é sobre o systemd expandir `$`), aqui
quem recusa é o **parser do próprio Quadlet**: qualquer `\` dentro do
valor de um `Label=` (ex.: uma regex com `\d`, `\.`) faz a linha inteira
ser descartada — `quadlet-generator: unsupported escape char` no
journal, sem erro visível em `systemctl cat` nem em `podman inspect`
(o label simplesmente não existe no container, como se a linha nunca
tivesse sido escrita). Não tem escape que resolva — nem `\\` nem aspas
em volta do valor. Reescrever sem barra invertida: `[0-9]` no lugar de
`\d`, `.` sem escapar (aceitável em regex de filtro, não crítica).
Caso real em [`wud/`](../../apps/wud/README.pt-BR.md#wudtagincludewudtagtransform-nada-de--no-valor).

### 19. Uma variável só, pra várias units: `~/.config/environment.d/*.conf`

Quando vários `.container` diferentes precisam apontar pro **mesmo**
path variável (ex.: uma raiz de mídia compartilhada entre vários
serviços — ver [media-stack](../../apps/media-stack/README.pt-BR.md)), dá pra evitar editar
cada arquivo com o path hardcoded usando uma variável de ambiente do
systemd, não um `EnvironmentFile=` comum: `EnvironmentFile=` só injeta
env var *dentro do container*, tarde demais pra afetar como o Quadlet
resolve `Volume=`. O mecanismo certo é o `environment.d(5)` do próprio
systemd — `~/.config/environment.d/*.conf` define variáveis pro
ambiente do *manager* `systemd --user` inteiro, e essas variáveis ficam
disponíveis pra expansão `${VAR}` em `Volume=`/`Environment=` de
qualquer unit desse usuário:

```bash
mkdir -p ~/.config/environment.d
cat > ~/.config/environment.d/minha-app.conf <<EOF
MEU_PATH=/caminho/real
EOF
systemctl --user daemon-reload   # obrigatório — sem isso a variável
                                  # nova não existe pro manager ainda
```

```ini
Volume=${MEU_PATH}:/algo:Z
```

Testado na prática: `systemctl cat` mostra `${MEU_PATH}` literal (é só
o texto do arquivo, sem substituição) — o que confunde, parece que não
funcionou — mas `podman inspect` do container já reflete o path
resolvido de verdade, porque a expansão acontece no `ExecStart=` gerado,
na hora que o systemd de fato inicia o processo, não na hora de gerar o
arquivo. Testar com `podman inspect <container> --format
'{{json .Mounts}}'`, não confiar só no `systemctl cat`.

**Funciona em `Label=` também, não só em `Volume=`** — todo
`homepage.href` deste repositório usa `${TAILNET}` por isso:

```ini
Label=homepage.href=https://meu-app.${TAILNET}.ts.net
```

```bash
echo "TAILNET=meu-tailnet" > ~/.config/environment.d/tailnet.conf
systemctl --user daemon-reload
```

Mantém o repo publicável sem expor o nome da tailnet, e sobrevive a
`wget` de unit atualizada — diferente de editar o valor direto no
arquivo, que o próximo download sobrescreve. **Variável não definida
expande pra string vazia, em silêncio** (`https://meu-app..ts.net`) —
conferir com `podman inspect` depois de definir, ver
[homepage](../../apps/homepage/README.pt-BR.md#marcando-um-serviço-pra-aparecer-no-dashboard).

### 20. Hardening (`ReadOnly`/`DropCapability`): testar o app, não o container

`ReadOnly=true` + `DropCapability=ALL` são baratos e valem em qualquer
serviço que aceite — mas quais aceitam só se descobre testando. Estado
medido nos serviços deste repositório:

| Container | `ReadOnly` | Capabilities |
| --- | --- | --- |
| `actual` | yes | **none** + `User=1000` |
| `adguardhome` | yes | 1 (`net_bind_service`) |
| `any-sync-bundle` | no | 5 (`chown`, `dac_override`, `fowner`, `setgid`, `setuid`) |
| `audiobookshelf` | no | 4 (`chown`, `net_bind_service`, `setgid`, `setuid`) |
| `authentik-postgres` | no | 5 (`chown`, `dac_override`, `fowner`, `setgid`, `setuid`) |
| `authentik-worker` | no | podman default + `User=0` |
| `authentik` | yes | **none** + `User=1000` |
| `beszel-agent` | no | podman default |
| `beszel` | yes | **none** |
| `calibre-web-automated` | yes | 4 (`chown`, `net_bind_service`, `setgid`, `setuid`) |
| `cookcli` | yes | **none** |
| `copyparty` | yes | **none** + `User=1000` |
| `donetick` | yes | **none** + `User=1000` |
| `freshrss` | yes | 4 (`chown`, `net_bind_service`, `setgid`, `setuid`) |
| `frigate` | no | podman default |
| `ghost` | yes | **none** + `User=1000` |
| `gitea` | no | 4 (`chown`, `net_bind_service`, `setgid`, `setuid`) |
| `home-assistant` | yes | **none** |
| `homebox` | yes | **none** + `User=1000` |
| `homepage` | yes | **none** |
| `immich-machine-learning` | yes | **none** |
| `immich-postgres` | no | **none** + `User=999` |
| `immich-redis` | no | podman default |
| `immich` | yes | **none** |
| `invio` | no | **none** |
| `karakeep-chrome` | yes | **none** |
| `karakeep-meilisearch` | yes | **none** |
| `karakeep` | yes | **none** |
| `lubelogger` | no | **none** |
| `mdrop` | yes | **none** |
| `media-stack-bazarr` | no | 4 (`chown`, `net_bind_service`, `setgid`, `setuid`) |
| `media-stack-deluge` | no | 4 (`chown`, `net_bind_service`, `setgid`, `setuid`) |
| `media-stack-dispatcharr` | no | podman default |
| `media-stack-downtify` | no | podman default |
| `media-stack-gluetun` | no | podman default |
| `media-stack-jellyfin` | no | podman default |
| `media-stack-lidarr` | no | 4 (`chown`, `net_bind_service`, `setgid`, `setuid`) |
| `media-stack-prowlarr` | no | 4 (`chown`, `net_bind_service`, `setgid`, `setuid`) |
| `media-stack-radarr` | no | 4 (`chown`, `net_bind_service`, `setgid`, `setuid`) |
| `media-stack-sabnzbd` | no | 4 (`chown`, `net_bind_service`, `setgid`, `setuid`) |
| `media-stack-seerr` | yes | **none** |
| `media-stack-sonarr` | no | 4 (`chown`, `net_bind_service`, `setgid`, `setuid`) |
| `memos` | yes | **none** + `User=1000` |
| `metube` | yes | **none** + `User=1000` |
| `monica` | no | podman default |
| `n8n` | no | **none** |
| `netbootxyz` | no | 6 (`chown`, `dac_override`, `fowner`, `net_bind_service`, `setgid`, `setuid`) |
| `nginx` | no | 4 (`chown`, `net_bind_service`, `setgid`, `setuid`) |
| `node-red` | no | **none** |
| `ntfy` | yes | **none** + `User=1000` |
| `omni-tools` | no | 4 (`chown`, `net_bind_service`, `setgid`, `setuid`) |
| `openwebui-ollama` | no | **none** |
| `openwebui` | no | **none** |
| `owncloud` | no | 6 (`chown`, `dac_override`, `fowner`, `net_bind_service`, `setgid`, `setuid`) |
| `owntracks-frontend` | no | podman default |
| `owntracks-mosquitto` | no | podman default |
| `owntracks-recorder` | no | podman default |
| `paperless-ngx-broker` | yes | **none** + `User=999` |
| `paperless-ngx-gotenberg` | yes | **none** |
| `paperless-ngx-tika` | yes | **none** |
| `paperless-ngx` | yes | **none** |
| `radicale` | yes | podman default |
| `stirling-pdf` | no | 5 (`chown`, `dac_override`, `fowner`, `setgid`, `setuid`) |
| `syncthing` | yes | **none** + `User=1000` |
| `traccar` | yes | **none** + `User=1000` |
| `tsdproxy` | no | **none** |
| `uptime-kuma` | yes | **none** + `User=1000` |
| `vaultwarden` | yes | 1 (`net_bind_service`) |
| `vaultzap` | yes | **none** |
| `wger` | yes | **none** |
| `wud` | yes | **none** |
| `zerobyte` | yes | **none** |
| `zigbee2mqtt-mosquitto` | yes | **none** + `User=1883` |
| `zigbee2mqtt` | yes | **none** |

A tabela é gerada a partir das próprias units — é o estado medido de cada
container, não um resumo. `podman default` quer dizer que o
`DropCapability=ALL` foi recusado e os 11 padrões do Podman continuam ali.

**Como cada linha foi medida** — a tabela diz *o que* está ligado, não até
onde aquilo foi verificado:

- **Exercitado de verdade** (o app respondeu por HTTP, o banco foi gravado, um
  arquivo foi convertido) — a maioria dos serviços de container único.
- **Medido com a imagem isolada** (volumes vazios, sem env real): foi o nível
  mais forte que ainda subiu, mas **não** exercita o app — `audiobookshelf`, `beszel`, `calibre-web-automated`, `freshrss`, `gitea`, `immich-machine-learning`, `lubelogger`, `n8n`, `nginx`, `node-red`, `openwebui-ollama`, `openwebui`, `paperless-ngx`. Confirmar de
  verdade ao instalar.
- **Não medido**: `owntracks-frontend` (não sobe isolado — sai sem o recorder
  alcançável, então a escada não distingue recusa de hardening de falta de
  dependência; com ReadOnly falha em "can't create /etc/nginx/nginx.conf") e
  `beszel-agent` (existe pra ler o host, então testá-lo isolado não diz nada —
  medir com o beszel no ar e as métricas ainda chegando).
- **Medido só até certo ponto**: o `zigbee2mqtt` chega na abertura do
  coordenador sem erro de permissão, mas não há coordenador Zigbee nesta
  máquina; o `home-assistant` foi medido com a instalação limpa — ligar
  integração que fale direto com hardware (Bluetooth, Zigbee por USB, mDNS)
  exige medir de novo.

Casos que a tabela não consegue mostrar:

- O `authentik-postgres` **não** aceita `User=999`, diferente do Postgres do
  immich: o entrypoint insiste em ajustar dono e permissão de
  `/var/lib/postgresql/data` e `/var/run/postgresql`, e com 3 capabilities
  ainda falha em "chmod: /var/run/postgresql".
- O `paperless-ngx-broker` é o oposto: `DropCapability=ALL` sozinho é recusado
  ("setpriv: setresuid failed") porque o entrypoint do Redis troca de usuário,
  mas com `User=999` passa o pacote completo.
- O `karakeep-chrome` tem a **maior superfície de ataque** daqui — abre
  qualquer URL que você salvar e roda com `--no-sandbox`, então a sandbox
  interna do Chrome está desligada e o hardening do container é a única camada
  que resta. Stateless, então ReadOnly não custa nada.

Três coisas que a tabela esconde, das nove medições feitas por último:

- **`Secret=` montado como arquivo não convive com `ReadOnly=true`.** O
  Podman não cria o ponto de montagem em `/run/secrets` com o raiz somente
  leitura, e nem um `Tmpfs=/run` resolve — a criação acontece antes do
  tmpfs valer. É o que trava o tsdproxy. No [vaultzap](../../apps/vaultzap/README.pt-BR.md) a
  saída foi trocar o secret pra `type=env`.
- **Medir com proxy no lugar do app engana.** O any-sync-bundle "passou"
  numa primeira medição que contava palavras no log: o Mongo do modo AIO
  subia, imprimia as linhas de boot e morria em seguida com `exit status
  14` — e o serviço ficou `failed` no host até eu reverter. Com o
  `Notify=healthy` como juiz, ele recusa `ReadOnly` **e**
  `DropCapability=ALL` sozinho.
- **O degrau mais alto pode passar onde o do meio falha.** O Ghost repetiu
  a inversão do metube: `DropCapability=ALL` sozinho morre em `failed
  switching to 'node'`, mas com `User=` o entrypoint não tem o que trocar
  e tudo funciona.

### Antes de conceder uma capability, teste o degrau de cima

As quatro capabilities mais pedidas aqui — `CHOWN`, `SETUID`, `SETGID` e
`NET_BIND_SERVICE` — aparecem quase sempre juntas, e pela mesma causa: o
entrypoint da imagem faz setup como root e depois vira o usuário da
aplicação. **Com `User=`, ele não tem o que ajustar nem pra quem trocar**,
e a necessidade some.

Varredura feita nos 14 serviços que pediam esse kit, testando
`User=1000` + `DropCapability=ALL`:

| Passa (foram pra zero capability) | Recusa, e onde o entrypoint escreve |
| --- | --- |
| memos, syncthing | nginx, omni-tools → `/etc/nginx/conf.d/default.conf` |
| | netbootxyz → `/var/lib/nginx/logs` |
| | owncloud → `/var/www/owncloud/custom` |
| | stirling-pdf → `/tmp/stirling-pdf` |
| | freshrss → `/etc/localtime` |
| | gitea, calibre-web-automated → lock do s6-overlay |
| | audiobookshelf, any-sync-bundle → exceção no start |

**A regra que sai daí:** `User=` funciona quando o entrypoint só escreve
nos volumes montados. Quando ele grava em `/etc`, `/var/lib` ou num `/tmp`
próprio — ou quando a imagem usa s6-overlay, que insiste em ser root — não
tem jeito, e o kit é o mínimo mesmo.

Uma quarta observação, do **zigbee2mqtt**: é o método.
`podman diff` depois de um start mostrou que o app só escreve no bind de
`/app/data`, o que responde "cabe ReadOnly?" sem precisar exercitar nada.
Vale a pena antes de partir pro teste caro.

Outra, mais geral: quando o entrypoint da imagem troca de usuário
(`gosu`/`usermod`/`setpriv`), às vezes **desligar** esse mecanismo sai
mais barato que conceder as três capabilities que ele pede — desde que
rodar como uid 0 dentro do container seja aceitável (em rootless isso é o
seu próprio uid no host, não root de verdade).

**A armadilha: "o container subiu" não é o teste.** O caso que ensinou
isso aqui foi um serviço PHP+nginx que já esteve no repositório: com
`CHOWN,SETUID,SETGID,NET_BIND_SERVICE` ele fica `running` e o nginx
atende — mas o php-fpm morre em silêncio e toda página vira 502. Só
apareceu quando o teste passou a exercitar o app de verdade:

```bash
podman run -d --name t --cap-drop=ALL --cap-add=... <imagem>
sleep 14
podman exec t curl -sf -o /dev/null -w "%{http_code}" http://127.0.0.1:80/
```

`DAC_OVERRIDE`+`FOWNER` eram o que faltava. Sem exercitar o app, o
hardening teria ido pro repositório quebrando o serviço.

**Erro no `exec` = capability gravada no binário.** Se o container morre
com `exec /caminho/do/binario: operation not permitted` — falhando *ao
executar*, não durante a execução — a causa não é o programa pedir a
capability em runtime: é o **arquivo** carregar uma *file capability*. O
Linux recusa executar binário com capability que não esteja no bounding
set. Foi o caso do adguardhome, cujo binário tem
`cap_net_bind_service=eip` (confirmado com `getcap`). Devolver a
capability resolve; procurar o pedido no código, não.

**Padrões que se repetem:**

- **Porta <1024 dentro do container** exige `NET_BIND_SERVICE` — vale
  mesmo em rootless, e é o caso de qualquer imagem que sirva na 80
  interna (vaultwarden, nginx). **Antes de conceder, ver se a app
  deixa mudar a porta**: o ntfy escuta na 80 por padrão, e
  `NTFY_LISTEN_HTTP=:2586` fez a necessidade sumir — zero capabilities
  no lugar de uma. Vale a mesma pergunta pro `gosu`/`usermod` do
  entrypoint e pro `setpriv`: às vezes desligar o mecanismo sai mais
  barato que atender o que ele pede.
- **Imagem que faz `chown`/`usermod` no entrypoint** (LinuxServer.io e
  parecidas) precisa de `CHOWN`+`SETUID`+`SETGID` no mínimo — **ou de
  `User=`**. O metube mostrou que a escada não é monotônica:
  `DropCapability=ALL` sozinho é recusado (`chown: ... Operation not
  permitted`), mas com `User=1000` o entrypoint não tem o que ajustar (o
  `PUID` da imagem já é 1000), o `chown` some, e o degrau **mais alto**
  passa. Não desistir no primeiro `chown` do log: testar o degrau
  seguinte antes de conceder a capability.
- **`ReadOnly` quebra** quando o entrypoint reescreve config no start
  (nginx é o caso clássico) ou quando a app grava fora dos volumes.
  `Tmpfs=/tmp` resolve a maioria dos casos de `/tmp`.

**Cuidado ao testar via `systemctl restart` em sequência**: 5 falhas
seguidas batem no rate limit do systemd (`start-limit-hit`) e a partir
daí *qualquer* start falha, inclusive o da configuração boa — dá a
impressão de que o hardening quebrou algo que na verdade funciona.
`systemctl --user reset-failed <app>` antes de cada tentativa.

**`UserNS=` não é hardening.** Em rootless o user namespace já existe
sempre; `keep-id` só decide qual uid aparece nos arquivos dos volumes
(regra 17). Adicionar onde a imagem faz `usermod` interno **quebra** —
usar só quando a imagem roda com uid fixo e não ajusta dono sozinha
(immich, node-red, jellyfin, seerr).

**`User=` é** — e é o de maior impacto, porque é o único que muda quem o
processo é **fora** do container. Medido aqui: uid 0 dentro mapeia pro
**seu** uid (1000) no host, então um escape alcança sua home, suas
chaves SSH e o socket do Podman. Um uid != 0 cai na faixa subuid
(`100999`), que não possui nada:

| config | uid no host |
| --- | --- |
| padrão | 1000 (você) |
| `UserNS=keep-id` | 1000 (você) |
| `User=1000` | **100999** |

Custo: o volume precisa do mesmo dono — `podman unshare chown -R
1000:1000 <volume>` (uid visto de *dentro* do namespace, não o 100999 do
host) — e mexer nele passa a exigir `podman unshare` (regra 17). Por
isso **não** vale onde a pasta é ponto de troca com você: o `inbox` do
[vaultzap](../../apps/vaultzap/README.pt-BR.md) ficaria inutilizável no uso diário, e é
justamente por isso que ele usa `keep-id`.

**Só funciona em imagem que não faça setup como root.** Testado:
uptime-kuma aceita (roda como `100999` hoje); karakeep não — o
s6-overlay pede `setgid`, depois `chown`, depois mais, e cada capability
devolvida anula o ganho. Capability pedida em cascata é sinal de parar,
não de insistir. Como `ReadOnly` e `User=` também se excluem em algumas
imagens, e o escape é o cenário pior, `User=` ganha quando dá pra ter
só um.

**`PidsLimit=`** — funciona aqui (o controller `pids` é o único
delegado neste host, ver regra 19) e contém fork bomb: um processo
comprometido não esgota a tabela de processos do host. Dimensionar pelo
uso real em repouso, que é de *threads*, não processos —
`cat /sys/fs/cgroup/.../pids.current`, não `podman top`. A diferença é
grande: um serviço Node típico daqui mostra 6 processos e 65 threads.
Folga de 4x resolve.

**`Tmpfs=/tmp` sem `size=` usa metade da RAM** — o default do kernel.
Medido aqui: `df -h /tmp` dentro do container mostra `7.8G` de limite num
host de 16GB, por container. Com vários serviços, um `/tmp` que encha
por bug ou abuso vira OOM no host inteiro. Sempre dimensionar:
`Tmpfs=/tmp:size=64M`. Quem só usa `/tmp` de passagem (wud, homepage,
vaultwarden — 0 em repouso) fica confortável em 64M; quem processa
arquivo precisa de mais (karakeep arquiva páginas inteiras, 256M;
vaultzap extrai `.zip`, 128M). Caso especial: Chrome com
`--disable-dev-shm-usage` passa a usar `/tmp` no lugar de `/dev/shm`, e
64M ali é a causa clássica de crash de renderização — o
`karakeep-chrome` fica em 512M.

**Volume `:ro` onde o app só lê** — o mais barato de todos, e o mais
esquecido. O homepage montava `config/` e `icons/` como `rw` sem
precisar; com `:ro` ele sobe igual e deixa de poder reescrever a própria
configuração se for comprometido.

**O que não vale aqui:** `Memory=` (o controller `memory` não está
delegado neste host — mesma razão pela qual o radicale não tem limite de
RAM), `SeccompProfile=` (o perfil padrão do Podman já cobre as syscalls
perigosas; um customizado quebra fácil pra ganho marginal) e `Mask=` (o
runtime já mascara `/proc/kcore` e afins).

Onde o hardening vale menos, independente de tudo isso: quem monta o
socket do Podman (homepage, wud, tsdproxy). Quem compromete esses cria
um container novo e privilegiado — as capabilities do container atual
não entram na conta. Fechar isso pede um proxy de socket somente-leitura,
não hardening de container.


### 21. Nem tudo vira Quadlet: software que precisa *ser* o host na rede usa `transactional-update`

Este repositório roda em cima de distros imutáveis (openSUSE MicroOS) —
mas "imutável" não quer dizer "tudo em container". A pergunta que decide
é: **esse software precisa ter identidade própria isolada (porta, dado,
rede dele), ou precisa ser indistinguível do host na rede (mesmo
hostname, mesma tabela de rotas, integrado ao DNS que os outros
processos do host também usam)?** No primeiro caso, Quadlet como sempre.
No segundo, `transactional-update pkg install <pacote>` — o mecanismo
nativo do MicroOS pra isso, que continua sendo reprodutível/reversível
(aplica num snapshot Btrfs novo no próximo boot, `transactional-update
rollback` desfaz), só que sem as camadas de isolamento que atrapalham
justamente o que esse tipo de software precisa fazer.

Caso concreto: **Tailscale como identidade do host** (não um app atrás
do [tsdproxy](../../apps/tsdproxy/README.pt-BR.md), que é outra coisa — isso continua sendo o
padrão pra publicar serviços). Rodar o `tailscaled` num container com
`--network=host` compartilha a interface de rede com o host (SSH via
tailnet funciona), mas **não** compartilha D-Bus/mount namespace — o
container não consegue integrar com o `systemd-resolved` do host, e o
MagicDNS fica quebrado pros próprios processos do host (outros peers da
tailnet ainda resolvem o nome deste host normalmente, quem quebra é a
resolução *saindo* deste host). Confirmado em pesquisa: até guias
dedicados a rodar Tailscale em distros imutáveis (openSUSE Kalpa) esbarram
na mesma limitação e não recomendam essa rota pra identidade primária do
host. `transactional-update pkg install tailscale` evita o problema
inteiro — ganha integração nativa com `systemd-resolved`/rotas, ao custo
de precisar de um reboot pra aplicar (normal pra esse tipo de pacote,
diferente de uma app que só precisa de `systemctl --user restart`).

### 22. Serviço com banco: SQLite sempre que o app suportar

Quando o projeto oferece **os dois** (SQLite e Postgres/MySQL/MariaDB),
aqui usa-se SQLite — mesmo que o `docker-compose.yml` oficial só mostre
o Postgres, o que é comum porque o compose de referência é escrito
pensando em instalação grande, com múltiplos usuários.

O que se ganha nesta escala (um usuário, uma máquina): **um container a
menos** (às vezes dois, quando o banco arrasta um Redis junto), um secret
a menos, e o backup vira `tar` do volume em vez de `pg_dump` com o
serviço no ar. E some a pior manutenção recorrente do repo — **major de
banco não é bump de tag**: subir Postgres 15→16 exige `pg_dump`/restore,
enquanto o arquivo SQLite acompanha o app.

Serviços aqui que já seguem isso: [Ghost](../../apps/ghost/README.pt-BR.md), [wger](../../apps/wger/README.pt-BR.md),
[Vaultwarden](../../apps/vaultwarden/README.pt-BR.md),
[Uptime Kuma](../../apps/uptime-kuma/README.pt-BR.md) e o [Paperless-ngx](../../apps/paperless-ngx/README.pt-BR.md) —
esse último pela **variante** do compose (`sqlite-tika.yml`, não
`postgres-tika.yml`), que é onde a escolha aparece quando o projeto
publica mais de um arquivo.

O contraexemplo é o [Immich](../../apps/immich/README.pt-BR.md), que só fala Postgres — e com
uma extensão de vetor que amarra a versão do banco à do app. Nem todo
projeto deixa escolher: o sinal costuma estar no schema ou na doc de
instalação (um `provider = "postgresql"` fixo no Prisma, por exemplo).
**Checar antes de assumir**, e registrar o porquê no README do serviço,
pra ninguém reabrir a discussão depois.

