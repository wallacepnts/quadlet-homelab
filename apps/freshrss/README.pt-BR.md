# FreshRSS

<img src="https://cdn.jsdelivr.net/gh/homarr-labs/dashboard-icons/svg/freshrss.svg" width="64" height="64" alt="">

**[🇺🇸 Read in English](./README.md)**

Agregador de feeds RSS/Atom self-hosted, com API compatível pra apps móveis.

## Instalar

```bash
qh freshrss            # mostra o plano
qh freshrss --apply
```

Abrir `http://<ip-do-host>:8104` ou `https://freshrss.<your-tailnet>.ts.net`.

<details>
<summary><b>Instalação manual</b></summary>

```bash
# 1. Baixar as units (sem precisar clonar o repositório)
mkdir -p ~/.config/containers/systemd
wget -P ~/.config/containers/systemd/ \
  https://raw.githubusercontent.com/wallacepnts/quadlet-homelab/main/apps/freshrss/freshrss.container

# 2. Diretório de dados — bind mount exige que já exista antes do start
mkdir -p ~/.config/containers/volumes/freshrss/data

# 3. Env não-secreto — baixar o exemplo, ajustar TZ/CRON_MIN se quiser
mkdir -p ~/.config/containers/env
wget -O ~/.config/containers/env/freshrss.env \
  https://raw.githubusercontent.com/wallacepnts/quadlet-homelab/main/apps/freshrss/.env.example

# 4. Subir
systemctl --user daemon-reload
systemctl --user start freshrss
```

</details>

## Arquivos

```
freshrss.container
.env.example
```

## Atualizar

```bash
qh freshrss --update --apply
```

Fixado em `1.29.1-alpine`. Nada atualiza sozinho — versão nova entra quando você
roda o comando acima.

## Backup

```bash
qh freshrss --backup --apply --out ~/backups
```

Ele para o serviço, empacota os dados, o `.env` e os secrets, e sobe de novo.
A frio de propósito: copiar banco vivo dá um arquivo que só falha na hora de
restaurar.

Pra restaurar, por cima dos dados atuais:

```bash
qh freshrss --restore ~/backups/freshrss-20260809-1200.tar.gz --apply
```

Ele pede que você digite `freshrss` pra confirmar, porque os dados atuais são
apagados antes de o arquivo ser extraído.

## Remover

```bash
qh freshrss --remove --apply           # para e tira, mantendo os dados
qh freshrss --remove --purge --apply   # e apaga volumes, secrets e .env
```

O `--purge` também pede o nome digitado. O nó da tailnet não é desregistrado
por isso — isso é no admin do Tailscale.

## Comandos

```bash
systemctl --user status freshrss
podman logs -f freshrss
```

## Créditos

[FreshRSS/FreshRSS](https://github.com/FreshRSS/FreshRSS) — AGPL-3.0

[Documentação oficial](https://freshrss.org)
