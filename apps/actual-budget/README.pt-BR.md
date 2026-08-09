# Actual Budget

<img src="https://cdn.jsdelivr.net/gh/homarr-labs/dashboard-icons/svg/actual-budget.svg" width="64" height="64" alt="">

**[🇺🇸 Read in English](./README.md)**

Rápido e focado em privacidade pra gerenciar finanças pessoais, usando a metodologia de Orçamento de Envelope.

## Instalar

```bash
qh actual-budget            # mostra o plano
qh actual-budget --apply
```

Abrir `http://<ip-do-host>:5006` ou `https://actual.<your-tailnet>.ts.net`.

<details>
<summary><b>Instalação manual</b></summary>

```bash
# 1. Baixar a unit (sem precisar clonar o repositório)
mkdir -p ~/.config/containers/systemd
wget -P ~/.config/containers/systemd/ \
  https://raw.githubusercontent.com/wallacepnts/quadlet-homelab/main/apps/actual-budget/actual.container

# 2. Diretório de dados — bind mount exige que já exista antes do start.
#    O próprio Actual cria server-files/ e user-files/ dentro dele.
mkdir -p ~/.config/containers/volumes/actual/data

# 3. Env — baixar o exemplo (TZ obrigatório, resto é opcional — ver
#    https://actualbudget.org/docs/config/)
mkdir -p ~/.config/containers/env
wget -O ~/.config/containers/env/actual.env \
  https://raw.githubusercontent.com/wallacepnts/quadlet-homelab/main/apps/actual-budget/.env.example

# 4. Subir
systemctl --user daemon-reload
systemctl --user start actual
```

</details>

## Arquivos

```
actual.container
.env.example
```

## Atualizar

```bash
qh actual-budget --update --apply
```

`AutoUpdate=registry` ligado: a imagem é atualizada sozinha.

## Backup

```bash
qh actual-budget --backup --apply --out ~/backups
```

Ele para o serviço, empacota os dados, o `.env` e os secrets, e sobe de novo.
A frio de propósito: copiar banco vivo dá um arquivo que só falha na hora de
restaurar.

Pra restaurar, por cima dos dados atuais:

```bash
qh actual-budget --restore ~/backups/actual-budget-20260809-1200.tar.gz --apply
```

Ele pede que você digite `actual-budget` pra confirmar, porque os dados atuais são
apagados antes de o arquivo ser extraído.

## Remover

```bash
qh actual-budget --remove --apply           # para e tira, mantendo os dados
qh actual-budget --remove --purge --apply   # e apaga volumes, secrets e .env
```

O `--purge` também pede o nome digitado. O nó da tailnet não é desregistrado
por isso — isso é no admin do Tailscale.

## Comandos

```bash
systemctl --user status actual
podman logs -f actual
```

## Créditos

[actualbudget/actual](https://github.com/actualbudget/actual) — MIT

[Documentação oficial](https://actualbudget.org)
