# LubeLogger

<img src="https://cdn.jsdelivr.net/gh/homarr-labs/dashboard-icons/png/lubelogger.png" width="64" height="64" alt="">

**[🇺🇸 Read in English](./README.md)**

Registro de manutenção veicular — trocas de óleo, revisões, gastos e lembretes, por veículo.

## Instalar

```bash
qh lubelogger            # mostra o plano
qh lubelogger --apply
```

Abrir `http://<ip-do-host>:8083` ou `https://lubelogger.<your-tailnet>.ts.net`.

<details>
<summary><b>Instalação manual</b></summary>

```bash
# 1. Baixar a unit (sem precisar clonar o repositório)
mkdir -p ~/.config/containers/systemd
wget -P ~/.config/containers/systemd/ \
  https://raw.githubusercontent.com/wallacepnts/quadlet-homelab/main/apps/lubelogger/lubelogger.container

# 2. Diretórios de dados — bind mount exige que já existam antes do start
mkdir -p ~/.config/containers/volumes/lubelogger/{data,keys}

# 3. Env — baixar o exemplo e editar o domínio
mkdir -p ~/.config/containers/env
wget -O ~/.config/containers/env/lubelogger.env \
  https://raw.githubusercontent.com/wallacepnts/quadlet-homelab/main/apps/lubelogger/.env.example
# editar ~/.config/containers/env/lubelogger.env: LUBELOGGER_DOMAIN

# 4. Subir
systemctl --user daemon-reload
systemctl --user start lubelogger
```

</details>

## Arquivos

```
lubelogger.container
.env.example
install.ini
```

## Atualizar

```bash
qh lubelogger --update --apply
```

Fixado em `v1.7.0`. Nada atualiza sozinho — versão nova entra quando você
roda o comando acima.

## Backup

```bash
qh lubelogger --backup --apply --out ~/backups
```

Ele para o serviço, empacota os dados, o `.env` e os secrets, e sobe de novo.
A frio de propósito: copiar banco vivo dá um arquivo que só falha na hora de
restaurar.

Pra restaurar, por cima dos dados atuais:

```bash
qh lubelogger --restore ~/backups/lubelogger-20260809-1200.tar.gz --apply
```

Ele pede que você digite `lubelogger` pra confirmar, porque os dados atuais são
apagados antes de o arquivo ser extraído.

## Remover

```bash
qh lubelogger --remove --apply           # para e tira, mantendo os dados
qh lubelogger --remove --purge --apply   # e apaga volumes, secrets e .env
```

O `--purge` também pede o nome digitado. O nó da tailnet não é desregistrado
por isso — isso é no admin do Tailscale.

## Comandos

```bash
systemctl --user status lubelogger
podman logs -f lubelogger
```

## Créditos

[hargata/lubelog](https://github.com/hargata/lubelog) — MIT

[Documentação oficial](https://lubelogger.com)
