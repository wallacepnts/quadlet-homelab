# WUD (What's Up Docker)

<img src="https://cdn.jsdelivr.net/gh/getwud/wud@main/ui/public/img/icons/android-chrome-512x512.png" width="64" height="64" alt="">

**[🇺🇸 Read in English](./README.md)**

Monitora as atualizações de imagem disponíveis pros containers, sem aplicar nada sozinho — só avisa.

## Instalar

```bash
qh wud            # mostra o plano
qh wud --apply
```

Abrir `http://<ip-do-host>:8085` ou `https://wud.<your-tailnet>.ts.net`.

<details>
<summary><b>Instalação manual</b></summary>

```bash
# 1. Baixar a unit (sem precisar clonar o repositório)
mkdir -p ~/.config/containers/systemd
wget -P ~/.config/containers/systemd/ \
  https://raw.githubusercontent.com/wallacepnts/quadlet-homelab/main/apps/wud/wud.container

# 2. Diretório de dados — bind mount exige que já exista antes do start
mkdir -p ~/.config/containers/volumes/wud/store

# 3. Env — baixar o exemplo. Schedule da checagem (cron): padrão do
#    próprio WUD é de hora em hora; diário é suficiente pra maioria dos
#    homelabs e gera bem menos tráfego contra os registries.
mkdir -p ~/.config/containers/env
wget -O ~/.config/containers/env/wud.env \
  https://raw.githubusercontent.com/wallacepnts/quadlet-homelab/main/apps/wud/.env.example

# 4. Socket do Podman
systemctl --user enable --now podman.socket

# 5. Subir
systemctl --user daemon-reload
systemctl --user start wud
```

</details>

## Arquivos

```
wud.container
.env.example
```

## Atualizar

```bash
qh wud --update --apply
```

Fixado em `8.3.1`. Nada atualiza sozinho — versão nova entra quando você
roda o comando acima.

## Backup

```bash
qh wud --backup --apply --out ~/backups
```

Ele para o serviço, empacota os dados, o `.env` e os secrets, e sobe de novo.
A frio de propósito: copiar banco vivo dá um arquivo que só falha na hora de
restaurar.

Pra restaurar, por cima dos dados atuais:

```bash
qh wud --restore ~/backups/wud-20260809-1200.tar.gz --apply
```

Ele pede que você digite `wud` pra confirmar, porque os dados atuais são
apagados antes de o arquivo ser extraído.

## Remover

```bash
qh wud --remove --apply           # para e tira, mantendo os dados
qh wud --remove --purge --apply   # e apaga volumes, secrets e .env
```

O `--purge` também pede o nome digitado. O nó da tailnet não é desregistrado
por isso — isso é no admin do Tailscale.

## Comandos

```bash
systemctl --user status wud
podman logs -f wud
```

## Créditos

[getwud/wud](https://github.com/getwud/wud) — MIT

[Documentação oficial](https://getwud.github.io/wud/)
