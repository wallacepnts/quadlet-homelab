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
jobs/                o gerador de jobs, para ~/.local/bin
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

Cada job leva então duas URLs — o `zerobyte-jobs.py` abaixo as escreve sozinho;
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
dele pede. O `zerobyte-jobs.py` descobre isso e cria pela API:

```bash
# Uma chave de API em Settings -> API keys, salva onde o script procura
mkdir -p ~/.config/zerobyte
printf '%s' 'A_CHAVE' > ~/.config/zerobyte/api-key && chmod 600 ~/.config/zerobyte/api-key

zerobyte-jobs.py --url https://zerobyte.<your-tailnet>.ts.net            # mostra o plano
zerobyte-jobs.py --url https://zerobyte.<your-tailnet>.ts.net --apply
```

O modo sai do dado: arquivo SQLite vira `sqlite`, marca de Postgres ou Mongo
vira `stop`, o resto não precisa de gancho. Diretório que ele não consegue ler
também conta como `stop` — ali está o dado de um container com uid mapeado, e
chutar `none` faria backup de banco em uso.

Duas coisas ele avisa em vez de fazer: `stop` sem unit com aquele nome (o
`media-stack` é o caso — doze units dividem um diretório, e uma delas carrega
um Postgres), e a sua allowlist, que ele imprime mas não edita. Job cujo gancho
não estiver no `ZEROBYTE_HOOK_UNITS` recebe 404 e falha.

Só olha as pastas dos serviços deste repositório. O que mais houver em
`volumes/` é listado e deixado em paz — sem `install.ini` e sem unit, o modo
seria chute.

Um job `secrets` cobre o `~/.config/containers/secrets`. Restaurar um volume de
dados sem eles dá um serviço que sobe e não funciona: o token de administrador
do vaultwarden deixa de bater, o `JWT_SECRET` do excalidash desloga todo mundo.
É um job só porque um job do Zerobyte cobre um único diretório — `includePaths`
e `customResticParams` são juntados ao caminho do volume, e não alcançam fora
dele.

**Guarde a senha do repositório em outro lugar.** O Restic cifra o repositório
com ela, e essa senha é ela própria um arquivo dentro de `secrets/` — que agora
mora *dentro* do que ela destranca. Numa perda total essa cópia é inalcançável:
deixe-a num gerenciador de senhas, ou no papel.

Rodar de novo não muda nada — os jobs são casados pelo nome.

### Mais de um repositório

Com dois ou mais cadastrados, diga qual roda o backup; os outros viram espelho
de todos os jobs:

```bash
zerobyte-jobs.py --url ... --repository <shortId> --apply
zerobyte-jobs.py --url ... --repository <shortId> --no-mirror --apply   # sem espelhar
```

Espelho copia o snapshot pronto, em vez de repetir o backup: o serviço para uma
vez só, e o que chega na nuvem é o mesmo que foi verificado aqui.

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
