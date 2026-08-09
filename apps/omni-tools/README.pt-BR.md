# Omni Tools

<img src="https://cdn.jsdelivr.net/gh/homarr-labs/dashboard-icons/png/omni-tools.png" width="64" height="64" alt="">

**[🇺🇸 Read in English](./README.md)**

Conversores, geradores e calculadoras que rodam no navegador — nada é enviado ao servidor.

## Instalar

```bash
qh omni-tools            # mostra o plano
qh omni-tools --apply
```

Abrir `http://<ip-do-host>:8101` ou `https://omni-tools.<your-tailnet>.ts.net`.

<details>
<summary><b>Instalação manual</b></summary>

```bash
# 1. Baixar a unit (sem precisar clonar o repositório)
mkdir -p ~/.config/containers/systemd
wget -P ~/.config/containers/systemd/ \
  https://raw.githubusercontent.com/wallacepnts/quadlet-homelab/main/apps/omni-tools/omni-tools.container

# 2. Subir — sem mkdir, sem secret, sem env
systemctl --user daemon-reload
systemctl --user start omni-tools
```

</details>

## Arquivos

```
omni-tools.container
```

## Atualizar

```bash
qh omni-tools --update --apply
```

Fixado em `0.6.0`. Nada atualiza sozinho — versão nova entra quando você
roda o comando acima.

## Backup

```bash
qh omni-tools --backup --apply --out ~/backups
```

Ele para o serviço, empacota os dados, o `.env` e os secrets, e sobe de novo.
A frio de propósito: copiar banco vivo dá um arquivo que só falha na hora de
restaurar.

Pra restaurar, por cima dos dados atuais:

```bash
qh omni-tools --restore ~/backups/omni-tools-20260809-1200.tar.gz --apply
```

Ele pede que você digite `omni-tools` pra confirmar, porque os dados atuais são
apagados antes de o arquivo ser extraído.

## Remover

```bash
qh omni-tools --remove --apply           # para e tira, mantendo os dados
qh omni-tools --remove --purge --apply   # e apaga volumes, secrets e .env
```

O `--purge` também pede o nome digitado. O nó da tailnet não é desregistrado
por isso — isso é no admin do Tailscale.

## Comandos

```bash
systemctl --user status omni-tools
podman logs -f omni-tools
```

## Créditos

[iib0011/omni-tools](https://github.com/iib0011/omni-tools) — MIT

[Documentação oficial](https://omnitools.app)
