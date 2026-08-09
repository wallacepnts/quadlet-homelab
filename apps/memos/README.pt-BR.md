# Memos

<img src="https://cdn.jsdelivr.net/gh/homarr-labs/dashboard-icons/svg/memos.svg" width="64" height="64" alt="">

**[🇺🇸 Read in English](./README.md)**

Notas rápidas self-hosted, markdown-native e leve.

## Instalar

```bash
qh memos            # mostra o plano
qh memos --apply
```

Abrir `http://<ip-do-host>:5230` ou `https://memos.<your-tailnet>.ts.net` e
criar a conta. **O primeiro usuário que se cadastra vira admin**, sem
confirmação de e-mail. Logo depois, desligar o cadastro em Configurações →
"Allow user signup", senão qualquer um que alcance a URL cria uma conta.

<details>
<summary><b>Instalação manual</b></summary>

```bash
mkdir -p ~/.config/containers/systemd ~/.config/containers/env
mkdir -p ~/.config/containers/volumes/memos/data
podman unshare chown -R 1000:1000 ~/.config/containers/volumes/memos

wget -P ~/.config/containers/systemd/ \
  https://raw.githubusercontent.com/wallacepnts/quadlet-homelab/main/apps/memos/memos.container
wget -O ~/.config/containers/env/memos.env \
  https://raw.githubusercontent.com/wallacepnts/quadlet-homelab/main/apps/memos/.env.example

systemctl --user daemon-reload
systemctl --user start memos
```

</details>

## Arquivos

```
memos.container   unit
.env.example      ambiente
```

Dados em `~/.config/containers/volumes/memos/data` na porta **5230**.

## Atualizar

```bash
qh memos --update --apply
```

Fixado em `0.30.0`. Nada atualiza sozinho — versão nova entra quando você
roda o comando acima.

## Backup

```bash
qh memos --backup --apply --out ~/backups
```

Ele para o serviço, empacota os dados, o `.env` e os secrets, e sobe de novo. A
frio de propósito: copiar banco vivo dá um arquivo que só falha na hora de
restaurar.

Pra restaurar, por cima dos dados atuais:

```bash
qh memos --restore ~/backups/memos-20260809-1200.tar.gz --apply
```

Ele pede que você digite `memos` pra confirmar, porque os dados atuais são
apagados antes de o arquivo ser extraído.

## Remover

```bash
qh memos --remove --apply           # para e tira, mantendo os dados
qh memos --remove --purge --apply   # e apaga volumes, secrets e .env
```

O `--purge` também pede o nome digitado. O nó da tailnet não é desregistrado
por isso — isso é no admin do Tailscale.

## Comandos

```bash
systemctl --user status memos
podman logs -f memos
podman exec memos wget -qO- http://127.0.0.1:5230/healthz
```

## Créditos

[Memos](https://github.com/usememos/memos) — MIT

[Documentação oficial](https://www.usememos.com/docs)
