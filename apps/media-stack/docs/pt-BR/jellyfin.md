# Jellyfin

<img src="https://cdn.jsdelivr.net/gh/homarr-labs/dashboard-icons/svg/jellyfin.svg" width="64" height="64" alt="">

**[🇺🇸 Read in English](../jellyfin.md)**

[< Media Stack](../../README.pt-BR.md)

Reproduz o que o stack juntou — filmes, séries e música — no navegador, na TV ou no celular.

Porta **8096**, unit `media-stack-jellyfin`.

Abra a porta e siga o assistente: crie o administrador e depois adicione uma biblioteca por tipo de conteúdo, apontando para as pastas dentro de `/data`.

A raiz de mídia é montada **somente leitura** aqui. O Jellyfin reproduz e nunca escreve, então um clique errado na interface não apaga a biblioteca — quem organiza são os *arr.

## Instalação

```bash
qh media-stack-jellyfin
qh media-stack-jellyfin --apply
```

Instalar a pasta — `qh media-stack --apply` — traz esta junto com as outras.

## Arquivos

```
media-stack-jellyfin.container   unit
```

Dados em `~/.config/containers/volumes/media-stack/jellyfin/config`, `~/.config/containers/volumes/media-stack/jellyfin/cache`.

## Atualizar

```bash
qh media-stack-jellyfin --update --apply
```

Pinado em `10.11.11`. Nada atualiza sozinho — a versão nova entra quando você roda
o comando acima.

## Backup

```bash
qh media-stack --backup --apply --out ~/backups
```

O backup age sobre a pasta inteira, não sobre uma unit — nomear `media-stack-jellyfin` aqui é
recusado. O arquivo guarda todos os apps de `media-stack`, e restaurar é
`qh media-stack --restore <arquivo> --apply`.

## Remover

```bash
qh media-stack-jellyfin --remove --apply           # para, mantém os dados
qh media-stack-jellyfin --remove --purge --apply   # e apaga o volume dela
```

Só o que é desta unit: o `.env` compartilhado e os outros apps da pasta ficam
intactos.

## Comandos

```bash
systemctl --user status media-stack-jellyfin
podman logs -f jellyfin
qh media-stack-jellyfin --update --apply
```

## Créditos

[Jellyfin](https://github.com/jellyfin/jellyfin) — GPL-2.0

[Documentação oficial](https://jellyfin.org/docs/)
