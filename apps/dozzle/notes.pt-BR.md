Abrir `https://dozzle.<your-tailnet>.ts.net`.

### O socket é a história inteira

```ini
Volume=%t/podman/podman.sock:/var/run/docker.sock:ro
```

Essa linha é o que faz o Dozzle funcionar, e é a única coisa que vale pensar
antes de instalar. O socket é a API inteira do Podman: montado somente-leitura,
ele impede este container de criar ou matar qualquer coisa, mas ele continua
**lendo tudo** — log, ambiente e configuração de todo container, inclusive os
que carregam segredo no ambiente.

Ou seja, quem abre a página lê tudo isso. Duas configurações estreitam isso, as
duas no `.env`:

- `DOZZLE_AUTH_PROVIDER=simple` põe um login na frente. Vem desligado, o que
  serve numa tailnet em que só você entra, e não serve em nenhuma outra.
- `DOZZLE_FILTER=name=media-stack` limita aos containers que você nomear.

O `DOZZLE_NO_ACTIONS=true` vem ligado: os botões que param e reiniciam
container falhariam contra um socket somente-leitura, e oferecer botão que não
funciona é pior que não oferecer.

### Backup

Não há o que copiar. Removê-lo não perde dado nenhum — os logs são do Podman.
