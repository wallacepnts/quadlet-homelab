# rclone

<img src="https://cdn.jsdelivr.net/gh/homarr-labs/dashboard-icons/svg/rclone.svg" width="64" height="64" alt="">

O [rclone](https://rclone.org) rodando como servidor de controle remoto, com a
interface web ligada. Ele lê o mesmo `~/.config/rclone/rclone.conf` do comando
`rclone` do host: toda conta de nuvem já configurada lá aparece no navegador, e
dá para adicionar outras por ele.

## Primeiro acesso

A instalação termina imprimindo o login (`admin` e uma senha gerada). Abra
`https://rclone.<your-tailnet>.ts.net`: o navegador pede os dois uma vez.

## Arquivos

```
rclone.container   unit
install.ini        a receita do segredo, o login e de onde vêm as atualizações
```

Porta **5572** na LAN. Os arquivos da interface ficam em cache em
`~/.config/containers/volumes/rclone/cache`.

## O que ele enxerga

- **Só os remotes.** Nenhuma pasta local é montada, então a interface navega e
  move arquivos entre as contas do config, não pelo disco do host. Para usar uma
  pasta local como ponta, adicione um `Volume=` e um remote `alias` ou `local`
  apontando para o caminho dentro do container.
- **O config do host, com escrita.** `~/.config/rclone` é montado em
  leitura e escrita de propósito: provedores OAuth giram o refresh token, e um
  config só de leitura deixaria o antigo no disco até parar de funcionar. O
  Zerobyte monta a mesma pasta só para leitura, e o Air Explorer RS do host usa o
  mesmo arquivo, então há uma cópia de cada token. O mount é `:z` (rótulo
  compartilhado) porque mais de uma coisa o abre.
- **Quem tem a senha tem todas as contas.** A interface lê, copia e apaga em
  todos os remotes. Fica atrás da tailnet e de autenticação básica, nada além.

## Sua própria senha

```bash
qh rclone --reinstall --ask-secrets --apply
```

## Atualização

**A interface web é outro projeto e também está fixada.** Por padrão o `rcd`
pergunta ao GitHub pela release mais nova da interface a cada start.
`--rc-web-fetch-url` o aponta para uma release só (`v2.0.5`, a atual): o primeiro
start baixa essa e os seguintes reaproveitam o cache. Para trocar de release,
mude a tag nessa URL no `Exec=` e apague
`~/.config/containers/volumes/rclone/cache/rclone/webgui`.

## Hardening

Medido em `1.75.2`: root somente leitura com `/tmp` de 64 MB, zero
capabilities, sem privilégios extras. O processo roda com o seu próprio uid por
`UserNS=keep-id`, que não é hardening — é o que o deixa ler e reescrever um
`rclone.conf` com modo 600 que é seu. Sem isso o arquivo pertenceria ao root do
container e um processo comum não o leria.

Testado em laboratório com as mesmas flags: login (401 sem ele, 200 com), a
interface servida do cache depois de um restart, o health check e a criação de
um remote pela API, que gravou o `rclone.conf` com 600 e dono o usuário do host.
Não testado: um remote de nuvem de verdade, nem uma sessão no navegador pelo
tsdproxy.

## Remover

O `--purge` nunca toca em `~/.config/rclone`: é o config do próprio host. O nó
da tailnet não é desregistrado por isso — é feito no admin do Tailscale.

## Créditos

[rclone/rclone](https://github.com/rclone/rclone) — MIT. A interface web é o
[rclone/rclone-webui-react](https://github.com/rclone/rclone-webui-react).

[Documentação oficial](https://rclone.org/rc/)
