# Instagram Monitor

<img src="https://api.iconify.design/mdi/instagram.svg?color=%23E1306C" width="64" height="64" alt="">

Suite OSINT de monitoramento de Instagram em tempo real.
O [instagram_monitor](https://github.com/misiektoja/instagram_monitor) rastreia
posts novos, stories, mudanças de seguidores, foto de perfil e bio — tudo sem
usar a API oficial. Pode monitorar contas públicas de forma anônima, ou entrar
com sessão para acessar stories e reels.

O dashboard web fica acessível via tsdproxy — feed de atividade ao vivo e
controles remotos de qualquer dispositivo na tailnet.

## Instalação

```bash
qh instagram-monitor            # mostra o plano
qh instagram-monitor --apply
```

Depois da instalação, rode o wizard de setup uma vez para criar o config e o
`.env` dentro do volume de dados:

```bash
podman run -it --rm \
  -v ~/.config/containers/volumes/instagram-monitor/data:/data:Z \
  -v ~/.config/containers/volumes/instagram-monitor/session:/home/instagram/.config/instaloader:Z \
  --user 10001:10001 \
  docker.io/misiektoja/instagram-monitor:v4.0.2 --setup
```

O wizard pergunta os usernames alvo, configuração de notificações e
opcionalmente uma sessão do Instagram (para stories e contas privadas). Depois
de concluir, reinicie o serviço:

```bash
systemctl --user restart instagram-monitor
```

<details>
<summary><b>Instalação manual (avançado)</b></summary>

```bash
# 1. Baixar a unit
mkdir -p ~/.config/containers/systemd
wget -P ~/.config/containers/systemd/ \
  https://raw.githubusercontent.com/wallacepnts/quadlet-homelab/main/apps/instagram-monitor/instagram-monitor.container

# 2. Diretórios de dados e sessão
mkdir -p ~/.config/containers/volumes/instagram-monitor/{data,session}
podman unshare chown -R 10001:10001 \
  ~/.config/containers/volumes/instagram-monitor/data \
  ~/.config/containers/volumes/instagram-monitor/session

# 3. Config seed (libera o dashboard via tsdproxy)
wget -O ~/.config/containers/volumes/instagram-monitor/data/instagram_monitor.conf \
  https://raw.githubusercontent.com/wallacepnts/quadlet-homelab/main/apps/instagram-monitor/instagram_monitor.conf
podman unshare chown 10001:10001 \
  ~/.config/containers/volumes/instagram-monitor/data/instagram_monitor.conf

# 4. Rodar o wizard de setup
podman run -it --rm \
  -v ~/.config/containers/volumes/instagram-monitor/data:/data:Z \
  -v ~/.config/containers/volumes/instagram-monitor/session:/home/instagram/.config/instaloader:Z \
  --user 10001:10001 \
  docker.io/misiektoja/instagram-monitor:v4.0.2 --setup

systemctl --user daemon-reload
systemctl --user start instagram-monitor
```

</details>

## Arquivos

```
instagram-monitor.container   unit
instagram_monitor.conf        config seed (WEB_DASHBOARD_ALLOWED_HOSTS)
install.ini                   receita de config e de onde vêm as atualizações
```

Dados em `~/.config/containers/volumes/instagram-monitor/data` (config, `.env`,
mídia baixada). Sessão do instaloader em
`~/.config/containers/volumes/instagram-monitor/session`. Porta **8128** na
LAN, dashboard web em `https://instagram-monitor.<your-tailnet>.ts.net`.

## Wizard de setup

A ferramenta gerencia seu próprio config: um `.env` para secrets (senha da
sessão do Instagram, senha SMTP, URLs de webhook) e um
`instagram_monitor.conf` para alvos e comportamento. Os dois vivem no volume de
dados e são criados pelo wizard `--setup`. Não usa podman secrets — a
ferramenta lê seu próprio `.env` de `/data/.env`.

Para rodar o wizard de novo (adicionar alvos, mudar notificações):

```bash
systemctl --user stop instagram-monitor
podman run -it --rm \
  -v ~/.config/containers/volumes/instagram-monitor/data:/data:Z \
  -v ~/.config/containers/volumes/instagram-monitor/session:/home/instagram/.config/instaloader:Z \
  --user 10001:10001 \
  docker.io/misiektoja/instagram-monitor:v4.0.2 --setup
systemctl --user start instagram-monitor
```

## Sessão do Instagram

Sem login, a ferramenta monitora apenas contas públicas. Para acessar stories,
reels e lista de seguidores, importe uma sessão do navegador:

```bash
podman run -it --rm \
  -v ~/.config/containers/volumes/instagram-monitor/data:/data:Z \
  -v ~/.config/containers/volumes/instagram-monitor/session:/home/instagram/.config/instaloader:Z \
  --user 10001:10001 \
  docker.io/misiektoja/instagram-monitor:v4.0.2 \
  --import-browser-session --browser firefox
```

Sessões do Firefox podem ser importadas de dentro do container. Navegadores
baseados em Chromium não funcionam no container — use login por senha ou
exporte cookies manualmente.

## Atualização

```bash
qh instagram-monitor --update --apply
```

Fixado em `v4.0.2`. Nada atualiza sozinho.

## Hardening

Tudo, medido em `v4.0.2`: root read-only com `/tmp`, zero capabilities,
`User=10001` (o usuário `instagram` da imagem). `PodmanArgs=--init` porque o
processo Python cria filhos (sessões do instaloader) que precisam de reaping de
zumbis — o compose upstream usa `init: true`.

## Backup

```bash
qh instagram-monitor --backup --apply --out ~/backups
```

O volume de dados guarda o config, `.env` e mídia baixada. O volume de sessão
guarda o cookie do instaloader — os dois são necessários para uma restauração
completa.

## Remover

```bash
qh instagram-monitor --remove --apply           # para, mantém os dados
qh instagram-monitor --remove --purge --apply   # e apaga os dois volumes
```

## Comandos

```bash
systemctl --user status instagram-monitor
podman logs -f instagram-monitor
```

## Créditos

[misiektoja/instagram_monitor](https://github.com/misiektoja/instagram_monitor) — MIT.
