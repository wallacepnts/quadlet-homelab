# Authentik

<img src="https://cdn.jsdelivr.net/gh/homarr-labs/dashboard-icons/svg/authentik.svg" width="64" height="64" alt="">

**[🇺🇸 Read in English](./README.md)**

Servidor de identidade.

## Instalar

```bash
qh authentik            # mostra o plano
qh authentik --apply
```

Abrir `http://<ip-do-host>:9000` ou `https://authentik.<your-tailnet>.ts.net`.

<details>
<summary><b>Instalação manual</b></summary>

```bash
# 1. Baixar as units (sem precisar clonar o repositório)
mkdir -p ~/.config/containers/systemd/authentik
wget -P ~/.config/containers/systemd/authentik/ \
  https://raw.githubusercontent.com/wallacepnts/quadlet-homelab/main/apps/authentik/authentik-net.network \
  https://raw.githubusercontent.com/wallacepnts/quadlet-homelab/main/apps/authentik/authentik-postgres.container \
  https://raw.githubusercontent.com/wallacepnts/quadlet-homelab/main/apps/authentik/authentik.container \
  https://raw.githubusercontent.com/wallacepnts/quadlet-homelab/main/apps/authentik/authentik-worker.container

# 2. Diretórios de dados — bind mount exige que já existam antes do start
mkdir -p ~/.config/containers/volumes/authentik/{postgres,data,certs}

# 3. Secrets — senha do Postgres + chave de assinatura do Authentik.
#    IMPORTANTE: sem newline no arquivo (`print(..., end='')`, não
#    `print(...)` puro) — testado na prática, o Postgres tolera o
#    newline sobrando na senha (o script de init dele descarta), mas o
#    Authentik não: a autenticação falha em loop
#    ("password authentication failed") com a MESMA senha, só porque um
#    lado compara a string com \n no final e o outro sem.
mkdir -p ~/.config/containers/secrets/authentik
python3 -c "import secrets; print(secrets.token_urlsafe(32), end='')" \
  > ~/.config/containers/secrets/authentik/postgres-password.txt
python3 -c "import secrets; print(secrets.token_urlsafe(48), end='')" \
  > ~/.config/containers/secrets/authentik/secret-key.txt
chmod 600 ~/.config/containers/secrets/authentik/*.txt
podman secret create authentik-postgres-password \
  ~/.config/containers/secrets/authentik/postgres-password.txt
podman secret create authentik-secret-key \
  ~/.config/containers/secrets/authentik/secret-key.txt

# 4. Subir (o server já sobe o Postgres sozinho via Requires=)
systemctl --user daemon-reload
systemctl --user start authentik
systemctl --user start authentik-worker
```

</details>

## Arquivos

```
authentik-postgres.container
authentik-worker.container
authentik.container
authentik-net.network
install.ini
```

Units da stack:

- `authentik-postgres`
- `authentik-worker`
- `authentik`
- `authentik-n`

## Atualizar

```bash
qh authentik --update --apply
```

Fixado em `16-alpine`, `2026.5.6`. Nada atualiza sozinho — versão nova entra quando você
roda o comando acima.

## Backup

```bash
qh authentik --backup --apply --out ~/backups
```

Ele para o serviço, empacota os dados, o `.env` e os secrets, e sobe de novo.
A frio de propósito: copiar banco vivo dá um arquivo que só falha na hora de
restaurar.

Pra restaurar, por cima dos dados atuais:

```bash
qh authentik --restore ~/backups/authentik-20260809-1200.tar.gz --apply
```

Ele pede que você digite `authentik` pra confirmar, porque os dados atuais são
apagados antes de o arquivo ser extraído.

## Remover

```bash
qh authentik --remove --apply           # para e tira, mantendo os dados
qh authentik --remove --purge --apply   # e apaga volumes, secrets e .env
```

O `--purge` também pede o nome digitado. O nó da tailnet não é desregistrado
por isso — isso é no admin do Tailscale.

## Comandos

```bash
systemctl --user status authentik
podman logs -f authentik
```

## Créditos

[goauthentik/authentik](https://github.com/goauthentik/authentik) — MIT

[Documentação oficial](https://goauthentik.io)
