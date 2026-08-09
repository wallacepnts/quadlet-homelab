# netboot.xyz

<img src="https://cdn.jsdelivr.net/gh/homarr-labs/dashboard-icons/svg/netbootxyz.svg" width="64" height="64" alt="">

**[🇺🇸 Read in English](./README.md)**

Menu de boot pela rede (PXE) pra instalar ou testar distros e ferramentas sem gravar pendrive.

## Instalar

```bash
qh netbootxyz            # mostra o plano
qh netbootxyz --apply
```

Abrir `http://<ip-do-host>:69` ou `https://netbootxyz.<your-tailnet>.ts.net`.

<details>
<summary><b>Instalação manual</b></summary>

```bash
# 1. Baixar a unit (sem precisar clonar o repositório)
mkdir -p ~/.config/containers/systemd
wget -P ~/.config/containers/systemd/ \
  https://raw.githubusercontent.com/wallacepnts/quadlet-homelab/main/apps/netbootxyz/netbootxyz.container

# 2. Diretórios de dados — bind mount exige que já existam antes do start
mkdir -p ~/.config/containers/volumes/netbootxyz/{config,assets}

# 3. Env não-secreto (todas as variáveis são opcionais, ver .env.example)
mkdir -p ~/.config/containers/env
wget -O ~/.config/containers/env/netbootxyz.env \
  https://raw.githubusercontent.com/wallacepnts/quadlet-homelab/main/apps/netbootxyz/.env.example

# 4. Subir
systemctl --user daemon-reload
systemctl --user start netbootxyz
```

</details>

## Arquivos

```
netbootxyz.container
.env.example
install.ini
```

## Atualizar

```bash
qh netbootxyz --update --apply
```

Fixado em `0.7.6-nbxyz23`. Nada atualiza sozinho — versão nova entra quando você
roda o comando acima.

## Backup

```bash
qh netbootxyz --backup --apply --out ~/backups
```

Ele para o serviço, empacota os dados, o `.env` e os secrets, e sobe de novo.
A frio de propósito: copiar banco vivo dá um arquivo que só falha na hora de
restaurar.

Pra restaurar, por cima dos dados atuais:

```bash
qh netbootxyz --restore ~/backups/netbootxyz-20260809-1200.tar.gz --apply
```

Ele pede que você digite `netbootxyz` pra confirmar, porque os dados atuais são
apagados antes de o arquivo ser extraído.

## Remover

```bash
qh netbootxyz --remove --apply           # para e tira, mantendo os dados
qh netbootxyz --remove --purge --apply   # e apaga volumes, secrets e .env
```

O `--purge` também pede o nome digitado. O nó da tailnet não é desregistrado
por isso — isso é no admin do Tailscale.

## Comandos

```bash
systemctl --user status netbootxyz
podman logs -f netbootxyz
```

## Créditos

[netbootxyz/docker-netbootxyz](https://github.com/netbootxyz/docker-netbootxyz) — MIT

[Documentação oficial](https://netboot.xyz/docs/docker)
