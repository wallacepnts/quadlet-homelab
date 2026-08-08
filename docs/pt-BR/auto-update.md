# Auto-update

Por que a maioria dos serviços daqui atualiza na mão, e o que precisa ser
verdade pra ligar o automático em um deles.

Desligado por padrão em todo o repositório (regra 9) — ativar é opt-in,
serviço por serviço, só quando as condições da regra 9 se cumprem
(`HealthCmd` real na imagem + sem dado crítico de terceiros em jogo, ou
disposição consciente de aceitar o risco). [`actual-budget`](../../apps/actual-budget/README.pt-BR.md)
e [`homepage`](../../apps/homepage/README.pt-BR.md) são os exemplos ativos hoje — usar os
READMEs deles como referência.

### 1. Ligar o timer (uma vez só, vale pra todo o host)

```bash
systemctl --user enable --now podman-auto-update.timer
```

Ele roda 1x/dia, checando todo container com o label
`io.containers.autoupdate` — não precisa religar por serviço, só essa vez.

### 2. Checar se o serviço é candidato (regra 9)

- Tem `HealthCmd` configurado no `.container`? Sem isso não existe
  rollback automático — o Podman aplica a atualização às cegas.
- Existe uma tag flutuante que faça sentido? Numa tag exata (`1.2.3`) o
  digest nunca muda, `AutoUpdate=` fica sem efeito nenhum. Checar se o
  projeto oferece algo tipo major.minor preso (ex.: `8.0`) antes de virar
  logo pra `:latest` — mas desconfiar mesmo assim (ver o caso real do
  MongoDB embutido no [any-sync-bundle](../../apps/any-sync-bundle/README.pt-BR.md#variantes):
  a versão vem fixa dentro da própria imagem, sem opção de pinar
  separado, e uma tag nova trouxe um MongoDB que morre com
  "illegal instruction" em kernel 6.19+ sem aviso nenhum).
- O dado ali é sensível/crítico o bastante pra preferir revisão manual
  antes de cada bump? (cofre de senhas, backend com estado real —
  provavelmente não vale a pena.)

### 3. Ativar no `.container`

```ini
Image=<registro>/<imagem>:<tag-flutuante>
AutoUpdate=registry
```

```bash
systemctl --user daemon-reload
systemctl --user restart <app>
```

### 4. Conferir e, se precisar, reverter

```bash
podman auto-update --dry-run              # prévia, sem aplicar nada
podman auto-update --rollback <container> # reverter manualmente
```

Fazer backup antes de qualquer bump de versão relevante — o rollback
automático só cobre "não ficou `healthy`", não cobre "ficou healthy mas
com um bug silencioso nos dados" (ver seção Backup de cada serviço).

### O que o AutoUpdate precisa pra funcionar direito

Três peças, as três obrigatórias:

1. **Tag flutuante** (`:latest`, `:2`, etc.) — `AutoUpdate=registry` compara
   o digest da tag contra o registry; numa tag pinada (`:v1.4.5`) o digest
   nunca muda, então nunca há nada pra atualizar.
2. **`AutoUpdate=registry`** no `.container` — sem essa linha o Podman
   nunca verifica, mesmo com tag flutuante.
3. **`podman-auto-update.timer` ativo** (`systemctl --user enable --now
   podman-auto-update.timer`) — é ele quem dispara a checagem
   periodicamente (diária, por padrão do systemd). Um timer só,
   compartilhado por todos os containers com `AutoUpdate=` deste usuário.

**A parte que faz isso ser seguro, não só automático: `HealthCmd` real.**
Rollback automático (voltar pra imagem anterior se a atualização quebrar)
só existe se o container tiver um healthcheck de verdade — o que por sua
vez exige shell/cliente HTTP dentro da imagem (`wget`/`curl`, ou uma
checagem TCP crua tipo a do lubelogger). Sem isso, `AutoUpdate=registry`
ainda troca a imagem e reinicia sozinho, só que **sem rede de segurança**:
se a build nova estiver quebrada, fica quebrada até alguém notar e
arrumar manualmente. Ver regra 9, no início deste README.

Checar candidatos antes de confiar cegamente: `podman auto-update
--dry-run`.

### Por que a maioria está desligado

Padrão deste repositório: tag explícita + bump manual por default,
auto-update é opt-in. Motivos específicos, documentados no README de
cada serviço (seção "Auto-update" ou "Atualizando as imagens"):

- **any-sync-bundle** — modo AIO com dado real (identidade do Anytype);
  `HealthCmd` cobre "o processo respondeu", não "a atualização não
  quebrou nada silenciosamente" (mesmo raciocínio de gitea/immich).
  Cada bump é testado à parte com dado descartável antes de tocar no
  dado real, coisa que auto-update automático não faz sozinho (ver
  README do serviço).
- **Karakeep** — a versão do Meilisearch é a que o `docker-compose.yml`
  oficial recomenda; trocar sem checar compatibilidade pode quebrar a
  busca. O Chrome segue a mesma regra, e o SQLite embutido é dado real do
  usuário (bookmarks, páginas arquivadas).
- **Immich** — fotos/vídeos e o índice de reconhecimento facial são dado
  real e irrecuperável do usuário; migrations de banco entre versões
  maiores não são incomuns, healthcheck "ok" não cobre isso.
- **Radicale** — calendários/contatos são dado real do usuário, e o banco
  embutido faz o healthcheck não cobrir migração de schema.
- **Syncthing** — mesmo raciocínio do ownCloud: arquivos sincronizados
  são dado real do usuário.
- **vaultwarden** — a imagem tem `wget`/`curl` (daria pra habilitar com
  rollback de verdade), mas é um cofre de senhas: revisão manual antes de
  atualizar é o padrão aqui de propósito, não uma limitação técnica.
- **zerobyte** — mesmo raciocínio do vaultwarden: guarda a senha de
  acesso a todos os outros backups, prefiro revisão manual mesmo tendo
  `HealthCmd` real.
- **lubelogger** — imagem Ubuntu sem `curl`/`wget`; o `HealthCmd` usa uma
  checagem TCP crua (regra 13), então nem entra na conversa de
  auto-update com rollback de verdade sem trocar a estratégia de
  healthcheck primeiro.
- **Calibre-Web-Automated** — mesmo raciocínio do vaultwarden: banco
  (`metadata.db`) + biblioteca são dado real do usuário, revisão manual
  antes de trocar de versão.
- **netboot.xyz** — tem `curl`/healthcheck real, mas prefiro conferir o
  changelog do webapp antes de trocar de tag (menu/boot loader sensível a
  mudança de versão).
- **Paperless-ngx** — mesmo raciocínio do vaultwarden: SQLite embutido
  (documentos + índice) é dado real do usuário, healthcheck HTTP não
  cobre migração de schema quebrada.
- **n8n** — mesmo raciocínio do vaultwarden: workflows/credenciais salvos são
  dado real do usuário, healthcheck HTTP não cobre uma atualização que
  quebre workflows existentes silenciosamente.
- **ownCloud** — mesmo raciocínio do karakeep: arquivos sincronizados
  são dado real do usuário; rodando em SQLite (modo não suportado em
  produção pelo próprio projeto), motivo a mais pra revisão manual.
- **tsdproxy** — sem motivo técnico específico, só não foi avaliado/ligado
  ainda (já usa uma tag de major flutuante, `:2`, mas sem `AutoUpdate=`
  isso não dispara sozinho).
- **AdGuard Home** — mesmo raciocínio do ownCloud/Radicale: DNS é
  infraestrutura crítica pra rede inteira, se cair ninguém resolve nome
  nenhum; revisão manual antes de trocar de versão, apesar de ter
  `HealthCmd` real.
- **Audiobookshelf** — mesmo raciocínio do vaultwarden: progresso de
  leitura/biblioteca é dado real do usuário.
- **Beszel**, **nginx**, **Ollama/Open WebUI** — todos com `HealthCmd`
  real (daria pra habilitar `AutoUpdate=registry` com rollback
  funcional), mas ainda não avaliados/ligados por padrão, mesmo
  raciocínio do tsdproxy.
- **FreshRSS** — mesmo raciocínio do vaultwarden: artigos
  lidos/receitas salvas são dado real do usuário.
- **Authentik** — usuários/grupos/configuração de SSO são dado real;
  `server` tem `HealthCmd`, mas revisão manual antes de atualizar,
  ainda mais sensível por ser infraestrutura de autenticação.
- **Monica** — caso à parte: **não tem tag fixa pra auto-update
  comparar contra** (só `:main`), ver seção própria do
  [README do serviço](../../apps/monica/README.pt-BR.md#tag-flutuante--exceção-consciente-à-regra-9).

