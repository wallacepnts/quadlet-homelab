# ntfy

<img src="https://cdn.jsdelivr.net/gh/homarr-labs/dashboard-icons/svg/ntfy.svg" width="64" height="64" alt="">

**[🇺🇸 Read in English](./README.md)**

Servidor de notificações push — destino dos alertas do uptime-kuma, wud e zerobyte, com app no celular.

## Instalar

```bash
qh ntfy            # mostra o plano
qh ntfy --apply
```

Abrir `http://<ip-do-host>:2586` ou `https://ntfy.<your-tailnet>.ts.net`.

<details>
<summary><b>Instalação manual</b></summary>

```bash
# 1. Baixar a unit (sem precisar clonar o repositório)
mkdir -p ~/.config/containers/systemd
wget -P ~/.config/containers/systemd/ \
  https://raw.githubusercontent.com/wallacepnts/quadlet-homelab/main/apps/ntfy/ntfy.container

# 2. Diretórios + dono correspondente ao User=1000 da unit.
#    `podman unshare` roda o chown DENTRO do user namespace, que é onde
#    o 1000 do container existe (no host isso vira 100999).
mkdir -p ~/.config/containers/volumes/ntfy/{cache,lib}
podman unshare chown -R 1000:1000 ~/.config/containers/volumes/ntfy

# 3. Variáveis — editar NTFY_BASE_URL com o seu domínio da tailnet
mkdir -p ~/.config/containers/env
wget -O ~/.config/containers/env/ntfy.env \
  https://raw.githubusercontent.com/wallacepnts/quadlet-homelab/main/apps/ntfy/.env.example

# 4. Subir
systemctl --user daemon-reload
systemctl --user start ntfy

# 5. Criar o usuário administrador (imperativo, não versionado). A senha
#    vai por variável de ambiente pra não ficar no histórico do shell.
read -rs NTFY_PASSWORD && export NTFY_PASSWORD
podman exec -e NTFY_PASSWORD ntfy ntfy user add --role=admin admin
unset NTFY_PASSWORD
```

</details>

## Arquivos

```
ntfy.container
.env.example
```

## Atualizar

```bash
qh ntfy --update --apply
```

Fixado em `v2.27.0`. Nada atualiza sozinho — versão nova entra quando você
roda o comando acima.

## Backup

```bash
qh ntfy --backup --apply --out ~/backups
```

Ele para o serviço, empacota os dados, o `.env` e os secrets, e sobe de novo.
A frio de propósito: copiar banco vivo dá um arquivo que só falha na hora de
restaurar.

Pra restaurar, por cima dos dados atuais:

```bash
qh ntfy --restore ~/backups/ntfy-20260809-1200.tar.gz --apply
```

Ele pede que você digite `ntfy` pra confirmar, porque os dados atuais são
apagados antes de o arquivo ser extraído.

## Remover

```bash
qh ntfy --remove --apply           # para e tira, mantendo os dados
qh ntfy --remove --purge --apply   # e apaga volumes, secrets e .env
```

O `--purge` também pede o nome digitado. O nó da tailnet não é desregistrado
por isso — isso é no admin do Tailscale.

## Comandos

```bash
systemctl --user status ntfy
podman logs -f ntfy
```

## Créditos

[binwiederhier/ntfy](https://github.com/binwiederhier/ntfy) — Apache-2.0

[Documentação oficial](https://ntfy.sh)
