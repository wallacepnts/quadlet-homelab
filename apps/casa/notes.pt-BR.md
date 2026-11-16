### Leia isto primeiro

Ele funciona como painel, mas uma das duas funções dele não funcionou nos testes, e a outra é muito acesso.

- **Ele segura o seu socket do Podman.** Lista, inicia, para e cria *qualquer* container do seu usuário, inclusive os dos Quadlets — quem está logado nele é, na prática, você neste host. Por isso a conta é criada no primeiro start, com senha gerada, e por isso a porta da rede local fica fechada na regra de acesso `tailnet`, que é a padrão.
- **Instalar apps pela loja dele falhou.** Testado no Podman 6.1.4 rootless, openSUSE Tumbleweed com SELinux enforcing, imagem `0.4.15`, pela API: o Memos da própria loja e um compose escrito à mão terminaram em `making volume mountpoint for volume /DATA/AppData/memos/memos: mkdir /DATA: permission denied`. O caminho de dentro do container do CasaOS não é convertido no caminho do host, então o Podman, rodando como você, tenta criar `/DATA` na raiz. O `DATA_ROOT` chega ao processo que instala; a conversão é que não aconteceu. O que **não** foi testado: instalar pela interface web, o gerenciador de arquivos e discos, e o compartilhamento por Samba.
- **O que ele cria não é deste repositório.** Mesmo onde uma instalação funcione, os containers saem dos compose da loja: sem Quadlet, sem tag fixada (o Excalidraw da loja é `:latest`), sem hardening, sem `qh`. Para instalar apps, use o `qh` ou a loja (`qh-store`).
- **Ele muda o seu Podman no primeiro start:** cria a rede `casa-net` (`10.22.0.0/16`, ajustável com `SUBNET` no `.env`) e se conecta a ela.

### Primeiro acesso

Abra `https://casa.<your-tailnet>.ts.net`, ou `http://<ip-do-host>:8129` com `--access local` ou `both`. O `qh` imprime o login (`admin` e a senha gerada) no fim da instalação.

### Por que a unit é assim

Cada linha abaixo foi medida, e as recusas estão em [docs/pt-BR/endurecimento.md](../../docs/pt-BR/endurecimento.md).

- **Root, com seis capabilities.** O entrypoint se recusa a rodar sem privilégio e baixa para o uid 1000 sozinho. Sem `chown`, `dac_override`, `fowner`, `setuid` ou `setgid` ele não sobe; sem `kill` ele sobe, mas uma parada leva 11 s e termina em `SIGKILL`.
- **`PodmanArgs=--cgroupns=host`.** O entrypoint acha o próprio container pelo id em `/proc/self/cgroup`. Um cgroup namespace privado (o padrão do Podman) não mostra nenhum, e o plano B dele devolve o nome errado: `Failed to identify the current container!`.
- **`ContainerName=casa` fica.** É assim que o entrypoint se encontra, e é por esse nome que ele se conecta à `casa-net`.
- **`SecurityLabelType=container_runtime_t`** para o socket, como nas outras units que o montam (só `:z` deixa a API recusando sob SELinux).
- **Sem `ReadOnly`.** O entrypoint reescreve `/etc/group` e o banco de usuários a cada start.
- **O healthcheck é o `/v1/users/status`**, não o `/`: o gateway responde `200` em `/` alguns segundos antes de o serviço de usuários subir, enquanto o `/v1/users/status` responde `404` até lá.

### Backup

Tudo o que o CasaOS guarda — contas, bancos, dados dos apps dele — está em `/DATA`, que é o único volume.

### Remover

O que o CasaOS criou no seu Podman também não é removido — a rede `casa-net` e qualquer container instalado por ele:

```bash
podman network rm casa-net
```

Um fork do [worph/casa-img](https://github.com/worph/casa-img), que empacota o CasaOS para Docker. MIT.
