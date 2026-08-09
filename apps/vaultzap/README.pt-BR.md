# VaultZap

<img src="https://raw.githubusercontent.com/wallacepnts/vaultzap/main/internal/web/static/img/favicon.svg" width="64" height="64" alt="">

**[🇺🇸 Read in English](./README.md)**

Arquivo local e navegável de conversas exportadas do WhatsApp — busca, galeria e calendário, 100% offline.

## Instalar

```bash
qh vaultzap            # mostra o plano
qh vaultzap --apply
```

Abrir `http://<ip-do-host>:8927` ou `https://vaultzap.<your-tailnet>.ts.net`.

<details>
<summary><b>Instalação manual</b></summary>

```bash
# 1. Baixar a unit (um arquivo só -> fica solto em systemd/)
mkdir -p ~/.config/containers/systemd
wget -P ~/.config/containers/systemd/ \
  https://raw.githubusercontent.com/wallacepnts/quadlet-homelab/main/apps/vaultzap/vaultzap.container

# 2. Diretórios — bind mount exige que já existam antes do start
mkdir -p ~/.config/containers/volumes/vaultzap/{data,inbox}

# 3. Env
mkdir -p ~/.config/containers/env
wget -O ~/.config/containers/env/vaultzap.env \
  https://raw.githubusercontent.com/wallacepnts/quadlet-homelab/main/apps/vaultzap/.env.example

# 4. Ícone do dashboard (o projeto tem o próprio, não há equivalente em
#    dashboard-icons)
mkdir -p ~/.config/containers/volumes/homepage/icons
wget -O ~/.config/containers/volumes/homepage/icons/vaultzap.svg \
  https://raw.githubusercontent.com/wallacepnts/vaultzap/main/internal/web/static/img/favicon.svg
systemctl --user restart homepage   # só detecta ícone novo depois de reiniciar

# 5. Subir
systemctl --user daemon-reload
systemctl --user start vaultzap
```

</details>

## Arquivos

```
vaultzap.container
.env.example
install.ini
```

## Atualizar

```bash
qh vaultzap --update --apply
```

`AutoUpdate=registry` ligado: a imagem é atualizada sozinha.

## Backup

```bash
qh vaultzap --backup --apply --out ~/backups
```

Ele para o serviço, empacota os dados, o `.env` e os secrets, e sobe de novo.
A frio de propósito: copiar banco vivo dá um arquivo que só falha na hora de
restaurar.

Pra restaurar, por cima dos dados atuais:

```bash
qh vaultzap --restore ~/backups/vaultzap-20260809-1200.tar.gz --apply
```

Ele pede que você digite `vaultzap` pra confirmar, porque os dados atuais são
apagados antes de o arquivo ser extraído.

## Remover

```bash
qh vaultzap --remove --apply           # para e tira, mantendo os dados
qh vaultzap --remove --purge --apply   # e apaga volumes, secrets e .env
```

O `--purge` também pede o nome digitado. O nó da tailnet não é desregistrado
por isso — isso é no admin do Tailscale.

## Comandos

```bash
systemctl --user status vaultzap
podman logs -f vaultzap
```

## Créditos

[wallacepnts/vaultzap](https://github.com/wallacepnts/vaultzap) — AGPL-3.0

[Documentação oficial](https://github.com/wallacepnts/vaultzap#readme)
