# Gluetun

<img src="https://cdn.jsdelivr.net/gh/homarr-labs/dashboard-icons/svg/gluetun.svg" width="64" height="64" alt="">

**[🇺🇸 Read in English](../gluetun.md)**

[< Media Stack](../../README.pt-BR.md)

**Opcional.** Túnel VPN para colocar o Deluge dentro. Nada no stack depende dele.

Unit `media-stack-gluetun`.

Instalado junto com a pasta e parado até ser configurado. Preencha o `~/.config/containers/env/media-stack-gluetun.env` com o provedor, a chave e o servidor — o arquivo que vem é um exemplo, e o `WIREGUARD_ADDRESSES` tem um valor de espaço reservado que precisa ser trocado.

Depois descomente as portas e as labels desta unit e comente as correspondentes no `media-stack-deluge.container`. O Deluge deixa de ter interface própria: passa a usar a pilha de rede deste container, e o endereço no host vira o do Gluetun.

Ele roda `--privileged` porque cria uma interface de rede e reescreve a tabela de rotas. É o único container deste repositório que faz isso.

## Comandos

```bash
systemctl --user status media-stack-gluetun
podman logs -f gluetun
qh media-stack-gluetun --update --apply
```

## Créditos

[Gluetun](https://github.com/qdm12/gluetun) — MIT

[Documentação oficial](https://github.com/qdm12/gluetun/wiki)
