# Auto-update

Três serviços atualizam sozinhos: Actual Budget, homepage e VaultZap. Todo o
resto tem tag fixa e sobe na mão.

## Ligando num serviço

```bash
systemctl --user enable --now podman-auto-update.timer   # uma vez, pro host
```

Depois, no `.container`:

```ini
Image=<registry>/<imagem>:<tag-flutuante>
AutoUpdate=registry
```

```bash
qh <app> --update --apply
```

## O que ele precisa pra ser seguro

- **Um `HealthCmd` de verdade.** Sem ele não há rollback — o Podman aplica a
  atualização às cegas. Com ele, container que falha o healthcheck volta pra
  imagem anterior.
- **Uma tag flutuante.** Em tag exata (`1.2.3`) o digest nunca muda e o
  `AutoUpdate=` não faz absolutamente nada.
- **Dado que você não se importe de ver mudar sem aviso.** Cofre de senha ou
  backend de sincronização merecem revisão antes de cada bump.

Voltando atrás na mão:

```bash
podman auto-update --rollback
```

## Por que a maioria está desligado

Tag fixa significa que a versão no host é a versão no repositório, e a
atualização acontece quando você decide. Os três que estão ligados têm
healthcheck funcionando, tag flutuante que o upstream de fato mantém, e dado
cuja perda seria um incômodo, não um desastre.
