# SABnzbd

<img src="https://cdn.jsdelivr.net/gh/homarr-labs/dashboard-icons/svg/sabnzbd.svg" width="64" height="64" alt="">

**[🇺🇸 Read in English](../sabnzbd.md)**

[< Media Stack](../../README.pt-BR.md)

Baixa da Usenet. Precisa de um provedor pago — Usenet não é de graça.

Porta **8081**, unit `media-stack-sabnzbd`.

O assistente pede servidor, usuário e senha do provedor. Depois ajuste as pastas para `/data/downloads`, para os *arr arquivarem o resultado renomeando em vez de copiar.

A interface fica na 8081 no host e na 8080 dentro do container — é esse o endereço que os *arr querem.

## Instalação

```bash
qh media-stack-sabnzbd
qh media-stack-sabnzbd --apply
```

Instalar a pasta — `qh media-stack --apply` — traz esta junto com as outras.

## Arquivos

```
media-stack-sabnzbd.container   unit
.env.example                    ambiente, compartilhado com a pasta toda
```

Dados em `~/.config/containers/volumes/media-stack/sabnzbd/config`.

## Atualizar

```bash
qh media-stack-sabnzbd --update --apply
```

Pinado em `version-5.0.4`. Nada atualiza sozinho — a versão nova entra quando você roda
o comando acima.

## Backup

```bash
qh media-stack --backup --apply --out ~/backups
```

O backup age sobre a pasta inteira, não sobre uma unit — nomear `media-stack-sabnzbd` aqui é
recusado. O arquivo guarda todos os apps de `media-stack`, e restaurar é
`qh media-stack --restore <arquivo> --apply`.

## Remover

```bash
qh media-stack-sabnzbd --remove --apply           # para, mantém os dados
qh media-stack-sabnzbd --remove --purge --apply   # e apaga o volume dela
```

Só o que é desta unit: o `.env` compartilhado e os outros apps da pasta ficam
intactos.

## Comandos

```bash
systemctl --user status media-stack-sabnzbd
podman logs -f sabnzbd
qh media-stack-sabnzbd --update --apply
```

## Créditos

[SABnzbd](https://github.com/sabnzbd/sabnzbd) — GPL-2.0

[Documentação oficial](https://sabnzbd.org/wiki/)
