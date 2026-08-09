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
homepage.

### 20. Hardening (`ReadOnly`/`DropCapability`): testar o app, não o container

Aplicar sem testar:

```ini
PidsLimit=256
NoNewPrivileges=true
```

Depois testar, nesta ordem, parando no primeiro que o app recusar:

1. `DropCapability=ALL` — o log diz o que falta (`chown: Operation not
   permitted` → `AddCapability=CHOWN`). Porta abaixo de 1024 dentro do
   container precisa de `NET_BIND_SERVICE`.
2. `ReadOnly=true` + `Tmpfs=/tmp:size=64M` — quebra quando o entrypoint
   reescreve config no start, ou quando o init precisa de `/run`.
3. `User=<uid não-zero>` — o de maior impacto e o que mais quebra. Exige
   `podman unshare chown -R <uid>:<uid> <volume>`, e não funciona em imagem
   que faz `chown`/`usermod` no start.

**Container rodando não é o teste.** Exercitar o app:

```bash
podman run -d --name t --read-only --tmpfs /tmp --cap-drop=ALL <imagem> ...
sleep 14
podman exec t curl -sf -o /dev/null -w "%{http_code}" http://127.0.0.1:<porta>/
podman rm -f t
```

Dimensionar o `Tmpfs`: sem `size=` o kernel dá metade da RAM. 64M basta pra
quem só usa `/tmp` de passagem; medir com `podman exec <app> df -h /tmp` sob
uso real antes de aumentar.

`Secret=` montado como arquivo não convive com `ReadOnly=true` — usar
`type=env`.

`UserNS=` não é hardening. Ele só decide o dono dos arquivos em bind mount.

**Ao testar via systemd**: rodar `systemctl --user reset-failed <app>` antes de
cada tentativa. Cinco falhas seguidas batem no rate limit, e daí todo start
falha — inclusive o que funciona.

### 21. Nem tudo vira Quadlet: software que precisa *ser* o host na rede é pacote do sistema

A pergunta que decide: **este software precisa de identidade isolada (porta,
dados e rede próprios), ou precisa ser indistinguível do host na rede — mesmo
hostname, mesma tabela de rotas, integrado ao DNS que os outros processos do
host usam?** No primeiro caso, Quadlet como sempre. No segundo, o pacote da
distribuição.

O caso concreto aqui é o **Tailscale como identidade do host** — não um app
publicado atrás de um proxy, que é outra coisa e continua Quadlet. Rodar o
`tailscaled` num container com `--network=host` compartilha a interface de rede
(SSH pela tailnet funciona), mas **não** compartilha os namespaces de D-Bus e
mount: o container não consegue se integrar ao `systemd-resolved` do host, e o
MagicDNS quebra para os processos do próprio host. Outros peers continuam
resolvendo o nome desta máquina; o que quebra é a resolução *saindo* dela.

Instalar o pacote resolve: integração nativa com o `systemd-resolved` e com as
rotas, ao custo de um reboot nas distribuições que exigem.

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

