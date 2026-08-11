# Ghost

<img src="https://cdn.jsdelivr.net/gh/selfhst/icons/webp/ghost.webp" width="64" height="64" alt="">

**[🇺🇸 Read in English](./README.md)**

Blog/newsletter self-hosted.

## Instalar

```bash
qh ghost            # mostra o plano
qh ghost --apply
```

Abrir `http://<ip-do-host>:2368` ou `https://ghost.<your-tailnet>.ts.net`.

<details>
<summary><b>Instalação manual</b></summary>

```bash
# 1. Baixar as units (sem precisar clonar o repositório)
mkdir -p ~/.config/containers/systemd
wget -P ~/.config/containers/systemd/ \
  https://raw.githubusercontent.com/wallacepnts/quadlet-homelab/main/apps/ghost/ghost.container

# 2. Diretório de dados — bind mount exige que já exista antes do start
mkdir -p ~/.config/containers/volumes/ghost/content

# 3. Env não-secreto — baixar o exemplo e EDITAR a url pro domínio real
#    antes de subir (mesmo motivo do Monica: deixar o placeholder gera
#    link/e-mail quebrado)
mkdir -p ~/.config/containers/env
wget -O ~/.config/containers/env/ghost.env \
  https://raw.githubusercontent.com/wallacepnts/quadlet-homelab/main/apps/ghost/.env.example

# 4. Subir
systemctl --user daemon-reload
systemctl --user start ghost
```

</details>

## Arquivos

```
ghost.container
.env.example
install.ini
```

## Atualizar

```bash
qh ghost --update --apply
```

Fixado em `6.56.0-alpine`. Nada atualiza sozinho — versão nova entra quando você
roda o comando acima.

## Backup

```bash
qh ghost --backup --apply --out ~/backups
```

Ele para o serviço, empacota os dados, o `.env` e os secrets, e sobe de novo.
A frio de propósito: copiar banco vivo dá um arquivo que só falha na hora de
restaurar.

Pra restaurar, por cima dos dados atuais:

```bash
qh ghost --restore ~/backups/ghost-20260809-1200.tar.gz --apply
```

Ele pede que você digite `ghost` pra confirmar, porque os dados atuais são
apagados antes de o arquivo ser extraído.

## Remover

```bash
qh ghost --remove --apply           # para e tira, mantendo os dados
qh ghost --remove --purge --apply   # e apaga volumes, secrets e .env
```

O `--purge` também pede o nome digitado. O nó da tailnet não é desregistrado
por isso — isso é no admin do Tailscale.

## Comandos

```bash
systemctl --user status ghost
podman logs -f ghost
```

## Créditos

[TryGhost/Ghost](https://github.com/TryGhost/Ghost) — MIT

[Documentação oficial](https://ghost.org)
