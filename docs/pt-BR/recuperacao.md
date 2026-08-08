# Recuperação e migração

Dois cenários diferentes: a máquina morreu e você só tem os `.tar.gz`,
ou o servidor antigo ainda está de pé e você quer mudar de casa.

## A máquina morreu: recuperação do zero

Diferente de ["Migrando de outro servidor"](#migrando-de-outro-servidor),
que é mudança planejada com o servidor antigo de pé. Aqui você tem os
`.tar.gz` do `--backup` e mais nada.

**A ordem é instalar e só então restaurar.** O `--restore` não instala:
sem a unit no lugar, não há onde extrair nem o que iniciar. Ele recusa
com o comando que resolve, em vez de estourar no meio:

```
homebox: nada a fazer em `RESTAURAR (sobrescreve)`.
  !  homebox não está instalado — rode antes: python3 install.py homebox --apply
```

### 1. Host

O ["Passo zero"](./README.md#passo-zero-preparar-o-host): Podman rootless e as quatro
pastas. Tailscale e `TAILNET` **se** você usa a tailnet — senão, `--local`
em cada instalação.

### 2. tsdproxy primeiro, se usa tailnet

```bash
python3 install.py tsdproxy --apply
```

Antes do resto, porque é ele que torna os outros alcançáveis pelo nome. A
authkey é nova: os nós antigos ficam órfãos no admin do Tailscale e
precisam ser removidos à mão.

### 3. Serviço a serviço

```bash
python3 install.py <app> --apply
python3 install.py <app> --restore ~/backups/<app>-AAAAMMDD-HHMMSS.tar.gz --apply
```

O `--apply` recria unit, pastas, `.env` e secret; o `--restore` troca tudo
isso pelo conteúdo do backup — inclusive recriando o `podman secret`, que
não existiria numa máquina nova. Em stack, subir só o principal: o
`Requires=` puxa a cadeia (immich, karakeep, paperless-ngx, authentik,
owntracks, zigbee2mqtt).

### 4. Conferir

```bash
systemctl --user list-units 'podman-*' --failed
python3 updates.py            # o backup pode ser de uma versão atrás
```

### O que o backup não traz

- **As imagens** — o primeiro `start` baixa de novo, e é o passo lento.
- **A identidade na tailnet** — nó novo, nome igual, endereço diferente.
- **O que a seção de migração já lista**: identidade criptográfica do
  any-sync-bundle, e endereços gravados dentro dos dados (`DOMAIN` do
  vaultwarden, `ALLOWED_HOSTS` do wger, `externalAddr` do
  any-sync-bundle) — se o host mudou de nome, esses precisam de revisão.
- **Serviço que nunca teve backup.** O `--backup` é ad-hoc; o agendado é o
  [zerobyte](../../apps/zerobyte/README.pt-BR.md).

Esta ordem tem teste: o `test_install.py` roda o cenário inteiro numa
sandbox — instalar, gravar dado, backup, apagar o home, e recuperar —
pra que o runbook não envelheça sozinho.

## Migrando de outro servidor

Trazer um backup de um servidor diferente (não uma instalação nova do
zero — pra isso, ver "Implantando em outro servidor" de cada serviço) pra
este host.

### 1. No servidor antigo

Parar o serviço e gerar o backup como já documentado na seção Backup de
cada README — `tar` de `volumes/<app>/` — incluindo também
`~/.config/containers/secrets/<app>/` se o serviço usar secrets (ver
lista na seção "Apagar tudo" acima): sem eles os dados restaurados não
autenticam/decodificam.

### 2. Transferir

Os dois hosts já estão na mesma tailnet — `scp`/`rsync` direto entre eles
pela tailnet é o caminho mais simples: já é criptografado, sem storage
intermediário, sem configuração extra.

### 3. Neste servidor

Instalar o Quadlet normalmente, mas **sem dar o primeiro `start`** —
extrair o backup em `volumes/<app>/` antes disso, recriar os secrets a
partir dos arquivos copiados (`podman secret create` com o mesmo
conteúdo), só então `systemctl --user start`.

### O que checar antes de considerar migrado

- **Identidade criptográfica**: any-sync-bundle e tsdproxy geram
  identidade própria no primeiro run (`peerId`/`peerKey`; estado
  `tsnet`); o [Beszel](../../apps/beszel/README.pt-BR.md) é o mesmo caso (`hub-data/id_ed25519`,
  a chave que autentica todo agent registrado nesse hub). Trazer esses
  dados faz o servidor novo *ser* a continuação do antigo (mesmo nó,
  clientes/agents existentes reconhecem). Não trazer gera uma instância
  nova e independente — o oposto do que "Implantando em outro servidor"
  de cada serviço recomenda pra instalação do zero.
- **Endereços gravados nos dados**: `externalAddr` (any-sync-bundle),
  `DOMAIN` (vaultwarden), `NEXTAUTH_URL`/cookies (karakeep) referenciam
  o hostname do servidor antigo — ajustar pro endereço da tailnet deste
  host depois de restaurar.
- **Compatibilidade de versão**: se o servidor antigo estava numa versão
  bem atrás da tag pinada aqui, checar o changelog antes — principalmente
  immich (migrations do Postgres) e vaultwarden (schema do SQLite).
- **Não apagar o servidor antigo até confirmar** que o novo está saudável
  e acessível — se algo der errado na migração, ainda dá pra voltar.

