# Recuperação e migração

## A máquina morreu

Instalar primeiro, restaurar depois. O `--restore` não cria a unit, os
diretórios nem o env — ele só devolve os dados por cima de uma instalação que
já existe.

```bash
# 1. Host: Podman rootless, systemd --user, e as pastas
curl -fsSL https://raw.githubusercontent.com/wallacepnts/quadlet-homelab/main/bootstrap.sh | bash

# 2. Se você usa tailnet, este vem antes dos outros
qh tsdproxy --apply

# 3. Serviço por serviço
qh <app> --apply
qh <app> --restore ~/backups/<app>-....tar.gz --apply

# 4. Conferir
systemctl --user is-active <app>
podman ps --filter "name=<app>"
```

A restauração pede o nome do serviço digitado, porque ela apaga os dados atuais
antes de extrair.

## O que o backup não leva

- **As imagens.** O primeiro start puxa de novo, e é a parte demorada.
- **A identidade na tailnet.** Nó novo com o mesmo nome e endereço diferente; o
  antigo sai no admin do Tailscale.
- **Endereços gravados dentro dos dados** — `DOMAIN`, `ALLOWED_HOSTS` e afins.
  Se o nome do host mudou, esses precisam de revisão à mão.

## Migrando de outro servidor

```bash
# no servidor antigo
qh <app> --backup --apply --out ~/backups

# transferir
scp ~/backups/<app>-....tar.gz novohost:~/backups/

# no novo
qh <app> --apply
qh <app> --restore ~/backups/<app>-....tar.gz --apply
```

Antes de dar por migrado: o serviço responde na porta, os dados estão lá, e
qualquer endereço que o app tenha gravado no próprio banco aponta pro host
novo.
