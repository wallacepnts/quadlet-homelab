# Zerobyte

<img src="https://cdn.jsdelivr.net/gh/homarr-labs/dashboard-icons/png/zerobyte.png" width="64" height="64" alt="">

**[🇺🇸 Read in English](./README.md)**

Automatiza backup (via Restic) dos dados de todos os outros serviços deste repositório.

## Instalar

```bash
qh zerobyte            # mostra o plano
qh zerobyte --apply
```

Abrir `http://<ip-do-host>:4096` ou `https://zerobyte.<your-tailnet>.ts.net`.

<details>
<summary><b>Instalação manual</b></summary>

```bash
# 1. Baixar a unit (sem precisar clonar o repositório)
mkdir -p ~/.config/containers/systemd
wget -P ~/.config/containers/systemd/ \
  https://raw.githubusercontent.com/wallacepnts/quadlet-homelab/main/apps/zerobyte/zerobyte.container

# 2. Diretórios — bind mount exige que já existam antes do start
mkdir -p ~/.config/containers/volumes/zerobyte/data
mkdir -p ~/backups/zerobyte-local
mkdir -p ~/.config/rclone

# 3. Configurar o destino rclone — interativo, roda no HOST (não no
#    container). Escolher o provedor (S3, Google Drive, Backblaze B2 etc.)
#    quando o assistente perguntar.
rclone config

# 4. APP_SECRET — chave de 32+ bytes usada pelo Zerobyte pra encriptar o
#    que ele guarda no próprio banco (não é a senha do repositório Restic
#    — essa é definida na hora de criar cada repositório, pela interface)
mkdir -p ~/.config/containers/secrets/zerobyte
openssl rand -hex 32 | tr -d '\n' > ~/.config/containers/secrets/zerobyte/app-secret.txt
chmod 600 ~/.config/containers/secrets/zerobyte/app-secret.txt
podman secret create zerobyte-app-secret ~/.config/containers/secrets/zerobyte/app-secret.txt

# 5. Env não-secreto — baixar o exemplo e editar
mkdir -p ~/.config/containers/env
wget -O ~/.config/containers/env/zerobyte.env \
  https://raw.githubusercontent.com/wallacepnts/quadlet-homelab/main/apps/zerobyte/.env.example
# editar ~/.config/containers/env/zerobyte.env: BASE_URL e RESTIC_HOSTNAME

# 6. Subir
systemctl --user daemon-reload
systemctl --user start zerobyte
```

</details>

## Arquivos

```
zerobyte.container   unit
backup-hook/         o gancho, para ~/.local/bin e systemd/user
jobs/                o gerador de jobs, atrás do `qh --zerobyte`
install.ini
.env.example
```

## Gancho de backup

O Zerobyte chama antes e depois de cada job, para o Restic nunca copiar um
banco no meio de uma escrita.

| Modo | O que faz | Indisponibilidade |
| --- | --- | --- |
| `sqlite` | Copia os bancos pela API de backup online do SQLite para `<volume>/.dbbackup/` | **nenhuma** |
| `stop` | Para a unit antes da cópia, religa depois. É o padrão | a cópia inteira |

```bash
# Sobre quais units ele pode agir, e como. O que não estiver na lista recebe 404.
systemctl --user edit --full zerobyte-backup-hook.service
#    Environment=ZEROBYTE_HOOK_UNITS=vaultwarden:sqlite,any-sync-bundle:stop

mkdir -p ~/.config/zerobyte-backup-hook
openssl rand -hex 32 > ~/.config/zerobyte-backup-hook/token
chmod 600 ~/.config/zerobyte-backup-hook/token

systemctl --user enable --now zerobyte-backup-hook.service
curl -s http://127.0.0.1:8766/healthz     # {"ok": true}
# Porta ocupada? O ZEROBYTE_HOOK_PORT muda; o WEBHOOK_ALLOWED_ORIGINS tem que acompanhar.
```

Cada job leva então duas URLs — o `qh --zerobyte` abaixo as escreve sozinho;
à mão só se você criar o job pela interface:

```
http://host.containers.internal:8766/hooks/<unit>/pre-backup
http://host.containers.internal:8766/hooks/<unit>/post-backup
```

`host.containers.internal` é o host visto de dentro do container: o gancho roda
no host, porque quem para uma unit é o `systemctl --user`, e isso um container
não alcança. `<unit>` diz sobre quem agir. O token vai no cabeçalho
`X-Zerobyte-Hook-Secret` — sem ele o gancho responde 401, e é o que impede que
qualquer coisa que chegue na porta 8766 pare os seus serviços.

### Criando os jobs

Um job por pasta dentro de `volumes/`, cada um com o modo de gancho que o dado
dele pede. O `qh --zerobyte` descobre isso e cria pela API. O endereço ele lê
do `BASE_URL` no `.env` do próprio serviço; o `--url` sobrescreve:

```bash
# Uma chave de API em Settings -> API keys, salva onde o script procura
mkdir -p ~/.config/zerobyte
printf '%s' 'A_CHAVE' > ~/.config/zerobyte/api-key && chmod 600 ~/.config/zerobyte/api-key

qh --zerobyte            # mostra o plano
qh --zerobyte --apply
```

O modo sai do dado: SQLite vira `sqlite`, marca de Postgres ou Mongo vira
`stop`, o resto não precisa de gancho. Pasta que ele não consegue ler também
conta como `stop` — é dado de container com uid mapeado.

Ele avisa em vez de fazer, em dois casos: `stop` sem unit com aquele nome (o
`media-stack`, cujas doze units dividem um diretório), e o
`ZEROBYTE_HOOK_UNITS`, que ele imprime mas não edita — job fora dessa lista
recebe 404 e falha. Pasta que não é de um serviço daqui é listada e deixada em
paz. Rodar de novo não muda nada: os jobs são casados pelo nome.

Todo job exclui `*.tmp`, `*.partial`, `lost+found`, `.Trash-*` e qualquer
diretório com um `CACHEDIR.TAG`. A lista é curta porque o descartável medido
nos volumes reais dá poucos megabytes — lista longa e chutada só acrescentaria
formas de perder algo que importava. O que o app sabe sobre o próprio dado vai
no `install.ini` dele:

```ini
[backup]
exclude =
    repositories
```

Essa é a do próprio zerobyte, e vale 15 MB por noite: repositório criado pela
interface cai dentro do volume de que este job faz backup.

Todo job leva também a mesma janela de retenção: 7 diários, 4 semanais, 6
mensais e as 3 últimas execuções. O Zerobyte aplica com `restic forget --prune`
logo depois de cada backup, então o espaço volta — não é só o snapshot sumir da
lista. Não há `keepHourly`: o agendamento é diário e ele nunca casaria.

O container mantém uma capacidade, a `DAC_READ_SEARCH`. Serviço que roda o
banco sob usuário próprio deixa arquivo de dono mapeado e modo 600 — com tudo
descartado, o restic lista o diretório e falha arquivo por arquivo
(`permission denied` no Mongo do any-sync-bundle). Ela fura só a checagem de
leitura; escrever seria `DAC_OVERRIDE`, que ele não tem, e os volumes estão
montados como somente-leitura de qualquer forma.

Um job `secrets` cobre o `~/.config/containers/secrets` — volume restaurado sem
eles dá serviço que sobe e não funciona.

**Guarde a senha do repositório em outro lugar.** Ela é um arquivo dentro de
`secrets/`, que agora mora *dentro* do que ela destranca: num gerenciador de
senhas, ou no papel.

### Avisos

Destino criado uma vez em **Settings → Notifications** (ntfy, e-mail, Telegram,
Gotify, Discord, Slack) é ligado em todos os jobs pelo mesmo comando, em falha e
em aviso. Em sucesso não: doze mensagens de "deu certo" por noite viram ruído
que você aprende a pular, e a que falhou vai junto — foi assim que um Mongo
passou um mês reportando `warning` sem ninguém ler.

### Mais de um repositório

Com dois ou mais cadastrados, diga qual roda o backup; os outros viram espelho
de todos os jobs:

```bash
qh --zerobyte --repository <shortId> --apply
qh --zerobyte --repository <shortId> --no-mirror --apply   # desliga o espelho
```

Espelho copia o snapshot pronto, em vez de repetir o backup: o serviço para uma
vez só, e o que chega na nuvem é o mesmo que foi verificado aqui. Ele
também dispara a primeira cópia, então o repositório novo se enche na hora e
não só na próxima execução. O `--no-mirror` tira o espelho de todos os jobs —
pela interface isso seria um a um.

## Atualizar

```bash
qh zerobyte --update --apply
```

Fixado em `v0.41.0`. Nada atualiza sozinho — versão nova entra quando você
roda o comando acima.

## Backup

```bash
qh zerobyte --backup --apply --out ~/backups
```

Ele para o serviço, empacota os dados, o `.env` e os secrets, e sobe de novo.
A frio de propósito: copiar banco vivo dá um arquivo que só falha na hora de
restaurar.

Pra restaurar, por cima dos dados atuais:

```bash
qh zerobyte --restore ~/backups/zerobyte-20260809-1200.tar.gz --apply
```

Ele pede que você digite `zerobyte` pra confirmar, porque os dados atuais são
apagados antes de o arquivo ser extraído.

## Remover

```bash
qh zerobyte --remove --apply           # para e tira, mantendo os dados
qh zerobyte --remove --purge --apply   # e apaga volumes, secrets e .env
```

O `--purge` também pede o nome digitado. O nó da tailnet não é desregistrado
por isso — isso é no admin do Tailscale.

## Comandos

```bash
systemctl --user status zerobyte
podman logs -f zerobyte
```

## Créditos

[nicotsx/zerobyte](https://github.com/nicotsx/zerobyte) — AGPL-3.0.

[Documentação oficial](https://zerobyte.app)
