# Calibre-Web-Automated

<img src="https://cdn.jsdelivr.net/gh/homarr-labs/dashboard-icons/svg/calibre-web.svg" width="64" height="64" alt="">

**[🇺🇸 Read in English](./README.md)**

Biblioteca de ebooks com conversão, metadados e capas automáticas via Calibre, com leitura direto no navegador.

## Instalar

```bash
qh calibre-web-automated            # mostra o plano
qh calibre-web-automated --apply
```

Abrir `http://<ip-do-host>:8105` ou `https://calibre-web.<your-tailnet>.ts.net`.

<details>
<summary><b>Instalação manual</b></summary>

```bash
# 1. Baixar a unit (sem precisar clonar o repositório)
mkdir -p ~/.config/containers/systemd
wget -P ~/.config/containers/systemd/ \
  https://raw.githubusercontent.com/wallacepnts/quadlet-homelab/main/apps/calibre-web-automated/calibre-web-automated.container

# 2. Diretórios de dados — bind mount exige que já existam antes do start
mkdir -p ~/.config/containers/volumes/calibre-web-automated/{config,ingest,library}

# 3. Env não-secreto — baixar o exemplo, ajustar PUID/PGID pro usuário
#    que roda o Podman (mesmo dono dos volumes acima)
mkdir -p ~/.config/containers/env
wget -O ~/.config/containers/env/calibre-web-automated.env \
  https://raw.githubusercontent.com/wallacepnts/quadlet-homelab/main/apps/calibre-web-automated/.env.example
sed -i "s/^PUID=.*/PUID=$(id -u)/;s/^PGID=.*/PGID=$(id -g)/" \
  ~/.config/containers/env/calibre-web-automated.env

# 4. Subir
systemctl --user daemon-reload
systemctl --user start calibre-web-automated
```

</details>

## Arquivos

```
calibre-web-automated.container
.env.example
```

## Atualizar

```bash
qh calibre-web-automated --update --apply
```

Fixado em `v4.0.6`. Nada atualiza sozinho — versão nova entra quando você
roda o comando acima.

## Backup

```bash
qh calibre-web-automated --backup --apply --out ~/backups
```

Ele para o serviço, empacota os dados, o `.env` e os secrets, e sobe de novo.
A frio de propósito: copiar banco vivo dá um arquivo que só falha na hora de
restaurar.

Pra restaurar, por cima dos dados atuais:

```bash
qh calibre-web-automated --restore ~/backups/calibre-web-automated-20260809-1200.tar.gz --apply
```

Ele pede que você digite `calibre-web-automated` pra confirmar, porque os dados atuais são
apagados antes de o arquivo ser extraído.

## Remover

```bash
qh calibre-web-automated --remove --apply           # para e tira, mantendo os dados
qh calibre-web-automated --remove --purge --apply   # e apaga volumes, secrets e .env
```

O `--purge` também pede o nome digitado. O nó da tailnet não é desregistrado
por isso — isso é no admin do Tailscale.

## Comandos

```bash
systemctl --user status calibre-web-automated
podman logs -f calibre-web-automated
```

## Créditos

[crocodilestick/Calibre-Web-Automated](https://github.com/crocodilestick/Calibre-Web-Automated) — GPL-3.0

[Documentação oficial](https://github.com/crocodilestick/Calibre-Web-Automated)
