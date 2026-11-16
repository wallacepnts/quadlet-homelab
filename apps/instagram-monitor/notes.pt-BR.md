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

### Wizard de setup

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

### Sessão do Instagram

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

### Backup

O volume de dados guarda o config, `.env` e mídia baixada. O volume de sessão
guarda o cookie do instaloader — os dois são necessários para uma restauração
completa.
