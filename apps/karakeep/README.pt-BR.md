# Karakeep

<img src="https://cdn.jsdelivr.net/gh/homarr-labs/dashboard-icons/svg/karakeep.svg" width="64" height="64" alt="">

**[🇺🇸 Read in English](./README.md)**

Gerenciador de bookmarks com busca full-text e arquivamento automático do conteúdo de cada página salva.

## Instalar

```bash
qh karakeep            # mostra o plano
qh karakeep --apply
```

Abrir `http://<ip-do-host>:8092` ou `https://karakeep.<your-tailnet>.ts.net`.

<details>
<summary><b>Instalação manual</b></summary>

```bash
# 1. Baixar as units pra uma subpasta dedicada (sem precisar clonar o
#    repositório)
mkdir -p ~/.config/containers/systemd/karakeep
for f in karakeep-net.network karakeep-chrome.container \
         karakeep-meilisearch.container karakeep.container; do
  wget -P ~/.config/containers/systemd/karakeep/ \
    "https://raw.githubusercontent.com/wallacepnts/quadlet-homelab/main/apps/karakeep/$f"
done

# 2. Diretórios de dados — bind mount exige que já existam antes do start
mkdir -p ~/.config/containers/volumes/karakeep/{data,meilisearch}

# 3. Segredos — gerados uma vez, nunca versionados. O mesmo
#    karakeep-meili-key é usado nos dois containers (meilisearch valida
#    a chave, karakeep autentica com ela).
mkdir -p ~/.config/containers/secrets/karakeep
openssl rand -base64 36 | tr -d '\n' > ~/.config/containers/secrets/karakeep/nextauth-secret.txt
openssl rand -base64 36 | tr -dc 'A-Za-z0-9' > ~/.config/containers/secrets/karakeep/meili-master-key.txt
chmod 600 ~/.config/containers/secrets/karakeep/*.txt

podman secret create karakeep-nextauth-secret ~/.config/containers/secrets/karakeep/nextauth-secret.txt
podman secret create karakeep-meili-key ~/.config/containers/secrets/karakeep/meili-master-key.txt

# 4. Env não-secreto — baixar o exemplo e editar NEXTAUTH_URL: precisa
#    bater exatamente com o endereço usado no navegador
mkdir -p ~/.config/containers/env
wget -O ~/.config/containers/env/karakeep.env \
  https://raw.githubusercontent.com/wallacepnts/quadlet-homelab/main/apps/karakeep/.env.example
# editar ~/.config/containers/env/karakeep.env: NEXTAUTH_URL

# 5. Subir (chrome e meilisearch sobem primeiro via Requires=)
systemctl --user daemon-reload
systemctl --user start karakeep
```

</details>

## Arquivos

```
karakeep-chrome.container
karakeep-meilisearch.container
karakeep.container
karakeep-net.network
.env.example
install.ini
```

Units da stack:

- `karakeep-chrome`
- `karakeep-meilisearch`
- `karakeep`
- `karakeep-n`

## Atualizar

```bash
qh karakeep --update --apply
```

Fixado em `0.33.1`, `124`, `v1.41.0`. Nada atualiza sozinho — versão nova entra quando você
roda o comando acima.

## Backup

```bash
qh karakeep --backup --apply --out ~/backups
```

Ele para o serviço, empacota os dados, o `.env` e os secrets, e sobe de novo.
A frio de propósito: copiar banco vivo dá um arquivo que só falha na hora de
restaurar.

Pra restaurar, por cima dos dados atuais:

```bash
qh karakeep --restore ~/backups/karakeep-20260809-1200.tar.gz --apply
```

Ele pede que você digite `karakeep` pra confirmar, porque os dados atuais são
apagados antes de o arquivo ser extraído.

## Remover

```bash
qh karakeep --remove --apply           # para e tira, mantendo os dados
qh karakeep --remove --purge --apply   # e apaga volumes, secrets e .env
```

O `--purge` também pede o nome digitado. O nó da tailnet não é desregistrado
por isso — isso é no admin do Tailscale.

## Comandos

```bash
systemctl --user status karakeep
podman logs -f karakeep
```

## Créditos

[karakeep-app/karakeep](https://github.com/karakeep-app/karakeep) — AGPL-3.0.

[Documentação oficial](https://karakeep.app)
