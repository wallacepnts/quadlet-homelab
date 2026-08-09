# Jellyfin

<img src="https://cdn.jsdelivr.net/gh/homarr-labs/dashboard-icons/svg/jellyfin.svg" width="64" height="64" alt="">

**[🇺🇸 Read in English](../jellyfin.md)**

[< Media Stack](../../README.pt-BR.md)

Reproduz o que o stack juntou — filmes, séries e música — no navegador, na TV ou no celular.

Porta **8096**, unit `media-stack-jellyfin`.

Abra a porta e siga o assistente: crie o administrador e depois adicione uma biblioteca por tipo de conteúdo, apontando para as pastas dentro de `/data`.

A raiz de mídia é montada **somente leitura** aqui. O Jellyfin reproduz e nunca escreve, então um clique errado na interface não apaga a biblioteca — quem organiza são os *arr.

## Comandos

```bash
systemctl --user status media-stack-jellyfin
podman logs -f jellyfin
qh media-stack-jellyfin --update --apply
```

## Créditos

[Jellyfin](https://github.com/jellyfin/jellyfin) — GPL-2.0

[Documentação oficial](https://jellyfin.org/docs/)
