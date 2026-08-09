# Donetick

<img src="https://cdn.jsdelivr.net/gh/homarr-labs/dashboard-icons/svg/donetick.svg" width="64" height="64" alt="">

**[🇺🇸 Read in English](./README.md)**

Tarefas domésticas recorrentes — quem faz, com que frequência e quando vence.

## Instalar

```bash
qh donetick            # mostra o plano
qh donetick --apply
```

Abrir `http://<ip-do-host>:2021` ou `https://donetick.<your-tailnet>.ts.net`.

<details>
<summary><b>Instalação manual</b></summary>

```bash
# 1. Baixar a unit (sem precisar clonar o repositório)
mkdir -p ~/.config/containers/systemd
wget -P ~/.config/containers/systemd/ \
  https://raw.githubusercontent.com/wallacepnts/quadlet-homelab/main/apps/donetick/donetick.container

# 2. Diretórios
mkdir -p ~/.config/containers/volumes/donetick/{config,data}

# 3. Config — trocar o segredo do JWT e o domínio
wget -O ~/.config/containers/volumes/donetick/config/selfhosted.yaml \
  https://raw.githubusercontent.com/wallacepnts/quadlet-homelab/main/apps/donetick/selfhosted.yaml.example
sed -i "s|CHANGEME_openssl_rand_hex_24|$(openssl rand -hex 24)|" \
  ~/.config/containers/volumes/donetick/config/selfhosted.yaml
sed -i "s|<your-tailnet>|SEU-TAILNET-AQUI|g" \
  ~/.config/containers/volumes/donetick/config/selfhosted.yaml

# 4. Dono correspondente ao User=1000 da unit
podman unshare chown -R 1000:1000 ~/.config/containers/volumes/donetick

# 5. Subir
systemctl --user daemon-reload
systemctl --user start donetick
```

```bash
sed -i 's/^is_user_creation_disabled: false/is_user_creation_disabled: true/' \
  ~/.config/containers/volumes/donetick/config/selfhosted.yaml
systemctl --user restart donetick
```

</details>

## Arquivos

```
donetick.container
selfhosted.yaml.example
install.ini
```

## Atualizar

```bash
qh donetick --update --apply
```

Fixado em `v0.1.76`. Nada atualiza sozinho — versão nova entra quando você
roda o comando acima.

## Backup

```bash
qh donetick --backup --apply --out ~/backups
```

Ele para o serviço, empacota os dados, o `.env` e os secrets, e sobe de novo.
A frio de propósito: copiar banco vivo dá um arquivo que só falha na hora de
restaurar.

Pra restaurar, por cima dos dados atuais:

```bash
qh donetick --restore ~/backups/donetick-20260809-1200.tar.gz --apply
```

Ele pede que você digite `donetick` pra confirmar, porque os dados atuais são
apagados antes de o arquivo ser extraído.

## Remover

```bash
qh donetick --remove --apply           # para e tira, mantendo os dados
qh donetick --remove --purge --apply   # e apaga volumes, secrets e .env
```

O `--purge` também pede o nome digitado. O nó da tailnet não é desregistrado
por isso — isso é no admin do Tailscale.

## Comandos

```bash
systemctl --user status donetick
podman logs -f donetick
```

## Créditos

[donetick/donetick](https://github.com/donetick/donetick) — AGPL-3.0

[Documentação oficial](https://donetick.com)
