# Deluge

<img src="https://cdn.jsdelivr.net/gh/homarr-labs/dashboard-icons/svg/deluge.svg" width="64" height="64" alt="">

**[🇺🇸 Read in English](../deluge.md)**

[< Media Stack](../../README.pt-BR.md)

Baixa torrents. Roda sozinho; a VPN é uma escolha à parte.

Porta **8112**, unit `media-stack-deluge`.

A interface web pede uma senha na primeira visita — o padrão do upstream é `deluge`, e ele pede para trocar. Aponte a pasta de download para `/data/downloads`.

A porta 6881 é publicada, TCP e UDP, para outros peers conseguirem conectar. Sem ela o download ainda funciona, só que mais devagar.

Para mandar o tráfego por uma VPN, troque as linhas comentadas no `media-stack-deluge.container` e no `media-stack-gluetun.container`. É troca e não acréscimo: as duas não podem publicar a 8112 ao mesmo tempo.

## Instalação

```bash
qh media-stack-deluge
qh media-stack-deluge --apply
```

Instalar a pasta — `qh media-stack --apply` — traz esta junto com as outras.

## Arquivos

```
media-stack-deluge.container   unit
.env.example                   ambiente, compartilhado com a pasta toda
```

Dados em `~/.config/containers/volumes/media-stack/deluge/config`.

## Atualizar

```bash
qh media-stack-deluge --update --apply
```

Pinado em `2.2.0`. Nada atualiza sozinho — a versão nova entra quando você roda
o comando acima.

## Backup

```bash
qh media-stack-deluge --backup --apply --out ~/backups
```

O arquivo guarda só os diretórios desta unit. O `.env` compartilhado da pasta fica de fora, para restaurar um app não devolver uma cópia velha aos outros onze.

Ele para esta unit, empacota e religa. A frio de propósito: copiar banco em uso
gera um arquivo que só falha na hora de restaurar.

```bash
qh media-stack-deluge --restore ~/backups/media-stack-deluge-20260809-1200.tar.gz --apply
```

A restauração pede que você digite `media-stack-deluge` para confirmar, porque os dados
atuais são apagados antes de o arquivo ser desempacotado.

## Remover

```bash
qh media-stack-deluge --remove --apply           # para, mantém os dados
qh media-stack-deluge --remove --purge --apply   # e apaga o volume dela
```

Só o que é desta unit: o `.env` compartilhado e os outros apps da pasta ficam
intactos.

## Comandos

```bash
systemctl --user status media-stack-deluge
podman logs -f deluge
qh media-stack-deluge --update --apply
```

## Créditos

[Deluge](https://github.com/deluge-torrent/deluge) — GPL-3.0

[Documentação oficial](https://deluge.readthedocs.io/)
