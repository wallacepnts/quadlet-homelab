A instalação exibe o usuário e a senha no final; a senha de administrador é um
segundo segredo. Abra `http://<ip-do-host>:8018` ou
`https://neko.<your-tailnet>.ts.net`.

**Depois ajuste o `NEKO_NAT1TO1`** no `~/.config/containers/env/neko.env` para
o endereço pelo qual os clientes alcançam o host — o IP da tailnet, ou o da
LAN. Sem isso a página carrega e a tela fica preta: o neko anuncia o IP do
próprio container para o fluxo de mídia, e ninguém de fora consegue rotear até
lá. Reinicie com `qh neko --update --apply`.

### Outros navegadores

O nome da imagem é a variante: `firefox` é o que vem, e o upstream também
publica `chromium`, `brave`, `vivaldi`, `tor-browser` e um `xfce` de área de
trabalho. Troque o `Image=` na unit e rode `qh neko --update --apply`. Os
derivados do Chromium pedem mais memória compartilhada que o Firefox — o
`ShmSize=2g` já é generoso, mas é esse o botão se uma aba morrer.

### Backup

Não há o que fazer backup: sem volume, sem estado. Remover e instalar de novo
devolve a mesma coisa.
