# Downtify

<img src="https://cdn.jsdelivr.net/gh/homarr-labs/dashboard-icons/png/downtify.png" width="64" height="64" alt="">

**[🇺🇸 Read in English](../downtify.md)**

[< Media Stack](../../README.pt-BR.md)

Cole um link do Spotify e a música cai no disco.

Porta **8000**, unit `media-stack-downtify`.

Escreve direto em `/data/downloads`, a mesma pasta dos clientes de download. Não passa pelo Lidarr e nada renomeia o resultado — é o atalho para um álbum, não uma biblioteca.

Esse subdiretório precisa existir antes do primeiro start, porque é montado sozinho. A instalação cria.

## Comandos

```bash
systemctl --user status media-stack-downtify
podman logs -f downtify
qh media-stack-downtify --update --apply
```

## Créditos

[Downtify](https://github.com/henriquesebastiao/downtify) — GPL-3.0

[Documentação oficial](https://github.com/henriquesebastiao/downtify#readme)
