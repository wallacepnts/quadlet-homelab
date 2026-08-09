# Vaultwarden

<img src="https://cdn.jsdelivr.net/gh/homarr-labs/dashboard-icons/svg/vaultwarden.svg" width="64" height="64" alt="">

**[🇺🇸 Read in English](./README.md)**

Cofre de senhas compatível com o protocolo do Bitwarden, leve o bastante pra rodar em qualquer lugar.

## Instalar

```bash
qh vaultwarden            # mostra o plano
qh vaultwarden --apply
```

Abrir `http://<ip-do-host>:8082` ou `https://vaultwarden.<your-tailnet>.ts.net`.

<details>
<summary><b>Instalação manual</b></summary>

```bash
# 1. Baixar a unit (sem precisar clonar o repositório)
mkdir -p ~/.config/containers/systemd
wget -P ~/.config/containers/systemd/ \
  https://raw.githubusercontent.com/wallacepnts/quadlet-homelab/main/apps/vaultwarden/vaultwarden.container

# 2. Diretório de dados — bind mount exige que já exista antes do start
mkdir -p ~/.config/containers/volumes/vaultwarden/data

# 3. ADMIN_TOKEN como hash Argon2id (não texto puro) — é a forma
#    recomendada pelo próprio projeto. O comando oficial `vaultwarden
#    hash` exige TTY interativo (não dá pra automatizar em script), então
#    geramos o hash equivalente em Python com os MESMOS parâmetros do
#    preset "bitwarden" que o binário usa (m=65540, t=3, p=4).
mkdir -p ~/.config/containers/secrets/vaultwarden
python3 - <<'PYEOF'
from argon2 import PasswordHasher
from argon2.low_level import Type
import secrets
import os

secrets_dir = os.path.expanduser("~/.config/containers/secrets/vaultwarden")
ph = PasswordHasher(time_cost=3, memory_cost=65540, parallelism=4, hash_len=32, salt_len=16, type=Type.ID)
raw_secret = secrets.token_urlsafe(32)
phc = ph.hash(raw_secret)

with open(f"{secrets_dir}/admin-token-raw.txt", "w") as f:
    f.write(raw_secret)
with open(f"{secrets_dir}/admin-token-hash.txt", "w") as f:
    f.write(phc)

print("Token admin (guardar em local seguro, é a SENHA do painel /admin):")
print(raw_secret)
PYEOF
chmod 600 ~/.config/containers/secrets/vaultwarden/*.txt

podman secret create vaultwarden-admin-token ~/.config/containers/secrets/vaultwarden/admin-token-hash.txt

# 4. Env não-secreto — baixar o exemplo e editar DOMAIN
mkdir -p ~/.config/containers/env
wget -O ~/.config/containers/env/vaultwarden.env \
  https://raw.githubusercontent.com/wallacepnts/quadlet-homelab/main/apps/vaultwarden/.env.example
# editar ~/.config/containers/env/vaultwarden.env: DOMAIN (e lembrar de
# trocar SIGNUPS_ALLOWED pra "false" depois de criar a primeira conta —
# ver seção Segurança abaixo)

# 5. Subir
systemctl --user daemon-reload
systemctl --user start vaultwarden
```

</details>

## Arquivos

```
vaultwarden.container
.env.example
install.ini
```

## Atualizar

```bash
qh vaultwarden --update --apply
```

Fixado em `1.37.1-alpine`. Nada atualiza sozinho — versão nova entra quando você
roda o comando acima.

## Backup

```bash
qh vaultwarden --backup --apply --out ~/backups
```

Ele para o serviço, empacota os dados, o `.env` e os secrets, e sobe de novo.
A frio de propósito: copiar banco vivo dá um arquivo que só falha na hora de
restaurar.

Pra restaurar, por cima dos dados atuais:

```bash
qh vaultwarden --restore ~/backups/vaultwarden-20260809-1200.tar.gz --apply
```

Ele pede que você digite `vaultwarden` pra confirmar, porque os dados atuais são
apagados antes de o arquivo ser extraído.

## Remover

```bash
qh vaultwarden --remove --apply           # para e tira, mantendo os dados
qh vaultwarden --remove --purge --apply   # e apaga volumes, secrets e .env
```

O `--purge` também pede o nome digitado. O nó da tailnet não é desregistrado
por isso — isso é no admin do Tailscale.

## Comandos

```bash
systemctl --user status vaultwarden
podman logs -f vaultwarden
```

## Créditos

[dani-garcia/vaultwarden](https://github.com/dani-garcia/vaultwarden) — AGPL-3.0.

[Documentação oficial](https://github.com/dani-garcia/vaultwarden/wiki)
