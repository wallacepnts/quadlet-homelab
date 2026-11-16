# Beszel

<img src="https://cdn.jsdelivr.net/gh/homarr-labs/dashboard-icons/svg/beszel.svg" width="64" height="64" alt="">

**[🇺🇸 Read in English](./README.md)**

Dashboard leve de monitoramento de recursos (CPU/RAM/disco/rede/containers) deste host.

## Primeiro acesso

Abrir `http://<ip-do-host>:8090` ou `https://beszel.<your-tailnet>.ts.net`.

## Arquivos

```
beszel-agent.container
beszel.container
beszel-net.network
.env.example
install.ini
```

Units da stack:

- `beszel-agent`
- `beszel`
- `beszel-n`

## Remover

O nó da tailnet não é desregistrado ao remover um app: isso é no admin do Tailscale.

## Créditos

[henrygd/beszel](https://github.com/henrygd/beszel) — MIT

[Documentação oficial](https://beszel.dev)
