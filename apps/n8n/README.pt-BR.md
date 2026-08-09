# n8n

<img src="https://cdn.jsdelivr.net/gh/homarr-labs/dashboard-icons/svg/n8n.svg" width="64" height="64" alt="">

**[🇺🇸 Read in English](./README.md)**

Automação de workflows via editor visual de nós.

## Instalar

```bash
qh n8n            # mostra o plano
qh n8n --apply
```

Abrir `http://<ip-do-host>:5678` ou `https://n8n.<your-tailnet>.ts.net`.

<details>
<summary><b>Instalação manual</b></summary>

```bash
# 1. Baixar a unit (sem precisar clonar o repositório)
mkdir -p ~/.config/containers/systemd
wget -P ~/.config/containers/systemd/ \
  https://raw.githubusercontent.com/wallacepnts/quadlet-homelab/main/apps/n8n/n8n.container

# 2. Diretório de dados — bind mount exige que já exista antes do start
mkdir -p ~/.config/containers/volumes/n8n/data

# 3. Secret — chave de criptografia das credenciais salvas nos workflows
#    (tokens de API, senhas etc.). Gerar explícito em vez de deixar o
#    n8n gerar sozinho no primeiro start, pra ter o valor documentado.
mkdir -p ~/.config/containers/secrets/n8n
openssl rand -hex 32 | tr -d '\n' > ~/.config/containers/secrets/n8n/encryption-key.txt
chmod 600 ~/.config/containers/secrets/n8n/encryption-key.txt
podman secret create n8n-encryption-key ~/.config/containers/secrets/n8n/encryption-key.txt

# 4. Env não-secreto — baixar o exemplo
mkdir -p ~/.config/containers/env
wget -O ~/.config/containers/env/n8n.env \
  https://raw.githubusercontent.com/wallacepnts/quadlet-homelab/main/apps/n8n/.env.example

# 5. Subir
systemctl --user daemon-reload
systemctl --user start n8n
```

</details>

## Arquivos

```
n8n.container
.env.example
install.ini
```

## Atualizar

```bash
qh n8n --update --apply
```

Fixado em `2.33.7`. Nada atualiza sozinho — versão nova entra quando você
roda o comando acima.

## Backup

```bash
qh n8n --backup --apply --out ~/backups
```

Ele para o serviço, empacota os dados, o `.env` e os secrets, e sobe de novo.
A frio de propósito: copiar banco vivo dá um arquivo que só falha na hora de
restaurar.

Pra restaurar, por cima dos dados atuais:

```bash
qh n8n --restore ~/backups/n8n-20260809-1200.tar.gz --apply
```

Ele pede que você digite `n8n` pra confirmar, porque os dados atuais são
apagados antes de o arquivo ser extraído.

## Remover

```bash
qh n8n --remove --apply           # para e tira, mantendo os dados
qh n8n --remove --purge --apply   # e apaga volumes, secrets e .env
```

O `--purge` também pede o nome digitado. O nó da tailnet não é desregistrado
por isso — isso é no admin do Tailscale.

## Comandos

```bash
systemctl --user status n8n
podman logs -f n8n
```

## Créditos

[n8n-io/n8n](https://github.com/n8n-io/n8n)

[Documentação oficial](https://n8n.io)
