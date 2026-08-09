# Paperless-ngx

<img src="https://cdn.jsdelivr.net/gh/homarr-labs/dashboard-icons/svg/paperless-ngx.svg" width="64" height="64" alt="">

**[🇺🇸 Read in English](./README.md)**

Digitaliza, faz OCR e indexa documentos automaticamente, com busca full-text pra nunca mais procurar papel.

## Instalar

```bash
qh paperless-ngx            # mostra o plano
qh paperless-ngx --apply
```

Abrir `http://<ip-do-host>:8091` ou `https://paperless.<your-tailnet>.ts.net`.

<details>
<summary><b>Instalação manual</b></summary>

```bash
# 1. Baixar as units pra uma subpasta dedicada (sem precisar clonar o
#    repositório)
mkdir -p ~/.config/containers/systemd/paperless-ngx
for f in paperless-ngx-net.network paperless-ngx-broker.container \
         paperless-ngx-gotenberg.container paperless-ngx-tika.container \
         paperless-ngx.container; do
  wget -P ~/.config/containers/systemd/paperless-ngx/ \
    "https://raw.githubusercontent.com/wallacepnts/quadlet-homelab/main/apps/paperless-ngx/$f"
done

# 2. Diretórios de dados — bind mount exige que já existam antes do start
mkdir -p ~/.config/containers/volumes/paperless-ngx/{broker,data,media,export,consume}
podman unshare chown -R 999:999 ~/.config/containers/volumes/paperless-ngx/redis   # o broker roda com User=999

# 3. Secret — chave usada pra assinar sessões/tokens
mkdir -p ~/.config/containers/secrets/paperless-ngx
openssl rand -base64 64 | tr -d '\n' > ~/.config/containers/secrets/paperless-ngx/secret-key.txt
chmod 600 ~/.config/containers/secrets/paperless-ngx/secret-key.txt
podman secret create paperless-ngx-secret-key ~/.config/containers/secrets/paperless-ngx/secret-key.txt

# 4. Env não-secreto — baixar o exemplo, ajustar USERMAP_UID/GID pro
#    usuário que roda o Podman (mesmo dono dos volumes acima)
mkdir -p ~/.config/containers/env
wget -O ~/.config/containers/env/paperless-ngx.env \
  https://raw.githubusercontent.com/wallacepnts/quadlet-homelab/main/apps/paperless-ngx/.env.example
sed -i "s/^USERMAP_UID=.*/USERMAP_UID=$(id -u)/;s/^USERMAP_GID=.*/USERMAP_GID=$(id -g)/" \
  ~/.config/containers/env/paperless-ngx.env

# 5. Subir (broker/gotenberg/tika sobem primeiro via Requires=)
systemctl --user daemon-reload
systemctl --user start paperless-ngx
```

```bash
podman exec -it paperless-ngx python3 manage.py createsuperuser
```

</details>

## Arquivos

```
paperless-ngx-broker.container
paperless-ngx-gotenberg.container
paperless-ngx-tika.container
paperless-ngx.container
paperless-ngx-net.network
.env.example
install.ini
```

Units da stack:

- `paperless-ngx-broker`
- `paperless-ngx-gotenberg`
- `paperless-ngx-tika`
- `paperless-ngx`
- `paperless-ngx-n`

## Atualizar

```bash
qh paperless-ngx --update --apply
```

Fixado em `3.0.5`, `3.3.1.0`, `8.34`. Nada atualiza sozinho — versão nova entra quando você
roda o comando acima.

## Backup

```bash
qh paperless-ngx --backup --apply --out ~/backups
```

Ele para o serviço, empacota os dados, o `.env` e os secrets, e sobe de novo.
A frio de propósito: copiar banco vivo dá um arquivo que só falha na hora de
restaurar.

Pra restaurar, por cima dos dados atuais:

```bash
qh paperless-ngx --restore ~/backups/paperless-ngx-20260809-1200.tar.gz --apply
```

Ele pede que você digite `paperless-ngx` pra confirmar, porque os dados atuais são
apagados antes de o arquivo ser extraído.

## Remover

```bash
qh paperless-ngx --remove --apply           # para e tira, mantendo os dados
qh paperless-ngx --remove --purge --apply   # e apaga volumes, secrets e .env
```

O `--purge` também pede o nome digitado. O nó da tailnet não é desregistrado
por isso — isso é no admin do Tailscale.

## Comandos

```bash
systemctl --user status paperless-ngx
podman logs -f paperless-ngx
```

## Créditos

[paperless-ngx/paperless-ngx](https://github.com/paperless-ngx/paperless-ngx) — GPL-3.0.

[Documentação oficial](https://docs.paperless-ngx.com/)
