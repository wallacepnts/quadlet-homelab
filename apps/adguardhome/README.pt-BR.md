# AdGuard Home

<img src="https://cdn.jsdelivr.net/gh/homarr-labs/dashboard-icons/svg/adguard-home.svg" width="64" height="64" alt="">

**[🇺🇸 Read in English](./README.md)**

Servidor DNS recursivo com bloqueio de anúncios e rastreadores pra toda a rede.

## Instalar

```bash
qh adguardhome            # mostra o plano
qh adguardhome --apply
```

Abrir `http://<ip-do-host>:3006` ou `https://adguardhome.<your-tailnet>.ts.net`.

<details>
<summary><b>Instalação manual</b></summary>

```bash
# 1. Baixar as units (sem precisar clonar o repositório)
mkdir -p ~/.config/containers/systemd
wget -P ~/.config/containers/systemd/ \
  https://raw.githubusercontent.com/wallacepnts/quadlet-homelab/main/apps/adguardhome/adguardhome.container

# 2. Diretórios de dados — bind mount exige que já existam antes do start
mkdir -p ~/.config/containers/volumes/adguardhome/{conf,work}

# 3. Subir
systemctl --user daemon-reload
systemctl --user start adguardhome
```

</details>

## Arquivos

```
adguardhome.container
install.ini
```

## Atualizar

```bash
qh adguardhome --update --apply
```

Fixado em `v0.107.78`. Nada atualiza sozinho — versão nova entra quando você
roda o comando acima.

## Backup

```bash
qh adguardhome --backup --apply --out ~/backups
```

Ele para o serviço, empacota os dados, o `.env` e os secrets, e sobe de novo.
A frio de propósito: copiar banco vivo dá um arquivo que só falha na hora de
restaurar.

Pra restaurar, por cima dos dados atuais:

```bash
qh adguardhome --restore ~/backups/adguardhome-20260809-1200.tar.gz --apply
```

Ele pede que você digite `adguardhome` pra confirmar, porque os dados atuais são
apagados antes de o arquivo ser extraído.

## Remover

```bash
qh adguardhome --remove --apply           # para e tira, mantendo os dados
qh adguardhome --remove --purge --apply   # e apaga volumes, secrets e .env
```

O `--purge` também pede o nome digitado. O nó da tailnet não é desregistrado
por isso — isso é no admin do Tailscale.

## Comandos

```bash
systemctl --user status adguardhome
podman logs -f adguardhome
```

## Créditos

[AdguardTeam/AdGuardHome](https://github.com/AdguardTeam/AdGuardHome) — GPL-3.0

[Documentação oficial](https://adguard.com/adguard-home/overview.html)
