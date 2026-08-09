# Hermes Agent

<img src="https://cdn.jsdelivr.net/gh/NousResearch/hermes-agent@main/website/static/img/logo.png" width="64" height="64" alt="">

**[🇺🇸 Read in English](./README.md)**

Agente de IA pessoal com habilidades e memória, expondo uma API compatível com a da OpenAI pros outros serviços chamarem.

## Instalar

```bash
qh hermes-agent            # mostra o plano
qh hermes-agent --apply
```

Abrir `http://<ip-do-host>:8642` ou `https://hermes.<your-tailnet>.ts.net`.

<details>
<summary><b>Instalação manual</b></summary>

```bash
# 1. Baixar a unit (sem precisar clonar o repositório)
mkdir -p ~/.config/containers/systemd
wget -P ~/.config/containers/systemd/ \
  https://raw.githubusercontent.com/wallacepnts/quadlet-homelab/main/apps/hermes-agent/hermes-agent.container

# 2. Diretórios
mkdir -p ~/.config/containers/volumes/hermes-agent/data
mkdir -p ~/.config/containers/env

# 3. Ambiente
wget -O ~/.config/containers/env/hermes-agent.env \
  https://raw.githubusercontent.com/wallacepnts/quadlet-homelab/main/apps/hermes-agent/.env.example

# 4. Secrets
podman secret create hermes-agent-api-key - <<< "$(python3 -c 'import secrets;print(secrets.token_urlsafe(32))')"
podman secret create hermes-agent-dashboard-password - <<< "$(python3 -c 'import secrets;print(secrets.token_urlsafe(24))')"
podman secret create hermes-agent-dashboard-secret - <<< "$(openssl rand -hex 32)"

# 5. Subir e rodar o assistente
systemctl --user daemon-reload
systemctl --user start hermes-agent
podman exec -it hermes-agent hermes setup
```

</details>

## Arquivos

```
hermes-agent.container
.env.example
install.ini
```

## Sem limite de memória

A unit define `PidsLimit=`, não `Memory=`. Limite de memória em unit rootless
exige o controlador de memória delegado ao gerenciador de usuário, e num host
onde ele não é, o container nem chega a ser criado:

```
memory.swap.max: no such file or directory
```

Pra saber se o seu host delega:

```bash
ls /sys/fs/cgroup/user.slice/user-$(id -u).slice/user@$(id -u).service/ | grep memory.max
```

## Atualizar

```bash
qh hermes-agent --update --apply
```

Fixado em `v2026.8.3`. Nada atualiza sozinho — versão nova entra quando você
roda o comando acima.

## Backup

```bash
qh hermes-agent --backup --apply --out ~/backups
```

Ele para o serviço, empacota os dados, o `.env` e os secrets, e sobe de novo.
A frio de propósito: copiar banco vivo dá um arquivo que só falha na hora de
restaurar.

Pra restaurar, por cima dos dados atuais:

```bash
qh hermes-agent --restore ~/backups/hermes-agent-20260809-1200.tar.gz --apply
```

Ele pede que você digite `hermes-agent` pra confirmar, porque os dados atuais são
apagados antes de o arquivo ser extraído.

## Remover

```bash
qh hermes-agent --remove --apply           # para e tira, mantendo os dados
qh hermes-agent --remove --purge --apply   # e apaga volumes, secrets e .env
```

O `--purge` também pede o nome digitado. O nó da tailnet não é desregistrado
por isso — isso é no admin do Tailscale.

## Comandos

```bash
systemctl --user status hermes-agent
podman logs -f hermes-agent
```

## Créditos

[NousResearch/hermes-agent](https://github.com/NousResearch/hermes-agent) — MIT

[Documentação oficial](https://hermes-agent.nousresearch.com)
