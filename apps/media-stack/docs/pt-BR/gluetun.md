# Gluetun

<img src="https://cdn.jsdelivr.net/gh/homarr-labs/dashboard-icons/svg/gluetun.svg" width="64" height="64" alt="">

**[🇺🇸 Read in English](../gluetun.md)**

[< Media Stack](../../README.pt-BR.md)

**Opcional.** Túnel VPN para colocar o Deluge dentro. Nada no stack depende dele.

Unit `media-stack-gluetun`.

Instalado junto com a pasta e parado até ser configurado. Preencha o `~/.config/containers/env/media-stack-gluetun.env` com o provedor, a chave e o servidor — o arquivo que vem é um exemplo, e o `WIREGUARD_ADDRESSES` tem um valor de espaço reservado que precisa ser trocado.

Depois descomente as portas e as labels desta unit e comente as correspondentes no `media-stack-deluge.container`. O Deluge deixa de ter interface própria: passa a usar a pilha de rede deste container, e o endereço no host vira o do Gluetun.

Ele roda `--privileged` porque cria uma interface de rede e reescreve a tabela de rotas. É o único container deste repositório que faz isso.

## Instalação

```bash
qh media-stack-gluetun
qh media-stack-gluetun --apply
```

Instalar a pasta — `qh media-stack --apply` — traz esta junto com as outras.

## Arquivos

```
media-stack-gluetun.container     unit
media-stack-gluetun.env.example   ambiente
```

## Atualizar

```bash
qh media-stack-gluetun --update --apply
```

Pinado em `latest`. Nada atualiza sozinho — a versão nova entra quando você roda
o comando acima.

## Backup

```bash
qh media-stack-gluetun --backup --apply --out ~/backups
```

O arquivo guarda os diretórios desta unit, os segredos dela e o `.env` próprio — nada que uma irmã também leia.

Ele para esta unit, empacota e religa. A frio de propósito: copiar banco em uso
gera um arquivo que só falha na hora de restaurar.

```bash
qh media-stack-gluetun --restore ~/backups/media-stack-gluetun-20260809-1200.tar.gz --apply
```

A restauração pede que você digite `media-stack-gluetun` para confirmar, porque os dados
atuais são apagados antes de o arquivo ser desempacotado.

## Remover

```bash
qh media-stack-gluetun --remove --apply
```

Ela não tem volume, então o `--purge` não tem o que apagar a mais aqui. O `.env`
compartilhado e os outros apps da pasta ficam intactos.

## Comandos

```bash
systemctl --user status media-stack-gluetun
podman logs -f gluetun
qh media-stack-gluetun --update --apply
```

## Créditos

[Gluetun](https://github.com/qdm12/gluetun) — MIT

[Documentação oficial](https://github.com/qdm12/gluetun/wiki)
