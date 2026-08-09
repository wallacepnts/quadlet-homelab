# Copyparty

<img src="https://cdn.jsdelivr.net/gh/homarr-labs/dashboard-icons/svg/copyparty.svg" width="64" height="64" alt="">

**[🇺🇸 Read in English](./README.md)**

Servidor de arquivos com upload pelo navegador ou celular, retomada de transferência e WebDAV.

## Instalar

```bash
qh copyparty            # mostra o plano
qh copyparty --apply
```

Abrir `http://<ip-do-host>:3923` ou `https://copyparty.<your-tailnet>.ts.net`.

<details>
<summary><b>Instalação manual</b></summary>

```bash
# 1. Baixar a unit (sem precisar clonar o repositório)
mkdir -p ~/.config/containers/systemd
wget -P ~/.config/containers/systemd/ \
  https://raw.githubusercontent.com/wallacepnts/quadlet-homelab/main/apps/copyparty/copyparty.container

# 2. Diretórios
mkdir -p ~/.config/containers/volumes/copyparty/{cfg,data}

# 3. Config — TROCAR a senha antes de subir
wget -O ~/.config/containers/volumes/copyparty/cfg/copyparty.conf \
  https://raw.githubusercontent.com/wallacepnts/quadlet-homelab/main/apps/copyparty/copyparty.conf.example
${EDITOR:-vi} ~/.config/containers/volumes/copyparty/cfg/copyparty.conf

# 4. Dono correspondente ao User=1000 da unit
podman unshare chown -R 1000:1000 ~/.config/containers/volumes/copyparty

# 5. Subir
systemctl --user daemon-reload
systemctl --user start copyparty
```

</details>

## Arquivos

```
copyparty.container
copyparty.conf.example
install.ini
```

## Atualizar

```bash
qh copyparty --update --apply
```

Fixado em `1.20.20`. Nada atualiza sozinho — versão nova entra quando você
roda o comando acima.

## Backup

```bash
qh copyparty --backup --apply --out ~/backups
```

Ele para o serviço, empacota os dados, o `.env` e os secrets, e sobe de novo.
A frio de propósito: copiar banco vivo dá um arquivo que só falha na hora de
restaurar.

Pra restaurar, por cima dos dados atuais:

```bash
qh copyparty --restore ~/backups/copyparty-20260809-1200.tar.gz --apply
```

Ele pede que você digite `copyparty` pra confirmar, porque os dados atuais são
apagados antes de o arquivo ser extraído.

## Remover

```bash
qh copyparty --remove --apply           # para e tira, mantendo os dados
qh copyparty --remove --purge --apply   # e apaga volumes, secrets e .env
```

O `--purge` também pede o nome digitado. O nó da tailnet não é desregistrado
por isso — isso é no admin do Tailscale.

## Comandos

```bash
systemctl --user status copyparty
podman logs -f copyparty
```

## Créditos

[9001/copyparty](https://github.com/9001/copyparty) — MIT

[Documentação oficial](https://github.com/9001/copyparty#readme)
