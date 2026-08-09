# mdrop

<img src="https://cdn.simpleicons.org/markdown/888888" width="64" height="64" alt="">

**[🇺🇸 Read in English](./README.md)**

Converte PDF, Office, imagem e áudio para Markdown pela web, sem estado e sem sair da máquina.

## Instalar

```bash
qh mdrop            # mostra o plano
qh mdrop --apply
```

Abrir `http://<ip-do-host>:8292` ou `https://mdrop.<your-tailnet>.ts.net`.

<details>
<summary><b>Instalação manual</b></summary>

```bash
# 1. Baixar a unit (sem precisar clonar o repositório)
mkdir -p ~/.config/containers/systemd
wget -P ~/.config/containers/systemd/ \
  https://raw.githubusercontent.com/wallacepnts/quadlet-homelab/main/apps/mdrop/mdrop.container

# 2. Subir — sem mkdir, sem secret, sem env
systemctl --user daemon-reload
systemctl --user start mdrop
```

</details>

## Arquivos

```
mdrop.container
```

## Atualizar

```bash
qh mdrop --update --apply
```

Fixado em `692d8f63593667d78ef67d3b79b9e68ce22c8244ace30036fac0fd24cd529ca4`. Nada atualiza sozinho — versão nova entra quando você
roda o comando acima.

## Backup

```bash
qh mdrop --backup --apply --out ~/backups
```

Ele para o serviço, empacota os dados, o `.env` e os secrets, e sobe de novo.
A frio de propósito: copiar banco vivo dá um arquivo que só falha na hora de
restaurar.

Pra restaurar, por cima dos dados atuais:

```bash
qh mdrop --restore ~/backups/mdrop-20260809-1200.tar.gz --apply
```

Ele pede que você digite `mdrop` pra confirmar, porque os dados atuais são
apagados antes de o arquivo ser extraído.

## Remover

```bash
qh mdrop --remove --apply           # para e tira, mantendo os dados
qh mdrop --remove --purge --apply   # e apaga volumes, secrets e .env
```

O `--purge` também pede o nome digitado. O nó da tailnet não é desregistrado
por isso — isso é no admin do Tailscale.

## Comandos

```bash
systemctl --user status mdrop
podman logs -f mdrop
```

## Créditos

[samapriya/mdrop](https://github.com/samapriya/mdrop) — MIT

[Documentação oficial](https://mdrop.remotelab.dev)
