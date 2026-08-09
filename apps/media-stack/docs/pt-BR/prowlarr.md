# Prowlarr

<img src="https://cdn.jsdelivr.net/gh/homarr-labs/dashboard-icons/svg/prowlarr.svg" width="64" height="64" alt="">

**[🇺🇸 Read in English](../prowlarr.md)**

[< Media Stack](../../README.pt-BR.md)

Guarda a lista de indexadores num lugar só e envia para o Sonarr, o Radarr e o Lidarr.

Porta **9696**, unit `media-stack-prowlarr`.

Adicione os indexadores aqui e depois vá em Settings -> Apps, uma entrada por *arr com o endereço (`http://sonarr:8989`) e a API key. A partir daí, indexador acrescentado aqui aparece em todos.

Configure este primeiro. Fazer os *arr antes significa cadastrar cada indexador três vezes — e de novo toda vez que um mudar.

## Instalação

```bash
qh media-stack-prowlarr
qh media-stack-prowlarr --apply
```

Instalar a pasta — `qh media-stack --apply` — traz esta junto com as outras.

## Arquivos

```
media-stack-prowlarr.container   unit
.env.example                     ambiente, compartilhado com a pasta toda
```

Dados em `~/.config/containers/volumes/media-stack/prowlarr/config`.

## Atualizar

```bash
qh media-stack-prowlarr --update --apply
```

Pinado em `2.5.2`. Nada atualiza sozinho — a versão nova entra quando você roda
o comando acima.

## Backup

```bash
qh media-stack-prowlarr --backup --apply --out ~/backups
```

O arquivo guarda só os diretórios desta unit. O `.env` compartilhado da pasta fica de fora, para restaurar um app não devolver uma cópia velha aos outros onze.

Ele para esta unit, empacota e religa. A frio de propósito: copiar banco em uso
gera um arquivo que só falha na hora de restaurar.

```bash
qh media-stack-prowlarr --restore ~/backups/media-stack-prowlarr-20260809-1200.tar.gz --apply
```

A restauração pede que você digite `media-stack-prowlarr` para confirmar, porque os dados
atuais são apagados antes de o arquivo ser desempacotado.

## Remover

```bash
qh media-stack-prowlarr --remove --apply           # para, mantém os dados
qh media-stack-prowlarr --remove --purge --apply   # e apaga o volume dela
```

Só o que é desta unit: o `.env` compartilhado e os outros apps da pasta ficam
intactos.

## Comandos

```bash
systemctl --user status media-stack-prowlarr
podman logs -f prowlarr
qh media-stack-prowlarr --update --apply
```

## Créditos

[Prowlarr](https://github.com/Prowlarr/Prowlarr) — GPL-3.0

[Documentação oficial](https://wiki.servarr.com/prowlarr)
