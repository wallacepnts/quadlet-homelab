# netboot.xyz

<img src="https://cdn.jsdelivr.net/gh/homarr-labs/dashboard-icons/svg/netbootxyz.svg" width="64" height="64" alt="">

**[🇺🇸 Read in English](./README.md)**

Menu de boot pela rede (PXE) pra instalar ou testar distros e ferramentas sem gravar pendrive.

## Primeiro acesso

Abrir `http://<ip-do-host>:8088` ou `https://netbootxyz.<your-tailnet>.ts.net`. A
69 também é publicada, mas é TFTP sobre UDP — o que as máquinas que dão boot por
ele falam, não uma página que o navegador abra.

## Arquivos

```
netbootxyz.container
.env.example
install.ini
```

## Remover

O nó da tailnet não é desregistrado ao remover um app: isso é no admin do Tailscale.

## Créditos

[netbootxyz/docker-netbootxyz](https://github.com/netbootxyz/docker-netbootxyz) — MIT

[Documentação oficial](https://netboot.xyz/docs/docker)
