# Traccar

<img src="https://cdn.jsdelivr.net/gh/homarr-labs/dashboard-icons/svg/traccar.svg" width="64" height="64" alt="">

**[🇺🇸 Read in English](./README.md)**

Rastreamento de GPS — mapa ao vivo, histórico, geocercas e relatórios, com app no celular.

## Instalar

```bash
qh traccar            # mostra o plano
qh traccar --apply
```

Abrir `http://<ip-do-host>:5056` ou `https://traccar.<your-tailnet>.ts.net`.

<details>
<summary><b>Instalação manual</b></summary>

```bash
# 1. Baixar a unit (sem precisar clonar o repositório)
mkdir -p ~/.config/containers/systemd
wget -P ~/.config/containers/systemd/ \
  https://raw.githubusercontent.com/wallacepnts/quadlet-homelab/main/apps/traccar/traccar.container

# 2. Diretórios + dono correspondente ao User=1000 da unit
mkdir -p ~/.config/containers/volumes/traccar/{data,logs,conf}

# 3. Config — precisa EXISTIR antes do start (é bind mount de arquivo;
#    se não existir, o Podman cria um diretório no lugar e o Traccar quebra)
wget -O ~/.config/containers/volumes/traccar/conf/traccar.xml \
  https://raw.githubusercontent.com/wallacepnts/quadlet-homelab/main/apps/traccar/traccar.xml.example

podman unshare chown -R 1000:1000 ~/.config/containers/volumes/traccar

# 4. Subir
systemctl --user daemon-reload
systemctl --user start traccar
```

</details>

## Arquivos

```
traccar.container
traccar.xml.example
```

## Atualizar

```bash
qh traccar --update --apply
```

Fixado em `6.14.5`. Nada atualiza sozinho — versão nova entra quando você
roda o comando acima.

## Backup

```bash
qh traccar --backup --apply --out ~/backups
```

Ele para o serviço, empacota os dados, o `.env` e os secrets, e sobe de novo.
A frio de propósito: copiar banco vivo dá um arquivo que só falha na hora de
restaurar.

Pra restaurar, por cima dos dados atuais:

```bash
qh traccar --restore ~/backups/traccar-20260809-1200.tar.gz --apply
```

Ele pede que você digite `traccar` pra confirmar, porque os dados atuais são
apagados antes de o arquivo ser extraído.

## Remover

```bash
qh traccar --remove --apply           # para e tira, mantendo os dados
qh traccar --remove --purge --apply   # e apaga volumes, secrets e .env
```

O `--purge` também pede o nome digitado. O nó da tailnet não é desregistrado
por isso — isso é no admin do Tailscale.

## Comandos

```bash
systemctl --user status traccar
podman logs -f traccar
```

## Créditos

[traccar/traccar](https://github.com/traccar/traccar) — Apache-2.0

[Documentação oficial](https://www.traccar.org)
