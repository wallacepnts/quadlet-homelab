# SABnzbd

<img src="https://cdn.jsdelivr.net/gh/homarr-labs/dashboard-icons/svg/sabnzbd.svg" width="64" height="64" alt="">

**[🇺🇸 Read in English](../sabnzbd.md)**

[< Media Stack](../../README.pt-BR.md)

Baixa da Usenet. Precisa de um provedor pago — Usenet não é de graça.

Porta **8081**, unit `media-stack-sabnzbd`.

O assistente pede servidor, usuário e senha do provedor. Depois ajuste as pastas para `/data/downloads`, para os *arr arquivarem o resultado renomeando em vez de copiar.

A interface fica na 8081 no host e na 8080 dentro do container — é esse o endereço que os *arr querem.

## Comandos

```bash
systemctl --user status media-stack-sabnzbd
podman logs -f sabnzbd
qh media-stack-sabnzbd --update --apply
```

## Créditos

[SABnzbd](https://github.com/sabnzbd/sabnzbd) — GPL-2.0

[Documentação oficial](https://sabnzbd.org/wiki/)
