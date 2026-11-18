Depois da instalação, rode o assistente uma vez; ele cria a configuração e o `.env` dentro do volume de dados:

```bash
podman run -it --rm \
  -v ~/.config/containers/volumes/instagram-monitor/data:/data:Z \
  -v ~/.config/containers/volumes/instagram-monitor/session:/home/instagram/.config/instaloader:Z \
  --user 10001:10001 \
  docker.io/misiektoja/instagram-monitor:v4.0.2 --setup
```

Ele pergunta os usuários a monitorar, as notificações e, opcionalmente, uma sessão do Instagram (stories, contas privadas). Depois `systemctl --user restart instagram-monitor`. Para rodar de novo, pare o serviço antes. Não usa secrets do Podman: a ferramenta lê o próprio `/data/.env`.
