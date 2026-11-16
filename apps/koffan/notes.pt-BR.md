O `qh` gera a senha e mostra uma vez, no fim da instalação. Abrir
`https://koffan.<your-tailnet>.ts.net`.

### A senha

É a única credencial, então é um secret do Podman e não uma linha no `.env`
como o compose oficial sugere — lá o padrão que vem é `shopping123`. O `qh`
gera com `rand-base64 18` e mostra uma vez.

Pra trocar depois:

```bash
podman secret rm koffan-password
openssl rand -base64 18 | tr -d '\n' | podman secret create koffan-password -
qh koffan --update --apply
```

### Notificações

O `WEBHOOK_URL` do `.env` é chamado a cada mudança. Apontado pro
ntfy daqui, o celular apita quando alguém acrescenta
pão no caminho de casa:

```ini
WEBHOOK_URL=http://ntfy:2586/compras
```

Os dois containers estão na `tsdproxy-net`, então `ntfy` resolve pelo nome.

### Backup

Para o serviço, empacota a pasta de dados e o `.env`, e sobe de novo.
