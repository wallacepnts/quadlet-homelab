# Dispatcharr

<img src="https://cdn.jsdelivr.net/gh/homarr-labs/dashboard-icons/svg/dispatcharr.svg" width="64" height="64" alt="">

**[🇺🇸 Read in English](../dispatcharr.md)**

[< Media Stack](../../README.pt-BR.md)

IPTV: organiza listas de canais, o guia e vídeo sob demanda.

Porta **9191**, unit `media-stack-dispatcharr`.

À parte da corrente: não usa o Prowlarr, os *arr nem os clientes de download, e guarda os próprios dados em vez de escrever na raiz de mídia.

Acrescente a lista M3U e a fonte de EPG pela interface. Ele carrega Postgres e Redis dentro do mesmo container, e é por isso que é uma unit e não três.

## Comandos

```bash
systemctl --user status media-stack-dispatcharr
podman logs -f dispatcharr
qh media-stack-dispatcharr --update --apply
```

## Créditos

[Dispatcharr](https://github.com/Dispatcharr/Dispatcharr) — CC-BY-NC-SA-4.0

[Documentação oficial](https://dispatcharr.github.io/Dispatcharr-Docs/)
