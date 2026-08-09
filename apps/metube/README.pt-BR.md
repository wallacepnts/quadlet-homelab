# MeTube

<img src="https://cdn.jsdelivr.net/gh/homarr-labs/dashboard-icons/svg/metube.svg" width="64" height="64" alt="">

**[🇺🇸 Read in English](./README.md)**

Interface web do yt-dlp — cola a URL e o vídeo cai no disco.

## Instalar

```bash
qh metube            # mostra o plano
qh metube --apply
```

Abrir `http://<ip-do-host>:8100` ou `https://metube.<your-tailnet>.ts.net`.

<details>
<summary><b>Instalação manual</b></summary>

```bash
# 1. Baixar a unit (sem precisar clonar o repositório)
mkdir -p ~/.config/containers/systemd
wget -P ~/.config/containers/systemd/ \
  https://raw.githubusercontent.com/wallacepnts/quadlet-homelab/main/apps/metube/metube.container

# 2. Diretório + dono correspondente ao User=1000 da unit
mkdir -p ~/.config/containers/volumes/metube/downloads
podman unshare chown -R 1000:1000 ~/.config/containers/volumes/metube

# 3. Subir
systemctl --user daemon-reload
systemctl --user start metube
```

</details>

## Arquivos

```
metube.container
```

## Atualizar

```bash
qh metube --update --apply
```

Fixado em `2026.08.04`. Nada atualiza sozinho — versão nova entra quando você
roda o comando acima.

## Backup

```bash
qh metube --backup --apply --out ~/backups
```

Ele para o serviço, empacota os dados, o `.env` e os secrets, e sobe de novo.
A frio de propósito: copiar banco vivo dá um arquivo que só falha na hora de
restaurar.

Pra restaurar, por cima dos dados atuais:

```bash
qh metube --restore ~/backups/metube-20260809-1200.tar.gz --apply
```

Ele pede que você digite `metube` pra confirmar, porque os dados atuais são
apagados antes de o arquivo ser extraído.

## Remover

```bash
qh metube --remove --apply           # para e tira, mantendo os dados
qh metube --remove --purge --apply   # e apaga volumes, secrets e .env
```

O `--purge` também pede o nome digitado. O nó da tailnet não é desregistrado
por isso — isso é no admin do Tailscale.

## Comandos

```bash
systemctl --user status metube
podman logs -f metube
```

## Créditos

[alexta69/metube](https://github.com/alexta69/metube) — AGPL-3.0

[Documentação oficial](https://github.com/alexta69/metube#readme)
