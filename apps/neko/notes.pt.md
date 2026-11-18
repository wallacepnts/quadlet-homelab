A instalação imprime o usuário e a senha no fim (a senha do admin é um segundo secret). Abra `http://<host-ip>:8018` ou `https://neko.<your-tailnet>.ts.net`.

**Depois defina `NEKO_NAT1TO1`** em `~/.config/containers/env/neko.env` com o endereço pelo qual os clientes alcançam o host (o IP da tailnet ou o da rede local) e rode `qh neko --update --apply`. Sem isso a página carrega e a tela fica preta.
