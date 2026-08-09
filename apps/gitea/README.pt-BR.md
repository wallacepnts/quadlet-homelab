# Gitea

<img src="https://cdn.jsdelivr.net/gh/homarr-labs/dashboard-icons/svg/gitea.svg" width="64" height="64" alt="">

**[🇺🇸 Read in English](./README.md)**

Servidor Git leve e completo — repositórios, issues, pull requests e CI numa interface só.

## Instalar

```bash
qh gitea            # mostra o plano
qh gitea --apply
```

Abrir `http://<ip-do-host>:3002` ou `https://gitea.<your-tailnet>.ts.net`.

<details>
<summary><b>Instalação manual</b></summary>

```bash
# 1. Baixar a unit (sem precisar clonar o repositório)
mkdir -p ~/.config/containers/systemd
wget -P ~/.config/containers/systemd/ \
  https://raw.githubusercontent.com/wallacepnts/quadlet-homelab/main/apps/gitea/gitea.container

# 2. Diretório de dados — bind mount exige que já exista antes do start
mkdir -p ~/.config/containers/volumes/gitea/data

# 3. Secrets — gerados com a própria imagem, formato específico do Gitea
#    (não é openssl rand genérico)
mkdir -p ~/.config/containers/secrets/gitea
podman run --rm docker.io/gitea/gitea:1.27.1 gitea generate secret SECRET_KEY \
  > ~/.config/containers/secrets/gitea/secret-key.txt
podman run --rm docker.io/gitea/gitea:1.27.1 gitea generate secret INTERNAL_TOKEN \
  > ~/.config/containers/secrets/gitea/internal-token.txt
chmod 600 ~/.config/containers/secrets/gitea/*.txt

podman secret create gitea-secret-key ~/.config/containers/secrets/gitea/secret-key.txt
podman secret create gitea-internal-token ~/.config/containers/secrets/gitea/internal-token.txt

# 4. Env não-secreto — baixar o exemplo (pré-preenche o assistente de
#    instalação: DB e domínio já vêm certos, só falta criar a conta admin
#    na UI)
mkdir -p ~/.config/containers/env
wget -O ~/.config/containers/env/gitea.env \
  https://raw.githubusercontent.com/wallacepnts/quadlet-homelab/main/apps/gitea/.env.example
# editar ~/.config/containers/env/gitea.env: GITEA__server__DOMAIN e
# GITEA__server__ROOT_URL

# 5. Subir
systemctl --user daemon-reload
systemctl --user start gitea
```

</details>

## Arquivos

```
gitea.container
.env.example
install.ini
```

## Atualizar

```bash
qh gitea --update --apply
```

Fixado em `1.27.1`. Nada atualiza sozinho — versão nova entra quando você
roda o comando acima.

## Backup

```bash
qh gitea --backup --apply --out ~/backups
```

Ele para o serviço, empacota os dados, o `.env` e os secrets, e sobe de novo.
A frio de propósito: copiar banco vivo dá um arquivo que só falha na hora de
restaurar.

Pra restaurar, por cima dos dados atuais:

```bash
qh gitea --restore ~/backups/gitea-20260809-1200.tar.gz --apply
```

Ele pede que você digite `gitea` pra confirmar, porque os dados atuais são
apagados antes de o arquivo ser extraído.

## Remover

```bash
qh gitea --remove --apply           # para e tira, mantendo os dados
qh gitea --remove --purge --apply   # e apaga volumes, secrets e .env
```

O `--purge` também pede o nome digitado. O nó da tailnet não é desregistrado
por isso — isso é no admin do Tailscale.

## Comandos

```bash
systemctl --user status gitea
podman logs -f gitea
```

## Créditos

[go-gitea/gitea](https://github.com/go-gitea/gitea) — MIT

[Documentação oficial](https://gitea.com)
