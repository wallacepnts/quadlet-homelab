# wger

<img src="https://cdn.jsdelivr.net/gh/homarr-labs/dashboard-icons/svg/wger.svg" width="64" height="64" alt="">

**[🇺🇸 Read in English](./README.md)**

Planejamento e acompanhamento de treinos, com banco de exercícios e medidas corporais.

## Instalar

```bash
qh wger            # mostra o plano
qh wger --apply
```

Abrir `http://<ip-do-host>:8102` ou `https://wger.<your-tailnet>.ts.net`.

<details>
<summary><b>Instalação manual</b></summary>

```bash
# 1. Baixar a unit (sem precisar clonar o repositório)
mkdir -p ~/.config/containers/systemd
wget -P ~/.config/containers/systemd/ \
  https://raw.githubusercontent.com/wallacepnts/quadlet-homelab/main/apps/wger/wger.container

# 2. Diretórios + dono correspondente ao uid 1000 da imagem
mkdir -p ~/.config/containers/volumes/wger/{db,static,media}
podman unshare chown -R 1000:1000 ~/.config/containers/volumes/wger

# 3. Variáveis — trocar <your-tailnet> em ALLOWED_HOSTS e CSRF_TRUSTED_ORIGINS
mkdir -p ~/.config/containers/env
wget -O ~/.config/containers/env/wger.env \
  https://raw.githubusercontent.com/wallacepnts/quadlet-homelab/main/apps/wger/.env.example
${EDITOR:-vi} ~/.config/containers/env/wger.env

# 4. SECRET_KEY — assina sessão e cookie
mkdir -p ~/.config/containers/secrets/wger
openssl rand -hex 32 > ~/.config/containers/secrets/wger/secret-key.txt
chmod 600 ~/.config/containers/secrets/wger/secret-key.txt
podman secret create wger-secret-key ~/.config/containers/secrets/wger/secret-key.txt

# 5. Subir. O primeiro start roda TODAS as migrações do Django e coleta
#    os estáticos — leva minutos, daí TimeoutStartSec=300.
systemctl --user daemon-reload
systemctl --user start wger
podman logs -f wger    # acompanhar até parar de aplicar migração
```

</details>

## Arquivos

```
wger.container
.env.example
install.ini
```

## Atualizar

```bash
qh wger --update --apply
```

Fixado em `2.6.0`. Nada atualiza sozinho — versão nova entra quando você
roda o comando acima.

## Backup

```bash
qh wger --backup --apply --out ~/backups
```

Ele para o serviço, empacota os dados, o `.env` e os secrets, e sobe de novo.
A frio de propósito: copiar banco vivo dá um arquivo que só falha na hora de
restaurar.

Pra restaurar, por cima dos dados atuais:

```bash
qh wger --restore ~/backups/wger-20260809-1200.tar.gz --apply
```

Ele pede que você digite `wger` pra confirmar, porque os dados atuais são
apagados antes de o arquivo ser extraído.

## Remover

```bash
qh wger --remove --apply           # para e tira, mantendo os dados
qh wger --remove --purge --apply   # e apaga volumes, secrets e .env
```

O `--purge` também pede o nome digitado. O nó da tailnet não é desregistrado
por isso — isso é no admin do Tailscale.

## Comandos

```bash
systemctl --user status wger
podman logs -f wger
```

## Créditos

[wger-project/wger](https://github.com/wger-project/wger) — AGPL-3.0

[Documentação oficial](https://wger.de)
