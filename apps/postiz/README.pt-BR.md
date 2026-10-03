# Postiz

<img src="https://cdn.jsdelivr.net/gh/homarr-labs/dashboard-icons/svg/postiz.svg" width="64" height="64" alt="">

**[🇺🇸 Read in English](./README.md)**

Um agendador de redes sociais: você escreve o post uma vez, escolhe os canais e a
hora, e ele publica por você. O Instagram vem de dois jeitos — por uma página do
Facebook Business, ou standalone, direto numa conta profissional do Instagram —
junto com X, LinkedIn, Threads, TikTok, YouTube e outras.

**Leia [O Instagram precisa de uma URL pública para a mídia](#o-instagram-precisa-de-uma-url-pública-para-a-mídia)
antes de configurar um canal.** Ela decide se a publicação funciona numa
instalação só na tailnet.

## Instalação

```bash
qh postiz            # mostra o plano
qh postiz --apply
```

Depois abra `https://postiz.<your-tailnet>.ts.net` e crie sua conta. O primeiro
cadastro funciona e então a página fecha: o `DISABLE_REGISTRATION=true` está no
`.env` que a instalação grava. Medido: a primeira conta é aceita, uma segunda
tentativa é recusada com `400`, e o `can-register` passa a `false`. Para
acrescentar alguém depois, ponha `false`, reinicie, crie a conta e volte para
`true`.

O endereço tem que ser o da tailnet. O Postiz monta os links de login e de OAuth a
partir dele, e a Meta só aceita redirecionamento em HTTPS. Instalar com
`--access local` deixa o link da unit apontando para a tailnet do mesmo jeito.

<details>
<summary><b>Instalação manual (avançado)</b></summary>

```bash
# 1. Baixar as units (não precisa clonar o repositório)
mkdir -p ~/.config/containers/systemd/postiz ~/.config/containers/env
for f in postiz postiz-postgres postiz-redis postiz-temporal postiz-temporal-postgres; do
  wget -P ~/.config/containers/systemd/postiz/ \
    https://raw.githubusercontent.com/wallacepnts/quadlet-homelab/main/apps/postiz/$f.container
done
wget -P ~/.config/containers/systemd/postiz/ \
  https://raw.githubusercontent.com/wallacepnts/quadlet-homelab/main/apps/postiz/postiz-net.network
wget -O ~/.config/containers/env/postiz.env \
  https://raw.githubusercontent.com/wallacepnts/quadlet-homelab/main/apps/postiz/.env.example
chmod 600 ~/.config/containers/env/postiz.env

# 2. As pastas de dados, cada uma do usuário com que a imagem roda, e o
#    nginx.conf (veja "Entrando")
V=~/.config/containers/volumes/postiz
mkdir -p $V/postgres $V/redis $V/temporal-postgres $V/uploads $V/config
wget -O $V/config/nginx.conf \
  https://raw.githubusercontent.com/wallacepnts/quadlet-homelab/main/apps/postiz/nginx.conf
podman unshare chown -R 70:70   $V/postgres
podman unshare chown -R 999:999 $V/redis $V/temporal-postgres
podman unshare chown -R 33:33   $V/uploads $V/config/nginx.conf

# 3. Os segredos. A URL do banco é montada a partir da senha, então vem em segundo.
mkdir -p ~/.config/containers/secrets/postiz
openssl rand -hex 24 | tr -d '\n' | podman secret create postiz-db-password -
openssl rand -hex 24 | tr -d '\n' | podman secret create postiz-temporal-db-password -
printf 'postgresql://postiz-user:%s@postiz-postgres:5432/postiz' \
  "$(podman secret inspect --showsecret --format '{{.SecretData}}' postiz-db-password)" \
  | podman secret create postiz-database-url -
openssl rand -hex 32 | tr -d '\n' | podman secret create postiz-jwt-secret -

systemctl --user daemon-reload
systemctl --user start postiz
```

</details>

## Arquivos

```
postiz.container                    o app: nginx, backend, frontend, workers
postiz-postgres.container           o banco dele (Postgres 17)
postiz-redis.container              filas e cache (Valkey)
postiz-temporal.container           executa a publicação agendada
postiz-temporal-postgres.container  o banco do próprio Temporal (Postgres 16)
postiz-net.network
nginx.conf                          o da própria imagem, com o cookie de sessão corrigido
.env.example                        chave de cadastro, chaves da Meta, armazenamento de mídia
install.ini                         a receita dos segredos
```

Dados em `~/.config/containers/volumes/postiz/`: `postgres/`, `temporal-postgres/`,
`redis/` e `uploads/`.

## Entrando

**O Postiz não funciona atrás de um endereço `*.ts.net` do jeito que vem.** Ele grava o
cookie de sessão com `Domain=.ts.net`, o domínio registrável que calcula a partir do
`FRONTEND_URL`. O `ts.net` está na Public Suffix List, então todo navegador recusa um
cookie para ele. O que você vê: a senha é aceita (`POST /api/auth/login` responde
`200`) e a página volta para o formulário de login, de novo e de novo. Nenhum log diz
o porquê.

Isso não apareceu nos testes deste serviço, que rodaram em `localhost`.

A correção está no `nginx.conf` que esta pasta instala por cima do da própria imagem:
uma linha, `proxy_cookie_domain .ts.net $host;`, em cada um dos dois locais com proxy,
que reescreve esse `Domain` para o host que o navegador usou. Cookie de qualquer outro
domínio passa intacto. É o `var/docker/nginx.conf` do projeto na `v2.24.0` e nada
mais, então **ao subir de versão, compare os dois** e leve as duas linhas:

```bash
diff <(curl -s https://raw.githubusercontent.com/gitroomhq/postiz-app/v2.24.0/var/docker/nginx.conf) \
     <(sed -n '/^user /,$p' ~/.config/containers/volumes/postiz/config/nginx.conf)
```

## O Instagram precisa de uma URL pública para a mídia

Para publicar uma imagem ou um vídeo, o Postiz entrega ao Instagram uma **URL** e o
Instagram baixa o arquivo dela (`image_url=...` e `video_url=...` em
`instagram.provider.ts`). Com o armazenamento local padrão essa URL é
`https://postiz.<your-tailnet>.ts.net/uploads/...`, que os servidores do Instagram
não alcançam: ela só existe na sua tailnet. A documentação do Postiz diz o mesmo de
todo provedor que puxa mídia por URL, e recomenda um CDN.

Então o post é criado e agendado, e falha quando a hora chega. É o que o código e a
documentação mostram, **sem teste contra a Meta com uma conta real**, porque isso
exige o seu app da Meta.

A saída que a documentação do Postiz dá é o **Cloudflare R2**, um bucket com URL
pública: descomente o bloco no fim de `~/.config/containers/env/postiz.env`,
preencha os seis valores e rode `systemctl --user restart postiz`. O app em si
continua privado na tailnet. O R2 tem camada gratuita; precisa de uma conta na
Cloudflare.

## Conectando o Instagram

Os dois jeitos usam um app da Meta só, criado em
[developers.facebook.com](https://developers.facebook.com/apps/creation/) (tipo
*Other*). Ponha as chaves em `~/.config/containers/env/postiz.env` e rode
`systemctl --user restart postiz`.

| | Facebook Business | Standalone |
| --- | --- | --- |
| Precisa de | uma conta do Instagram ligada a uma página do Facebook | uma conta **profissional** do Instagram |
| Chaves | `FACEBOOK_APP_ID`, `FACEBOOK_APP_SECRET` | `INSTAGRAM_APP_ID`, `INSTAGRAM_APP_SECRET` |
| URI de redirecionamento | `https://postiz.<your-tailnet>.ts.net/integrations/social/instagram` | `https://postiz.<your-tailnet>.ts.net/integrations/social/instagram-standalone` |
| Produto da Meta | Facebook Login for Business | Instagram Business Login |

A documentação do Postiz pede a verificação da empresa só para apps **públicos**.
Enquanto as permissões avançadas do app não são aprovadas, só quem tem função nele
consegue conectar e publicar; então acrescente a conta em *Funções do app →
Adicionar pessoas → Instagram Tester* **e aceite o convite no Instagram**, em
*Configurações → Apps e sites*
([instagram.com/accounts/manage_access](https://www.instagram.com/accounts/manage_access/)).
Dois erros que isso evita:

- `Insufficient developer role`, ao conectar: a conta nunca foi adicionada como testadora.
- Um canal que conecta, mas cujos posts falham com erro de permissão: as permissões
  não estão aprovadas e a conta não tem função no app.

As permissões a pedir, passo a passo, estão no
[guia oficial](https://docs.postiz.com/self-host/providers/instagram).

## O que roda, e por que são cinco containers

O Postiz entrega o agendamento ao **Temporal**, um motor de workflows que guarda
cada post pendente num banco e o executa na hora, mesmo depois de um reinício. É por
isso que um agendador precisa de um segundo banco. O compose oficial traz ainda o
Elasticsearch para o Temporal; aqui ele não entra.

- **Sem Elasticsearch.** Medido: a visibilidade em SQL do Temporal dá conta, e é um
  container a menos. Custa um ajuste, `SKIP_ADD_CUSTOM_SEARCH_ATTRIBUTES=true`. Sem
  ele a imagem reserva dois atributos `Text` dos três que o banco permite, o Postiz
  precisa de mais dois, e o backend morre no boot com
  `Unable to create search attributes: cannot have more than 3 search attribute of type Text`.
- **Valkey no lugar do Redis 7.2**, como no resto deste repositório. Medido
  funcionando: conectado, sem erros. As imagens de Postgres são as do próprio compose.
- **Ficou de fora do compose:** o `spotlight` (depuração com Sentry), o
  `temporal-ui` e o `temporal-admin-tools`. O volume `/config` do compose também não
  é montado: nada no código o lê.

## Como ele parte, e o que faz a cada vez

A imagem sozinha tem 5,5 GB. A primeira partida leva de 25 a 50 segundos; a unit dá mais folga. Duas coisas no
comando de partida da própria imagem merecem ser sabidas:

- **Baixa o Prisma CLI do npm a cada partida** (`pnpm dlx prisma@6.5.0`, cerca de
  244 MB). O container precisa de internet ao subir, não só para publicar.
- **Depois roda `prisma db push --accept-data-loss`.** Não há histórico de
  migrações: uma atualização que mude o schema o aplica direto, e pode apagar
  colunas. Faça backup antes de toda atualização.

Usa cerca de **2 GB de RAM** (a soma do conjunto residente de cada processo, que
conta páginas compartilhadas duas vezes, então é um teto) e 197 processos em
repouso, mais uns 230 MB de tmpfs.

## Endurecimento

Tudo menos o container do Temporal é somente leitura, sem capabilities, e todos
rodam com usuário que não é root. Testado exercitando o app: cadastro, login, o
envio de uma imagem de 9 MB pelo buffer do nginx, um post agendado num canal e
executado pelo worker do Temporal, num banco novo e num já em uso.

- **O Postiz roda como `www-data` (`User=33`)**, que não precisa de capability
  nenhuma. Como root precisa de quatro (`CHOWN`, `DAC_OVERRIDE`, `SETGID`,
  `SETUID`) só para o nginx subir.
- **O `HOME` aponta para um tmpfs**, `/home/postiz`, que guarda os arquivos do pm2
  e o cache do pnpm. O `/root` da própria imagem é `0700`.
- **`PidsLimit=512`.** 197 em repouso, pico de 202: os 256 do repositório são
  apertados demais para este.
- **O Temporal não é somente leitura.** Ele renderiza a configuração em
  `/etc/temporal/config` a cada partida.

**Às vezes a página não carrega depois de uma partida.** O backend pode subir sem nunca
abrir a porta 3000, sem nada em log nenhum: o nginx responde `502`, o container fica
`starting` e o `pm2 list` mostra `backend online`. Medido na unit instalada: 1 partida em
4 (e 2 em 9 no laboratório com o cache em volume). Sem ajuda, o systemd desiste em
`TimeoutStartSec` (7 minutos) e parte de novo; para não esperar:

```bash
podman exec postiz pm2 restart backend      # abre a :3000 em uns 13 segundos
```

A causa não foi encontrada: o processo fica ocioso, com as conexões ao Redis e ao Temporal abertas.

Toda recusa, com o erro, está em
[as recusas](../../docs/pt-BR/endurecimento.md#recusas-registradas). Uma delas é fácil
de desfazer sem querer: o cache do pnpm tem que continuar em tmpfs. Medido com ele
em volume, o backend nunca abriu a porta 3000 em 2 de 9 partidas, sem nada em log
nenhum.

## Atualizar

```bash
qh postiz --backup --apply --out ~/backups    # antes: veja "Como ele parte"
qh postiz --update --apply
```

Fixado em `1.28.1`, `16.15`, `17.11-alpine`, `9.1.1-alpine3.24`, `v2.25.0`. Nada atualiza
sozinho. O Postgres segue o compose da versão do Postiz para a qual você vai, então
um salto de major da imagem dele é uma migração à parte.

## Backup

```bash
qh postiz --backup --apply --out ~/backups
```

Para as cinco units, empacota as quatro pastas e os segredos, e religa. A frio de
propósito: copiar banco em uso gera um arquivo que só falha na hora de restaurar. Os
posts agendados vivem no banco do Temporal, então vão junto.

## Remover

```bash
qh postiz --remove --apply           # para, mantém os dados
qh postiz --remove --purge --apply   # e apaga os volumes e os segredos
```

O nó da tailnet não é removido por aqui — isso é no admin do Tailscale.

## Comandos

```bash
systemctl --user status postiz postiz-temporal postiz-postgres postiz-redis postiz-temporal-postgres
podman logs -f postiz
podman exec postiz pm2 list                     # backend, frontend, orchestrator
podman exec postiz-temporal sh -c 'temporal workflow list --address $(hostname -i):7233'
```

Se um post falhar com `getaddrinfo EAI_AGAIN graph.facebook.com`, é o DNS da rede do
Podman, não o Postiz: na máquina em que isto foi testado, a primeira consulta depois
de um tempo parado estourava o prazo, enquanto o resolvedor do host nunca falhou (0
de 40 contra 1 em 20). O Postiz o mostra como *"The account is missing some
permissions"*, a mesma mensagem que dá num problema real de permissão.

## Créditos

[gitroomhq/postiz-app](https://github.com/gitroomhq/postiz-app) — AGPL-3.0

[Documentação oficial](https://docs.postiz.com)
