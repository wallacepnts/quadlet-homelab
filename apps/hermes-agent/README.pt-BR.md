# Hermes Agent

<img src="https://cdn.jsdelivr.net/gh/NousResearch/hermes-agent@main/website/static/img/logo.png" width="64" height="64" alt="">

**[🇺🇸 Read in English](./README.md)**

Agente de IA pessoal com habilidades e memória, expondo uma API compatível com a da OpenAI pros outros serviços chamarem.

## Primeiro acesso

Abrir `http://<ip-do-host>:8642` ou `https://hermes.<your-tailnet>.ts.net`.

## Arquivos

```
hermes-agent.container
.env.example
install.ini
```

## Sem limite de memória

A unit define `PidsLimit=`, não `Memory=`. Limite de memória em unit rootless
exige o controlador de memória delegado ao gerenciador de usuário, e num host
onde ele não é, o container nem chega a ser criado:

```
memory.swap.max: no such file or directory
```

Pra saber se o seu host delega:

```bash
ls /sys/fs/cgroup/user.slice/user-$(id -u).slice/user@$(id -u).service/ | grep memory.max
```

## Remover

O nó da tailnet não é desregistrado ao remover um app: isso é no admin do Tailscale.

## Créditos

[NousResearch/hermes-agent](https://github.com/NousResearch/hermes-agent) — MIT

[Documentação oficial](https://hermes-agent.nousresearch.com)
