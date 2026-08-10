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
install.ini
.env.example
install.ini
```

## Gancho de backup

O Restic copiando um banco enquanto ele é escrito gera um arquivo que só
quebra na hora de restaurar. O gancho é o que torna a cópia agendada segura: o
Zerobyte chama antes e depois de cada job. Roda no python do host — uma unit
não consegue parar a si mesma de dentro do container que está sendo parado — e
não precisa de nada instalado.

| Modo | O que faz | Indisponibilidade |
| --- | --- | --- |
| `sqlite` | Copia cada banco pela API de backup online do SQLite para `<volume>/.dbbackup/`, que o Restic já cobre | **nenhuma** |
| `stop` | Para a unit antes da cópia e religa depois. É o padrão | a cópia inteira |

Prefira `sqlite`: parar não é nem suficiente para ele, porque o Restic ainda lê
o `.db` e o `-wal` como dois arquivos. Use `stop` para o que não tem dump
online, como o Mongo embutido do any-sync-bundle. Arquivo comum — foto,
documento, mídia — não precisa de nenhum dos dois.

O `qh zerobyte --apply` instala. Faltam três passos:

```bash
# 1. Sobre quais units ele pode agir, e como. O que não estiver na lista recebe 404.
systemctl --user edit --full zerobyte-backup-hook.service
#    Environment=ZEROBYTE_HOOK_UNITS=vaultwarden:sqlite,any-sync-bundle:stop

# 2. O token que o Zerobyte manda no cabeçalho X-Zerobyte-Hook-Secret
mkdir -p ~/.config/zerobyte-backup-hook
openssl rand -hex 32 > ~/.config/zerobyte-backup-hook/token
chmod 600 ~/.config/zerobyte-backup-hook/token

# 3. Subir
systemctl --user enable --now zerobyte-backup-hook.service
curl -s http://127.0.0.1:8765/healthz     # {"ok": true}
```

Depois aponte cada job para estas duas URLs, com o mesmo token como segredo. O
`WEBHOOK_ALLOWED_ORIGINS` no `.env` já nomeia o endereço — sem ele o Zerobyte
se recusa a salvar a URL.

```
http://host.containers.internal:8765/hooks/<unit>/pre-backup
http://host.containers.internal:8765/hooks/<unit>/post-backup
```

Quais units precisam — as que guardam banco de dados:

```bash
find ~/.config/containers/volumes -maxdepth 4 \
  \( -name "*.db" -o -name "*.sqlite*" -o -name "PG_VERSION" \) | cut -d/ -f7 | sort -u
```

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
