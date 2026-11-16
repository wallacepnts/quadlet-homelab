A instalação termina imprimindo o login (`admin` e uma senha gerada). Abra
`https://rclone.<your-tailnet>.ts.net`: o navegador pede os dois uma vez.

### O que ele enxerga

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

### Sua própria senha

```bash
qh rclone --reinstall --ask-secrets --apply
```

### Atualização

**A interface web é outro projeto e também está fixada.** Por padrão o `rcd`
pergunta ao GitHub pela release mais nova da interface a cada start.
`--rc-web-fetch-url` o aponta para uma release só (`v2.0.5`, a atual): o primeiro
start baixa essa e os seguintes reaproveitam o cache. Para trocar de release,
mude a tag nessa URL no `Exec=` e apague
`~/.config/containers/volumes/rclone/cache/rclone/webgui`.

### Remover

O `--purge` nunca toca em `~/.config/rclone`: é o config do próprio host. O nó
da tailnet não é desregistrado por isso — é feito no admin do Tailscale.
