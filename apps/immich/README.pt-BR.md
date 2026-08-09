# Immich

<img src="https://cdn.jsdelivr.net/gh/homarr-labs/dashboard-icons/svg/immich.svg" width="64" height="64" alt="">

**[🇺🇸 Read in English](./README.md)**

Backup e organização de fotos/vídeos, com reconhecimento facial e busca smart.

## Instalar

```bash
qh immich            # mostra o plano
qh immich --apply
```

Abrir `http://<ip-do-host>:2283` ou `https://immich.<your-tailnet>.ts.net`.

<details>
<summary><b>Instalação manual</b></summary>

```bash
# 1. Baixar as units pra uma subpasta dedicada (sem precisar clonar o
#    repositório)
mkdir -p ~/.config/containers/systemd/immich
for f in immich-net.network immich-redis.container immich-postgres.container \
         immich-machine-learning.container immich.container; do
  wget -P ~/.config/containers/systemd/immich/ \
    "https://raw.githubusercontent.com/wallacepnts/quadlet-homelab/main/apps/immich/$f"
done

# 2. Diretórios de dados — bind mount exige que já existam antes do start
mkdir -p ~/.config/containers/volumes/immich/{upload,postgres,redis,ml-cache,ml-dotcache,ml-config}
podman unshare chown -R 999:999 ~/.config/containers/volumes/immich/postgres   # o Postgres roda com User=999

# 3. Secret — senha do Postgres, mesma usada nos dois containers
mkdir -p ~/.config/containers/secrets/immich
openssl rand -base64 24 | tr -d '\n' > ~/.config/containers/secrets/immich/db-password.txt
chmod 600 ~/.config/containers/secrets/immich/db-password.txt
podman secret create immich-db-password ~/.config/containers/secrets/immich/db-password.txt

# 4. Env não-secreto — baixar o exemplo
mkdir -p ~/.config/containers/env
wget -O ~/.config/containers/env/immich.env \
  https://raw.githubusercontent.com/wallacepnts/quadlet-homelab/main/apps/immich/.env.example

# 5. Subir (redis e postgres sobem primeiro via Requires=)
systemctl --user daemon-reload
systemctl --user start immich
```

</details>

## Arquivos

```
immich-machine-learning.container
immich-postgres.container
immich-redis.container
immich.container
immich-net.network
.env.example
install.ini
```

Units da stack:

- `immich-machine-learning`
- `immich-postgres`
- `immich-redis`
- `immich`
- `immich-n`

## Atualizar

```bash
qh immich --update --apply
```

Fixado em `8e8d64b405ce18f41b8e5ee20aa4687a8ed0022d1298f2ce31cdcf3a76e09411`, `bcf63357191b76a916ae5eb93464d65c07511da41e3bf7a8416db519b40b1c23`, `v3.1.0`. Nada atualiza sozinho — versão nova entra quando você
roda o comando acima.

## Backup

```bash
qh immich --backup --apply --out ~/backups
```

Ele para o serviço, empacota os dados, o `.env` e os secrets, e sobe de novo.
A frio de propósito: copiar banco vivo dá um arquivo que só falha na hora de
restaurar.

Pra restaurar, por cima dos dados atuais:

```bash
qh immich --restore ~/backups/immich-20260809-1200.tar.gz --apply
```

Ele pede que você digite `immich` pra confirmar, porque os dados atuais são
apagados antes de o arquivo ser extraído.

## Remover

```bash
qh immich --remove --apply           # para e tira, mantendo os dados
qh immich --remove --purge --apply   # e apaga volumes, secrets e .env
```

O `--purge` também pede o nome digitado. O nó da tailnet não é desregistrado
por isso — isso é no admin do Tailscale.

## Comandos

```bash
systemctl --user status immich
podman logs -f immich
```

## Créditos

[immich-app/immich](https://github.com/immich-app/immich) — AGPL-3.0.

[Documentação oficial](https://immich.app)
