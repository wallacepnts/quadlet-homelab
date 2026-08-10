# Beaver Habits

<img src="https://api.iconify.design/mdi/check-circle-outline.svg?color=%23888888" width="64" height="64" alt="">

**[🇺🇸 Read in English](./README.md)**

Acompanhamento de hábitos sem metas: você marca o dia e segue. A graça do
projeto é o que ele deixa de fora — nenhuma meta para falhar, nenhuma tela de
culpa.

## Instalação

```bash
qh beaverhabits            # mostra o plano
qh beaverhabits --apply
```

Abra `http://<ip-do-host>:8015` ou `https://habits.<your-tailnet>.ts.net` e
crie a conta. **Quem alcançar o endereço também pode criar uma** — assim que a
sua existir, ponha `MAX_USER_COUNT=1` no `.env` e reinicie.

<details>
<summary><b>Instalação manual</b></summary>

```bash
mkdir -p ~/.config/containers/systemd ~/.config/containers/env
mkdir -p ~/.config/containers/volumes/beaverhabits/data
podman unshare chown -R 1000:1000 ~/.config/containers/volumes/beaverhabits

wget -P ~/.config/containers/systemd/ \
  https://raw.githubusercontent.com/wallacepnts/quadlet-homelab/main/apps/beaverhabits/beaverhabits.container
wget -O ~/.config/containers/env/beaverhabits.env \
  https://raw.githubusercontent.com/wallacepnts/quadlet-homelab/main/apps/beaverhabits/.env.example

systemctl --user daemon-reload
systemctl --user start beaverhabits
```

</details>

## Arquivos

```
beaverhabits.container   unit
.env.example             ambiente
```

Dados em `~/.config/containers/volumes/beaverhabits/data`, na porta **8015**.
O `HABITS_STORAGE=USER_DISK` guarda os hábitos como JSON nesse diretório — sem
banco de dados, então o backup é o diretório.

## API

Existe uma API REST, e é com ela que falam o switch do Home Assistant, o
plugin do Stream Deck e o atalho do iPhone listados no README do projeto. Veja
o [guia da API](https://github.com/daya0576/beaverhabits/wiki/Beaver-Habit-Tracker-API-How%E2%80%90to-Guide).

## Atualizar

```bash
qh beaverhabits --update --apply
```

Pinado em `0.10.0`. Nada atualiza sozinho — a versão nova entra quando você
roda o comando acima.

## Backup

```bash
qh beaverhabits --backup --apply --out ~/backups
```

Para o serviço, empacota os dados e o `.env`, e religa.

Para restaurar, por cima dos dados atuais:

```bash
qh beaverhabits --restore ~/backups/beaverhabits-20260810-1200.tar.gz --apply
```

## Remover

```bash
qh beaverhabits --remove --apply           # para, mantém os dados
qh beaverhabits --remove --purge --apply   # e apaga o volume e o .env
```

## Comandos

```bash
systemctl --user status beaverhabits
podman logs -f beaverhabits
podman exec beaverhabits python -c "import urllib.request as u; print(u.urlopen('http://127.0.0.1:8080/health').status)"
```

## Créditos

[Beaver Habit Tracker](https://github.com/daya0576/beaverhabits) por
[daya0576](https://github.com/daya0576) — BSD-3-Clause

[Documentação oficial](https://github.com/daya0576/beaverhabits/wiki)
