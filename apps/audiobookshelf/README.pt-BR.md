# Audiobookshelf

<img src="https://cdn.jsdelivr.net/gh/homarr-labs/dashboard-icons/svg/audiobookshelf.svg" width="64" height="64" alt="">

**[🇺🇸 Read in English](./README.md)**

Servidor de audiolivros e podcasts, com progresso sincronizado entre dispositivos.

## Instalar

```bash
qh audiobookshelf            # mostra o plano
qh audiobookshelf --apply
```

Abrir `http://<ip-do-host>:13378` ou `https://audiobookshelf.<your-tailnet>.ts.net`.

<details>
<summary><b>Instalação manual</b></summary>

```bash
# 1. Baixar as units (sem precisar clonar o repositório)
mkdir -p ~/.config/containers/systemd
wget -P ~/.config/containers/systemd/ \
  https://raw.githubusercontent.com/wallacepnts/quadlet-homelab/main/apps/audiobookshelf/audiobookshelf.container

# 2. Diretórios de dados — bind mount exige que já existam antes do start
mkdir -p ~/.config/containers/volumes/audiobookshelf/{config,metadata,audiobooks,podcasts}

# 3. Env não-secreto — baixar o exemplo, ajustar TZ se precisar
mkdir -p ~/.config/containers/env
wget -O ~/.config/containers/env/audiobookshelf.env \
  https://raw.githubusercontent.com/wallacepnts/quadlet-homelab/main/apps/audiobookshelf/.env.example

# 4. Subir
systemctl --user daemon-reload
systemctl --user start audiobookshelf
```

</details>

## Arquivos

```
audiobookshelf.container
.env.example
```

## Atualizar

```bash
qh audiobookshelf --update --apply
```

Fixado em `2.36.0`. Nada atualiza sozinho — versão nova entra quando você
roda o comando acima.

## Backup

```bash
qh audiobookshelf --backup --apply --out ~/backups
```

Ele para o serviço, empacota os dados, o `.env` e os secrets, e sobe de novo.
A frio de propósito: copiar banco vivo dá um arquivo que só falha na hora de
restaurar.

Pra restaurar, por cima dos dados atuais:

```bash
qh audiobookshelf --restore ~/backups/audiobookshelf-20260809-1200.tar.gz --apply
```

Ele pede que você digite `audiobookshelf` pra confirmar, porque os dados atuais são
apagados antes de o arquivo ser extraído.

## Remover

```bash
qh audiobookshelf --remove --apply           # para e tira, mantendo os dados
qh audiobookshelf --remove --purge --apply   # e apaga volumes, secrets e .env
```

O `--purge` também pede o nome digitado. O nó da tailnet não é desregistrado
por isso — isso é no admin do Tailscale.

## Comandos

```bash
systemctl --user status audiobookshelf
podman logs -f audiobookshelf
```

## Créditos

[advplyr/audiobookshelf](https://github.com/advplyr/audiobookshelf) — GPL-3.0

[Documentação oficial](https://audiobookshelf.org)
