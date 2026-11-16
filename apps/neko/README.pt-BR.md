# neko

<img src="https://api.iconify.design/mdi/web-box.svg?color=%23888888" width="64" height="64" alt="">

**[🇺🇸 Read in English](./README.md)**

Um navegador rodando no servidor, transmitido para o seu por WebRTC. Várias
pessoas podem assistir à mesma sessão e passar o controle entre si, e nada do
que ele abre toca a sua máquina — que é a graça, seja para assistir algo junto
ou para abrir um link em que você não confia.

## Primeiro acesso

A instalação exibe o usuário e a senha no final; a senha de administrador é um
segundo segredo. Abra `http://<ip-do-host>:8018` ou
`https://neko.<your-tailnet>.ts.net`.

**Depois ajuste o `NEKO_NAT1TO1`** no `~/.config/containers/env/neko.env` para
o endereço pelo qual os clientes alcançam o host — o IP da tailnet, ou o da
LAN. Sem isso a página carrega e a tela fica preta: o neko anuncia o IP do
próprio container para o fluxo de mídia, e ninguém de fora consegue rotear até
lá. Reinicie com `qh neko --update --apply`.

## Arquivos

```
neko.container   unit
.env.example     ambiente
install.ini      as receitas das senhas
```

Web na **8018**, WebRTC na **59000** (TCP e UDP). Sem volume: a sessão é
descartável de propósito, e reiniciar dá um navegador novo.

O compose do upstream publica uma faixa de 101 portas UDP. O
`NEKO_WEBRTC_UDPMUX` e o `NEKO_WEBRTC_TCPMUX` colocam tudo isso numa porta só,
que é o que torna este um serviço de duas portas como os outros daqui.

## Outros navegadores

O nome da imagem é a variante: `firefox` é o que vem, e o upstream também
publica `chromium`, `brave`, `vivaldi`, `tor-browser` e um `xfce` de área de
trabalho. Troque o `Image=` na unit e rode `qh neko --update --apply`. Os
derivados do Chromium pedem mais memória compartilhada que o Firefox — o
`ShmSize=2g` já é generoso, mas é esse o botão se uma aba morrer.

## Backup

Não há o que fazer backup: sem volume, sem estado. Remover e instalar de novo
devolve a mesma coisa.

## Créditos

[neko](https://github.com/m1k1o/neko) por [m1k1o](https://github.com/m1k1o) —
Apache-2.0

[Documentação oficial](https://neko.m1k1o.net/)
