# Home Assistant

<img src="https://cdn.jsdelivr.net/gh/homarr-labs/dashboard-icons/svg/home-assistant.svg" width="64" height="64" alt="">

**[🇺🇸 Read in English](./README.md)**

Hub central de automação residencial, integra dispositivos de qualquer fabricante num painel só.

## Instalar

```bash
qh home-assistant            # mostra o plano
qh home-assistant --apply
```

Abrir `http://<ip-do-host>:8123` ou `https://home-assistant.<your-tailnet>.ts.net`.

<details>
<summary><b>Instalação manual</b></summary>

```bash
# 1. Baixar a unit (sem precisar clonar o repositório)
mkdir -p ~/.config/containers/systemd
wget -P ~/.config/containers/systemd/ \
  https://raw.githubusercontent.com/wallacepnts/quadlet-homelab/main/apps/home-assistant/home-assistant.container

# 2. Diretório de dados — bind mount exige que já exista antes do start
mkdir -p ~/.config/containers/volumes/home-assistant/config

# 3. Env — baixar o exemplo
mkdir -p ~/.config/containers/env
wget -O ~/.config/containers/env/home-assistant.env \
  https://raw.githubusercontent.com/wallacepnts/quadlet-homelab/main/apps/home-assistant/.env.example

# 4. Subir
systemctl --user daemon-reload
systemctl --user start home-assistant
```

</details>

## Arquivos

```
home-assistant.container
.env.example
install.ini
```

## Atualizar

```bash
qh home-assistant --update --apply
```

Fixado em `2026.8.1`. Nada atualiza sozinho — versão nova entra quando você
roda o comando acima.

## Backup

```bash
qh home-assistant --backup --apply --out ~/backups
```

Ele para o serviço, empacota os dados, o `.env` e os secrets, e sobe de novo.
A frio de propósito: copiar banco vivo dá um arquivo que só falha na hora de
restaurar.

Pra restaurar, por cima dos dados atuais:

```bash
qh home-assistant --restore ~/backups/home-assistant-20260809-1200.tar.gz --apply
```

Ele pede que você digite `home-assistant` pra confirmar, porque os dados atuais são
apagados antes de o arquivo ser extraído.

## Remover

```bash
qh home-assistant --remove --apply           # para e tira, mantendo os dados
qh home-assistant --remove --purge --apply   # e apaga volumes, secrets e .env
```

O `--purge` também pede o nome digitado. O nó da tailnet não é desregistrado
por isso — isso é no admin do Tailscale.

## Comandos

```bash
systemctl --user status home-assistant
podman logs -f home-assistant
```

## Créditos

[home-assistant/core](https://github.com/home-assistant/core) — Apache-2.0

[Documentação oficial](https://www.home-assistant.io)
