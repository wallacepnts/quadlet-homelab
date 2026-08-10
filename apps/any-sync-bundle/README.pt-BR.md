# any-sync-bundle

<img src="https://cdn.jsdelivr.net/gh/homarr-labs/dashboard-icons/svg/anytype.svg" width="64" height="64" alt="">

**[🇺🇸 Read in English](./README.md)**

Backend do protocolo Any-Sync, que sincroniza os dados do Anytype entre dispositivos sem depender da nuvem da empresa.

## Instalar

```bash
qh any-sync-bundle            # mostra o plano
qh any-sync-bundle --apply
```

Abrir `http://<ip-do-host>:33010` ou `https://any-sync.<your-tailnet>.ts.net`.

<details>
<summary><b>Instalação manual</b></summary>

```bash
# 1. Baixar a unit (sem precisar clonar o repositório)
mkdir -p ~/.config/containers/systemd/any-sync
wget -P ~/.config/containers/systemd/any-sync/ \
  https://raw.githubusercontent.com/wallacepnts/quadlet-homelab/main/apps/any-sync-bundle/any-sync-bundle.container

# 2. Diretório de dados — bind mount do Podman não cria o diretório do
#    host sozinho (diferente do docker compose); sem isso o container
#    entra em crash-loop com "statfs: no such file or directory"
mkdir -p ~/.config/containers/volumes/any-sync-bundle/data

# 3. Env vars do container — baixar o exemplo e editar
mkdir -p ~/.config/containers/env
wget -O ~/.config/containers/env/any-sync-bundle.env \
  https://raw.githubusercontent.com/wallacepnts/quadlet-homelab/main/apps/any-sync-bundle/.env.example
# editar ~/.config/containers/env/any-sync-bundle.env: ANY_SYNC_BUNDLE_INIT_EXTERNAL_ADDRS

# 4. Subir
systemctl --user daemon-reload
systemctl --user start any-sync-bundle
loginctl enable-linger $(whoami)

# 5. Conferir
systemctl --user is-active any-sync-bundle
podman logs any-sync-bundle --tail 20   # procurar "AnySync Bundle is ready!"
```

</details>

## Arquivos

```
any-sync-bundle.container   unit
.env.example                ambiente
```

## Conectando o app do Anytype

O primeiro start escreve o `client-config.yml` no volume de dados — é ele que
aponta um cliente Anytype para cá em vez da nuvem da empresa. Importe no app
seguindo as [instruções do
Anytype](https://doc.anytype.io/anytype-docs/advanced/data-and-security/self-hosting/self-hosted#how-to-switch-to-a-self-hosted-network).

```bash
cat ~/.config/containers/volumes/any-sync-bundle/data/client-config.yml
```

Ele é regerado a cada start, então não precisa de backup. O
`bundle-config.yml`, ao lado, é o oposto: carrega as chaves privadas, e
perdê-lo é perder a rede.

## Atualizar

```bash
qh any-sync-bundle --update --apply
```

Fixado em `1.5.0-2026-07-17`. Nada atualiza sozinho — versão nova entra quando você
roda o comando acima.

## Backup

```bash
qh any-sync-bundle --backup --apply --out ~/backups
```

Ele para o serviço, empacota os dados, o `.env` e os secrets, e sobe de novo.
A frio de propósito: copiar banco vivo dá um arquivo que só falha na hora de
restaurar.

Para a cópia agendada, o Zerobyte também precisa encontrar este serviço
parado — o [gancho de backup](../zerobyte/README.pt-BR.md#gancho-de-backup)
faz isso, com `any-sync-bundle` na allowlist.

Pra restaurar, por cima dos dados atuais:

```bash
qh any-sync-bundle --restore ~/backups/any-sync-bundle-20260809-1200.tar.gz --apply
```

Ele pede que você digite `any-sync-bundle` pra confirmar, porque os dados atuais são
apagados antes de o arquivo ser extraído.

## Remover

```bash
qh any-sync-bundle --remove --apply           # para e tira, mantendo os dados
qh any-sync-bundle --remove --purge --apply   # e apaga volumes, secrets e .env
```

O `--purge` também pede o nome digitado. O nó da tailnet não é desregistrado
por isso — isso é no admin do Tailscale.

## Comandos

```bash
systemctl --user status any-sync-bundle
podman logs -f any-sync-bundle
```

## Créditos

[grishy/any-sync-bundle](https://github.com/grishy/any-sync-bundle) — MIT

[Documentação oficial](https://github.com/grishy/any-sync-bundle#readme)
