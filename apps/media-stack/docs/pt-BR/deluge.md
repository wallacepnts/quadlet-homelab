# Deluge

<img src="https://cdn.jsdelivr.net/gh/homarr-labs/dashboard-icons/svg/deluge.svg" width="64" height="64" alt="">

**[🇺🇸 Read in English](../deluge.md)**

[< Media Stack](../../README.pt-BR.md)

Baixa torrents. Roda sozinho; a VPN é uma escolha à parte.

Porta **8112**, unit `media-stack-deluge`.

A interface web pede uma senha na primeira visita — o padrão do upstream é `deluge`, e ele pede para trocar. Aponte a pasta de download para `/data/downloads`.

A porta 6881 é publicada, TCP e UDP, para outros peers conseguirem conectar. Sem ela o download ainda funciona, só que mais devagar.

Para mandar o tráfego por uma VPN, troque as linhas comentadas no `media-stack-deluge.container` e no `media-stack-gluetun.container`. É troca e não acréscimo: as duas não podem publicar a 8112 ao mesmo tempo.

## Comandos

```bash
systemctl --user status media-stack-deluge
podman logs -f deluge
qh media-stack-deluge --update --apply
```

## Créditos

[Deluge](https://github.com/deluge-torrent/deluge) — GPL-3.0

[Documentação oficial](https://deluge.readthedocs.io/)
