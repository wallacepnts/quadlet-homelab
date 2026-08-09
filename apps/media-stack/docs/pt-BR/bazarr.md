# Bazarr

<img src="https://cdn.jsdelivr.net/gh/homarr-labs/dashboard-icons/svg/bazarr.svg" width="64" height="64" alt="">

**[🇺🇸 Read in English](../bazarr.md)**

[< Media Stack](../../README.pt-BR.md)

Busca legendas para o que o Sonarr e o Radarr trouxeram.

Porta **6767**, unit `media-stack-bazarr`.

Settings -> Sonarr e Settings -> Radarr, com o endereço (`http://sonarr:8989`) e a API key de cada um. Depois Settings -> Languages, escolha os idiomas, e Settings -> Providers, escolha onde procurar.

Ele lê a biblioteca pelos *arr, então só enxerga o que eles conhecem. Arquivo colocado na pasta na mão não aparece.

## Comandos

```bash
systemctl --user status media-stack-bazarr
podman logs -f bazarr
qh media-stack-bazarr --update --apply
```

## Créditos

[Bazarr](https://github.com/morpheus65535/bazarr) — GPL-3.0

[Documentação oficial](https://wiki.bazarr.media/)
