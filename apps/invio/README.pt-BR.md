# Invio

<img src="https://cdn.simpleicons.org/invoiceninja/888888" width="64" height="64" alt="">

**[🇺🇸 Read in English](./README.md)**

Emissão e controle de faturas self-hosted, com SQLite e sem depender de serviço externo.

## Instalar

```bash
qh invio            # mostra o plano
qh invio --apply
```

Abrir `http://<ip-do-host>:8106` ou `https://invio.<your-tailnet>.ts.net`.

<details>
<summary><b>Instalação manual</b></summary>

```bash
# 1. Baixar a unit (sem precisar clonar o repositório)
mkdir -p ~/.config/containers/systemd
wget -P ~/.config/containers/systemd/ \
  https://raw.githubusercontent.com/wallacepnts/quadlet-homelab/main/apps/invio/invio.container

# 2. Diretório de dados
mkdir -p ~/.config/containers/volumes/invio/data

# 3. Variáveis — trocar <your-tailnet> no ORIGIN
mkdir -p ~/.config/containers/env
wget -O ~/.config/containers/env/invio.env \
  https://raw.githubusercontent.com/wallacepnts/quadlet-homelab/main/apps/invio/.env.example
${EDITOR:-vi} ~/.config/containers/env/invio.env

# 4. Secrets — a senha do admin e a chave que assina a sessão. Não vão no
#    .env de propósito.
mkdir -p ~/.config/containers/secrets/invio
python3 -c "import secrets;print(secrets.token_urlsafe(18),end='')" \
  > ~/.config/containers/secrets/invio/admin-pass.txt
python3 -c "import secrets;print(secrets.token_hex(32),end='')" \
  > ~/.config/containers/secrets/invio/jwt-secret.txt
chmod 600 ~/.config/containers/secrets/invio/*.txt
podman secret create invio-admin-pass ~/.config/containers/secrets/invio/admin-pass.txt
podman secret create invio-jwt-secret ~/.config/containers/secrets/invio/jwt-secret.txt

# 5. Subir
systemctl --user daemon-reload
systemctl --user start invio
```

```bash
qh invio --apply
```

</details>

## Arquivos

```
invio.container
.env.example
install.ini
```

## Atualizar

```bash
qh invio --update --apply
```

Fixado em `v2.1.1`. Nada atualiza sozinho — versão nova entra quando você
roda o comando acima.

## Backup

```bash
qh invio --backup --apply --out ~/backups
```

Ele para o serviço, empacota os dados, o `.env` e os secrets, e sobe de novo.
A frio de propósito: copiar banco vivo dá um arquivo que só falha na hora de
restaurar.

Pra restaurar, por cima dos dados atuais:

```bash
qh invio --restore ~/backups/invio-20260809-1200.tar.gz --apply
```

Ele pede que você digite `invio` pra confirmar, porque os dados atuais são
apagados antes de o arquivo ser extraído.

## Remover

```bash
qh invio --remove --apply           # para e tira, mantendo os dados
qh invio --remove --purge --apply   # e apaga volumes, secrets e .env
```

O `--purge` também pede o nome digitado. O nó da tailnet não é desregistrado
por isso — isso é no admin do Tailscale.

## Comandos

```bash
systemctl --user status invio
podman logs -f invio
```

## Créditos

[kittendevv/Invio](https://github.com/kittendevv/Invio)

[Documentação oficial](https://github.com/kittendevv/Invio#readme)
