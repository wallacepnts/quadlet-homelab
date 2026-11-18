**Leia isto primeiro.** Funciona como painel, mas:

- **Ele segura o seu socket do Podman.** Lista, inicia, para e cria *qualquer* container do seu usuário: quem entra nele é, na prática, você neste host. Por isso a porta da rede local fica fechada na regra `tailnet` padrão.
- **Instalar apps pela loja dele falhou nos testes** (`mkdir /DATA: permission denied`). O que ele cria não é deste repositório: sem Quadlet, sem tag fixa, sem endurecimento. Para instalar apps, use a loja (`qh-store`) ou o `qh`.
- **Ele altera o seu Podman no primeiro início**: cria a rede `casa-net` (`10.22.0.0/16`, `SUBNET` no `.env`).

Abra `https://casa.<your-tailnet>.ts.net`; o `qh` imprime o login (`admin` e a senha gerada). Ao remover, `podman network rm casa-net` e remova o que ele instalou.
