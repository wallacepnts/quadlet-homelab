Depois abra `https://postiz.<your-tailnet>.ts.net` e crie sua conta. O primeiro
cadastro funciona e então a página fecha: o `DISABLE_REGISTRATION=true` está no
`.env` que a instalação grava. Medido: a primeira conta é aceita, uma segunda
tentativa é recusada com `400`, e o `can-register` passa a `false`. Para
acrescentar alguém depois, ponha `false`, reinicie, crie a conta e volte para
`true`.

O endereço tem que ser o da tailnet. O Postiz monta os links de login e de OAuth a
partir dele, e a Meta só aceita redirecionamento em HTTPS. Instalar com
`--access local` deixa o link da unit apontando para a tailnet do mesmo jeito.

### Entrando

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

### O Instagram precisa de uma URL pública para a mídia

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

### Conectando o Instagram

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

### O que roda, e por que são cinco containers

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

### Como ele parte, e o que faz a cada vez

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

### Atualizar

O Postgres segue o compose da versão do Postiz para a qual você vai, então um salto de major da imagem dele é uma migração à parte.

### Backup

Para as cinco units, empacota as quatro pastas e os segredos, e religa. A frio de
propósito: copiar banco em uso gera um arquivo que só falha na hora de restaurar. Os
posts agendados vivem no banco do Temporal, então vão junto.

### Remover

O nó da tailnet não é removido por aqui — isso é no admin do Tailscale.
