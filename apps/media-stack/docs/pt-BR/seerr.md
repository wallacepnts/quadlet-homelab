# Seerr

<img src="https://cdn.jsdelivr.net/gh/homarr-labs/dashboard-icons/svg/seerr.svg" width="64" height="64" alt="">

**[🇺🇸 Read in English](../seerr.md)**

[< Media Stack](../../README.pt-BR.md)

Onde um título é pedido. Ele repassa o pedido ao Sonarr ou ao Radarr e avisa quando chega.

Porta **5055**, unit `media-stack-seerr`.

O assistente pede primeiro o Jellyfin (`http://jellyfin:8096`) e depois o Sonarr e o Radarr. Cada um deles quer a API key, que fica em Settings -> General do próprio app.

É a peça para dar a alguém que deve pedir sem mexer no resto. É a única do stack pensada para mais de uma pessoa.

## Instalação

```bash
qh media-stack-seerr
qh media-stack-seerr --apply
```

Instalar a pasta — `qh media-stack --apply` — traz esta junto com as outras.

## Arquivos

```
media-stack-seerr.container   unit
.env.example                  ambiente, compartilhado com a pasta toda
```

Dados em `~/.config/containers/volumes/media-stack/seerr/config`.

## Atualizar

```bash
qh media-stack-seerr --update --apply
```

Pinado em `v3.4.1`. Nada atualiza sozinho — a versão nova entra quando você roda
o comando acima.

## Backup

```bash
qh media-stack-seerr --backup --apply --out ~/backups
```

O arquivo guarda só os diretórios desta unit. O `.env` compartilhado da pasta fica de fora, para restaurar um app não devolver uma cópia velha aos outros onze.

Ele para esta unit, empacota e religa. A frio de propósito: copiar banco em uso
gera um arquivo que só falha na hora de restaurar.

```bash
qh media-stack-seerr --restore ~/backups/media-stack-seerr-20260809-1200.tar.gz --apply
```

A restauração pede que você digite `media-stack-seerr` para confirmar, porque os dados
atuais são apagados antes de o arquivo ser desempacotado.

## Remover

```bash
qh media-stack-seerr --remove --apply           # para, mantém os dados
qh media-stack-seerr --remove --purge --apply   # e apaga o volume dela
```

Só o que é desta unit: o `.env` compartilhado e os outros apps da pasta ficam
intactos.

## Comandos

```bash
systemctl --user status media-stack-seerr
podman logs -f seerr
qh media-stack-seerr --update --apply
```

## Créditos

[Seerr](https://github.com/seerr-team/seerr) — MIT

[Documentação oficial](https://docs.seerr.dev/)
