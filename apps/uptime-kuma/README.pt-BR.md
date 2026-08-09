# Uptime Kuma

<img src="https://cdn.jsdelivr.net/gh/homarr-labs/dashboard-icons/svg/uptime-kuma.svg" width="64" height="64" alt="">

**[🇺🇸 Read in English](./README.md)**

Monitor de disponibilidade dos outros serviços e da tailnet, com histórico e notificação.

## Instalar

```bash
qh uptime-kuma            # mostra o plano
qh uptime-kuma --apply
```

Abrir `http://<ip-do-host>:3005` ou `https://uptime-kuma.<your-tailnet>.ts.net`.

<details>
<summary><b>Instalação manual</b></summary>

```bash
# 1. Baixar as units (sem precisar clonar o repositório)
mkdir -p ~/.config/containers/systemd
wget -P ~/.config/containers/systemd/ \
  https://raw.githubusercontent.com/wallacepnts/quadlet-homelab/main/apps/uptime-kuma/uptime-kuma.container

# 2. Diretório de dados + dono correspondente ao User=1000 da unit.
#    `podman unshare` executa o chown DENTRO do user namespace, que é
#    onde o 1000 do container existe (no host isso vira 100999).
mkdir -p ~/.config/containers/volumes/uptime-kuma/data
podman unshare chown -R 1000:1000 ~/.config/containers/volumes/uptime-kuma/data

# 3. Subir
systemctl --user daemon-reload
systemctl --user start uptime-kuma
```

</details>

## Arquivos

```
uptime-kuma.container
```

## Atualizar

```bash
qh uptime-kuma --update --apply
```

Fixado em `2.5.0`. Nada atualiza sozinho — versão nova entra quando você
roda o comando acima.

## Backup

```bash
qh uptime-kuma --backup --apply --out ~/backups
```

Ele para o serviço, empacota os dados, o `.env` e os secrets, e sobe de novo.
A frio de propósito: copiar banco vivo dá um arquivo que só falha na hora de
restaurar.

Pra restaurar, por cima dos dados atuais:

```bash
qh uptime-kuma --restore ~/backups/uptime-kuma-20260809-1200.tar.gz --apply
```

Ele pede que você digite `uptime-kuma` pra confirmar, porque os dados atuais são
apagados antes de o arquivo ser extraído.

## Remover

```bash
qh uptime-kuma --remove --apply           # para e tira, mantendo os dados
qh uptime-kuma --remove --purge --apply   # e apaga volumes, secrets e .env
```

O `--purge` também pede o nome digitado. O nó da tailnet não é desregistrado
por isso — isso é no admin do Tailscale.

## Comandos

```bash
systemctl --user status uptime-kuma
podman logs -f uptime-kuma
```

## Créditos

[louislam/uptime-kuma](https://github.com/louislam/uptime-kuma) — MIT

[Documentação oficial](https://uptime.kuma.pet)
