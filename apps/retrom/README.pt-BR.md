# Retrom

<img src="https://api.iconify.design/mdi/gamepad-variant.svg?color=%23888888" width="64" height="64" alt="">

**[🇺🇸 Read in English](./README.md)**

Biblioteca de jogos para emulação: uma coleção no servidor, jogada no
navegador ou pelo cliente de desktop do Retrom.

## Instalação

```bash
qh retrom            # mostra o plano
qh retrom --apply
```

Coloque os jogos em `~/.config/containers/volumes/retrom/library`, na
[estrutura de pastas que o Retrom
espera](https://github.com/JMBeresford/retrom/wiki/Library-Structure), e abra
`http://<ip-do-host>:5101` ou `https://retrom.<your-tailnet>.ts.net`.

**O primeiro start leva uns 90 segundos** — ele baixa o EmulatorJS e roda as
migrações do banco. O `TimeoutStartSec=300` e os 180 segundos de carência do
healthcheck existem por isso; os restarts seguintes são rápidos.

<details>
<summary><b>Instalação manual</b></summary>

```bash
mkdir -p ~/.config/containers/systemd ~/.config/containers/env
mkdir -p ~/.config/containers/volumes/retrom/{config,data,library}

wget -P ~/.config/containers/systemd/ \
  https://raw.githubusercontent.com/wallacepnts/quadlet-homelab/main/apps/retrom/retrom.container
wget -O ~/.config/containers/env/retrom.env \
  https://raw.githubusercontent.com/wallacepnts/quadlet-homelab/main/apps/retrom/.env.example

systemctl --user daemon-reload
systemctl --user start retrom
```

</details>

## Arquivos

```
retrom.container   unit
.env.example       ambiente
```

Config, dados e biblioteca em `~/.config/containers/volumes/retrom/`, na porta
**5101**.

O entrypoint faz chown dos três a cada start, para o que o `PUID`/`PGID`
disserem. Em biblioteca grande, isso é minutos de disco para um dono que não
mudou — o `SKIP_RECURSIVE_CHOWN=true` no `.env` desliga.

## Metadados

Capas e descrições vêm do IGDB ou do SteamGridDB, e os dois pedem chave de
API. Sem chave a biblioteca funciona igual, listada pelo nome do arquivo. As
chaves são configuradas pelo cliente, não aqui — veja [Metadata
Providers](https://github.com/JMBeresford/retrom/wiki/Metadata-Providers).

## Atualizar

```bash
qh retrom --update --apply
```

Pinado em `0.8.4`. Nada atualiza sozinho — a versão nova entra quando você roda
o comando acima.

## Backup

```bash
qh retrom --backup --apply --out ~/backups
```

Para o serviço, empacota os três volumes e o `.env`, e religa. A frio de
propósito: o Retrom carrega um PostgreSQL embutido, e copiá-lo em uso dá um
arquivo que só falha na hora de restaurar. É também por isso que o modo a usar
no [gancho de backup do Zerobyte](../zerobyte) é o `stop`.

Para restaurar, por cima dos dados atuais:

```bash
qh retrom --restore ~/backups/retrom-20260810-1200.tar.gz --apply
```

## Remover

```bash
qh retrom --remove --apply           # para, mantém os dados
qh retrom --remove --purge --apply   # e apaga os volumes e o .env
```

O `--purge` apaga a biblioteca junto — os jogos ficam num volume como todo o
resto.

## Comandos

```bash
systemctl --user status retrom
podman logs -f retrom
podman exec retrom curl -fsS -o /dev/null http://127.0.0.1:5101/
```

## Créditos

[Retrom](https://github.com/JMBeresford/retrom) por
[JMBeresford](https://github.com/JMBeresford) — GPL-3.0

[Documentação oficial](https://github.com/JMBeresford/retrom/wiki)
