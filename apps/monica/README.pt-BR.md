# Monica

<img src="https://cdn.jsdelivr.net/gh/homarr-labs/dashboard-icons/svg/monica.svg" width="64" height="64" alt="">

**[🇺🇸 Read in English](./README.md)**

CRM pessoal — histórico de relacionamentos, contatos, lembretes.

## Instalar

```bash
qh monica            # mostra o plano
qh monica --apply
```

Abrir `http://<ip-do-host>:9092` ou `https://monica.<your-tailnet>.ts.net`.

<details>
<summary><b>Instalação manual</b></summary>

```bash
# 1. Baixar as units (sem precisar clonar o repositório)
mkdir -p ~/.config/containers/systemd
wget -P ~/.config/containers/systemd/ \
  https://raw.githubusercontent.com/wallacepnts/quadlet-homelab/main/apps/monica/monica.container

# 2. Diretório de dados — bind mount exige que já exista antes do start
mkdir -p ~/.config/containers/volumes/monica/storage

# 3. Env não-secreto — baixar o exemplo e EDITAR o APP_URL (trocar
#    "<your-tailnet>" pelo domínio real, ver abaixo) antes de subir
mkdir -p ~/.config/containers/env
wget -O ~/.config/containers/env/monica.env \
  https://raw.githubusercontent.com/wallacepnts/quadlet-homelab/main/apps/monica/.env.example

# 4. Secret — APP_KEY (formato "base64:" + 32 bytes aleatórios em base64,
#    igual ao que o próprio `artisan key:generate` produziria)
mkdir -p ~/.config/containers/secrets/monica
python3 -c "
import base64, os
print(f'base64:{base64.b64encode(os.urandom(32)).decode()}', end='')
" > ~/.config/containers/secrets/monica/app-key.txt
chmod 600 ~/.config/containers/secrets/monica/app-key.txt
podman secret create monica-app-key ~/.config/containers/secrets/monica/app-key.txt

# 5. Subir
systemctl --user daemon-reload
systemctl --user start monica
```

```bash
podman logs monica 2>&1 | grep -A5 "verify\|reset-password"
```

</details>

## Arquivos

```
monica.container
.env.example
install.ini
```

## Atualizar

```bash
qh monica --update --apply
```

Fixado em `main`. Nada atualiza sozinho — versão nova entra quando você
roda o comando acima.

## Backup

```bash
qh monica --backup --apply --out ~/backups
```

Ele para o serviço, empacota os dados, o `.env` e os secrets, e sobe de novo.
A frio de propósito: copiar banco vivo dá um arquivo que só falha na hora de
restaurar.

Pra restaurar, por cima dos dados atuais:

```bash
qh monica --restore ~/backups/monica-20260809-1200.tar.gz --apply
```

Ele pede que você digite `monica` pra confirmar, porque os dados atuais são
apagados antes de o arquivo ser extraído.

## Remover

```bash
qh monica --remove --apply           # para e tira, mantendo os dados
qh monica --remove --purge --apply   # e apaga volumes, secrets e .env
```

O `--purge` também pede o nome digitado. O nó da tailnet não é desregistrado
por isso — isso é no admin do Tailscale.

## Comandos

```bash
systemctl --user status monica
podman logs -f monica
```

## Créditos

[monicahq/monica](https://github.com/monicahq/monica) — AGPL-3.0

[Documentação oficial](https://beta.monicahq.com)
