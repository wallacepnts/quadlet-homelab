# Open WebUI

<img src="https://cdn.jsdelivr.net/gh/homarr-labs/dashboard-icons/svg/open-webui.svg" width="64" height="64" alt="">

**[🇺🇸 Read in English](./README.md)**

Interface de chat web + servidor de LLMs locais, CPU-only por padrão (opções de GPU NVIDIA/AMD documentadas).

## Instalar

```bash
qh openwebui            # mostra o plano
qh openwebui --apply
```

Abrir `http://<ip-do-host>:3003` ou `https://ollama.<your-tailnet>.ts.net`.

<details>
<summary><b>Instalação manual</b></summary>

```bash
# 1. Baixar as units (sem precisar clonar o repositório)
mkdir -p ~/.config/containers/systemd/openwebui
wget -P ~/.config/containers/systemd/openwebui/ \
  https://raw.githubusercontent.com/wallacepnts/quadlet-homelab/main/apps/openwebui/openwebui-net.network \
  https://raw.githubusercontent.com/wallacepnts/quadlet-homelab/main/apps/openwebui/openwebui-ollama.container \
  https://raw.githubusercontent.com/wallacepnts/quadlet-homelab/main/apps/openwebui/openwebui.container

# 2. Diretórios de dados — bind mount exige que já existam antes do start
mkdir -p ~/.config/containers/volumes/openwebui/{ollama,webui}

# 3. Env não-secreto (Open WebUI)
mkdir -p ~/.config/containers/env
wget -O ~/.config/containers/env/openwebui.env \
  https://raw.githubusercontent.com/wallacepnts/quadlet-homelab/main/apps/openwebui/.env.example

# 4. Secret — chave usada pra assinar sessão de login do Open WebUI
mkdir -p ~/.config/containers/secrets/openwebui
python3 -c "import secrets; print(secrets.token_hex(32))" \
  > ~/.config/containers/secrets/openwebui/secret-key.txt
chmod 600 ~/.config/containers/secrets/openwebui/secret-key.txt
podman secret create openwebui-secret-key \
  ~/.config/containers/secrets/openwebui/secret-key.txt

# 5. Subir (Ollama primeiro, Open WebUI já sobe ele sozinho via Requires=,
#    mas dá pra fazer os dois num só start pelo principal)
systemctl --user daemon-reload
systemctl --user start openwebui
```

```bash
podman exec -it ollama ollama pull llama3.2
```

</details>

## Arquivos

```
openwebui-ollama.container
openwebui.container
openwebui-net.network
.env.example
install.ini
```

Units da stack:

- `openwebui-ollama`
- `openwebui`
- `openwebui-n`

## Atualizar

```bash
qh openwebui --update --apply
```

Fixado em `0.32.6`, `v0.11.0`. Nada atualiza sozinho — versão nova entra quando você
roda o comando acima.

## Backup

```bash
qh openwebui --backup --apply --out ~/backups
```

Ele para o serviço, empacota os dados, o `.env` e os secrets, e sobe de novo.
A frio de propósito: copiar banco vivo dá um arquivo que só falha na hora de
restaurar.

Pra restaurar, por cima dos dados atuais:

```bash
qh openwebui --restore ~/backups/openwebui-20260809-1200.tar.gz --apply
```

Ele pede que você digite `openwebui` pra confirmar, porque os dados atuais são
apagados antes de o arquivo ser extraído.

## Remover

```bash
qh openwebui --remove --apply           # para e tira, mantendo os dados
qh openwebui --remove --purge --apply   # e apaga volumes, secrets e .env
```

O `--purge` também pede o nome digitado. O nó da tailnet não é desregistrado
por isso — isso é no admin do Tailscale.

## Comandos

```bash
systemctl --user status openwebui
podman logs -f openwebui
```

## Créditos

[ollama/ollama](https://github.com/ollama/ollama) — MIT

[Documentação oficial](https://ollama.com)
