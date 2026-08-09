# nginx

<img src="https://cdn.jsdelivr.net/gh/homarr-labs/dashboard-icons/svg/nginx.svg" width="64" height="64" alt="">

**[🇺🇸 Read in English](./README.md)**

Servidor de arquivos estáticos.

## Instalar

```bash
qh nginx            # mostra o plano
qh nginx --apply
```

Abrir `http://<ip-do-host>:8103` ou `https://nginx.<your-tailnet>.ts.net`.

<details>
<summary><b>Instalação manual</b></summary>

```bash
# 1. Baixar as units (sem precisar clonar o repositório)
mkdir -p ~/.config/containers/systemd
wget -P ~/.config/containers/systemd/ \
  https://raw.githubusercontent.com/wallacepnts/quadlet-homelab/main/apps/nginx/nginx.container

# 2. Diretórios de dados — bind mount exige que já existam antes do start
mkdir -p ~/.config/containers/volumes/nginx/{html,conf.d}
echo "<h1>Funcionando</h1>" > ~/.config/containers/volumes/nginx/html/index.html
wget -O ~/.config/containers/volumes/nginx/conf.d/default.conf \
  https://raw.githubusercontent.com/wallacepnts/quadlet-homelab/main/apps/nginx/conf.d/default.conf

# 3. Subir
systemctl --user daemon-reload
systemctl --user start nginx
```

</details>

## Arquivos

```
nginx.container
install.ini
```

## Atualizar

```bash
qh nginx --update --apply
```

Fixado em `1.30.4-alpine`. Nada atualiza sozinho — versão nova entra quando você
roda o comando acima.

## Backup

```bash
qh nginx --backup --apply --out ~/backups
```

Ele para o serviço, empacota os dados, o `.env` e os secrets, e sobe de novo.
A frio de propósito: copiar banco vivo dá um arquivo que só falha na hora de
restaurar.

Pra restaurar, por cima dos dados atuais:

```bash
qh nginx --restore ~/backups/nginx-20260809-1200.tar.gz --apply
```

Ele pede que você digite `nginx` pra confirmar, porque os dados atuais são
apagados antes de o arquivo ser extraído.

## Remover

```bash
qh nginx --remove --apply           # para e tira, mantendo os dados
qh nginx --remove --purge --apply   # e apaga volumes, secrets e .env
```

O `--purge` também pede o nome digitado. O nó da tailnet não é desregistrado
por isso — isso é no admin do Tailscale.

## Comandos

```bash
systemctl --user status nginx
podman logs -f nginx
```

## Créditos

[](https://hub.docker.com/_/nginx) — BSD-2-Clause

[Documentação oficial](https://nginx.org/en/docs/)
