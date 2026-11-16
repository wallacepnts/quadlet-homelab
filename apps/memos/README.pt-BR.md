# Memos

<img src="https://cdn.jsdelivr.net/gh/homarr-labs/dashboard-icons/svg/memos.svg" width="64" height="64" alt="">

**[🇺🇸 Read in English](./README.md)**

Notas rápidas self-hosted, markdown-native e leve.

## Primeiro acesso

Abrir `http://<ip-do-host>:5230` ou `https://memos.<your-tailnet>.ts.net` e
criar a conta. **O primeiro usuário que se cadastra vira admin**, sem
confirmação de e-mail. Logo depois, desligar o cadastro em Configurações →
"Allow user signup", senão qualquer um que alcance a URL cria uma conta.

## Arquivos

```
memos.container   unit
.env.example      ambiente
```

Dados em `~/.config/containers/volumes/memos/data` na porta **5230**.

## Remover

O nó da tailnet não é desregistrado ao remover um app: isso é no admin do Tailscale.

## Créditos

[Memos](https://github.com/usememos/memos) — MIT

[Documentação oficial](https://www.usememos.com/docs)
