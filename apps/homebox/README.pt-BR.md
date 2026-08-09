# HomeBox

<img src="https://cdn.jsdelivr.net/gh/homarr-labs/dashboard-icons/svg/homebox.svg" width="64" height="64" alt="">

**[🇺🇸 Read in English](./README.md)**

Inventário doméstico — o que você tem, onde está, nota fiscal, manual e garantia, com busca e etiquetas.

## Instalar

```bash
qh homebox            # mostra o plano
qh homebox --apply
```

Abrir `http://<ip-do-host>:7745` ou `https://homebox.<your-tailnet>.ts.net`.

<details>
<summary><b>Instalação manual</b></summary>

```bash
# 1. Baixar a unit (sem precisar clonar o repositório)
mkdir -p ~/.config/containers/systemd
wget -P ~/.config/containers/systemd/ \
  https://raw.githubusercontent.com/wallacepnts/quadlet-homelab/main/apps/homebox/homebox.container

# 2. Diretório + dono correspondente ao User=1000 da unit.
#    `podman unshare` roda o chown DENTRO do user namespace, que é onde
#    o 1000 do container existe (no host isso vira 100999).
mkdir -p ~/.config/containers/volumes/homebox/data
podman unshare chown -R 1000:1000 ~/.config/containers/volumes/homebox/data

# 3. Secret obrigatório (ver acima)
mkdir -p ~/.config/containers/secrets/homebox
openssl rand -base64 48 | tr -d '\n' \
  > ~/.config/containers/secrets/homebox/api-key-pepper.txt
chmod 600 ~/.config/containers/secrets/homebox/api-key-pepper.txt
podman secret create homebox-api-key-pepper \
  ~/.config/containers/secrets/homebox/api-key-pepper.txt

# 4. Variáveis. Subir com o cadastro ABERTO pra criar a sua conta —
#    o passo 6 fecha depois.
mkdir -p ~/.config/containers/env
wget -O ~/.config/containers/env/homebox.env \
  https://raw.githubusercontent.com/wallacepnts/quadlet-homelab/main/apps/homebox/.env.example
sed -i 's/^HBOX_OPTIONS_ALLOW_REGISTRATION=false/HBOX_OPTIONS_ALLOW_REGISTRATION=true/' \
  ~/.config/containers/env/homebox.env

# 5. Subir
systemctl --user daemon-reload
systemctl --user start homebox
```

```bash
# 6. Fechar o cadastro depois de criar a sua conta
sed -i 's/^HBOX_OPTIONS_ALLOW_REGISTRATION=true/HBOX_OPTIONS_ALLOW_REGISTRATION=false/' \
  ~/.config/containers/env/homebox.env
systemctl --user restart homebox
# conferir: allowRegistration deve virar false
curl -s http://127.0.0.1:7745/api/v1/status | grep -o '"allowRegistration":[a-z]*'
```

</details>

## Arquivos

```
homebox.container
.env.example
install.ini
```

## Atualizar

```bash
qh homebox --update --apply
```

Fixado em `0.26.2`. Nada atualiza sozinho — versão nova entra quando você
roda o comando acima.

## Backup

```bash
qh homebox --backup --apply --out ~/backups
```

Ele para o serviço, empacota os dados, o `.env` e os secrets, e sobe de novo.
A frio de propósito: copiar banco vivo dá um arquivo que só falha na hora de
restaurar.

Pra restaurar, por cima dos dados atuais:

```bash
qh homebox --restore ~/backups/homebox-20260809-1200.tar.gz --apply
```

Ele pede que você digite `homebox` pra confirmar, porque os dados atuais são
apagados antes de o arquivo ser extraído.

## Remover

```bash
qh homebox --remove --apply           # para e tira, mantendo os dados
qh homebox --remove --purge --apply   # e apaga volumes, secrets e .env
```

O `--purge` também pede o nome digitado. O nó da tailnet não é desregistrado
por isso — isso é no admin do Tailscale.

## Comandos

```bash
systemctl --user status homebox
podman logs -f homebox
```

## Créditos

[sysadminsmedia/homebox](https://github.com/sysadminsmedia/homebox) — AGPL-3.0

[Documentação oficial](https://homebox.software)
