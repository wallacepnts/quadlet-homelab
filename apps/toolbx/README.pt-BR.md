# Toolbx

<img src="https://cdn.jsdelivr.net/gh/containers/containertoolbx.org@main/apple-touch-icon.png" width="64" height="64" alt="">

**[🇺🇸 Read in English](./README.md)**

Shells descartáveis de Arch, Fedora, RHEL e Ubuntu, nas imagens oficiais do Toolbx — um lugar pra instalar ferramenta avulsa que não é o host.

## Instalar

```bash
qh toolbx            # mostra o plano
qh toolbx --apply
```

## Arquivos

```
toolbx-arch.container
toolbx-fedora.container
toolbx-rhel.container
toolbx-ubuntu.container
install.ini
```

Units da stack:

- `toolbx-arch`
- `toolbx-fedora`
- `toolbx-rhel`
- `toolbx-ubuntu`

## Atualizar

```bash
qh toolbx --update --apply
```

Fixado em `10.2`, `26.04`, `38d89c96265cfa7d6795c2e6f4b5b803df3e1f3d934fcfbabb346153aabdf985`. Nada atualiza sozinho — versão nova entra quando você
roda o comando acima.

## Backup

```bash
qh toolbx --backup --apply --out ~/backups
```

Ele para o serviço, empacota os dados, o `.env` e os secrets, e sobe de novo.
A frio de propósito: copiar banco vivo dá um arquivo que só falha na hora de
restaurar.

Pra restaurar, por cima dos dados atuais:

```bash
qh toolbx --restore ~/backups/toolbx-20260809-1200.tar.gz --apply
```

Ele pede que você digite `toolbx` pra confirmar, porque os dados atuais são
apagados antes de o arquivo ser extraído.

## Remover

```bash
qh toolbx --remove --apply           # para e tira, mantendo os dados
qh toolbx --remove --purge --apply   # e apaga volumes, secrets e .env
```

O `--purge` também pede o nome digitado. O nó da tailnet não é desregistrado
por isso — isso é no admin do Tailscale.

## Comandos

```bash
systemctl --user status toolbx
podman logs -f toolbx
```

## Créditos

[containers/toolbox](https://containertoolbx.org/) — Apache-2.0

[Documentação oficial](https://containertoolbx.org/)
