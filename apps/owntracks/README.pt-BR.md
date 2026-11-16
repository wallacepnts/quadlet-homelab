# OwnTracks

<img src="https://cdn.jsdelivr.net/gh/homarr-labs/dashboard-icons/svg/owntracks.svg" width="64" height="64" alt="">

**[🇺🇸 Read in English](./README.md)**

Rastreamento de localização pessoal via app de celular, com broker MQTT próprio e histórico de posições.

## Primeiro acesso

Abrir `http://<ip-do-host>:1883` ou `https://owntracks-ui.<your-tailnet>.ts.net`.

## Arquivos

```
owntracks-frontend.container
owntracks-mosquitto.container
owntracks-recorder.container
owntracks-net.network
.env.example
install.ini
```

Units da stack:

- `owntracks-frontend`
- `owntracks-mosquitto`
- `owntracks-recorder`
- `owntracks-n`

## Remover

O nó da tailnet não é desregistrado ao remover um app: isso é no admin do Tailscale.

## Créditos

[owntracks/recorder](https://github.com/owntracks/recorder) — GPL-2.0

[Documentação oficial](https://owntracks.org/booklet/)
