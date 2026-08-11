# Dozzle

<img src="https://cdn.jsdelivr.net/gh/homarr-labs/dashboard-icons/svg/dozzle.svg" width="64" height="64" alt="">

**[🇺🇸 Read in English](./README.md)**

Log ao vivo de cada container, no navegador. Substitui o `podman logs -f` que
você rodaria por SSH, com busca, vários containers lado a lado e sem terminal.

Ele não guarda nada: sem banco, sem volume, sem cópia de log. O que você vê é o
que o Podman tem naquele momento.

## Instalação

```bash
qh dozzle            # mostra o plano
qh dozzle --apply
```

Abrir `https://dozzle.<your-tailnet>.ts.net`.

<details>
<summary><b>Instalação manual (avançado)</b></summary>

```bash
mkdir -p ~/.config/containers/systemd ~/.config/containers/env

wget -P ~/.config/containers/systemd/ \
  https://raw.githubusercontent.com/wallacepnts/quadlet-homelab/main/apps/dozzle/dozzle.container
wget -O ~/.config/containers/env/dozzle.env \
  https://raw.githubusercontent.com/wallacepnts/quadlet-homelab/main/apps/dozzle/.env.example

systemctl --user daemon-reload
systemctl --user start dozzle
```

</details>

## Arquivos

```
dozzle.container   unit
.env.example       ambiente
```

Sem volume, porque não há o que guardar.

## O socket é a história inteira

```ini
Volume=%t/podman/podman.sock:/var/run/docker.sock:ro
```

Essa linha é o que faz o Dozzle funcionar, e é a única coisa que vale pensar
antes de instalar. O socket é a API inteira do Podman: montado somente-leitura,
ele impede este container de criar ou matar qualquer coisa, mas ele continua
**lendo tudo** — log, ambiente e configuração de todo container, inclusive os
que carregam segredo no ambiente.

Ou seja, quem abre a página lê tudo isso. Duas configurações estreitam isso, as
duas no `.env`:

- `DOZZLE_AUTH_PROVIDER=simple` põe um login na frente. Vem desligado, o que
  serve numa tailnet em que só você entra, e não serve em nenhuma outra.
- `DOZZLE_FILTER=name=media-stack` limita aos containers que você nomear.

O `DOZZLE_NO_ACTIONS=true` vem ligado: os botões que param e reiniciam
container falhariam contra um socket somente-leitura, e oferecer botão que não
funciona é pior que não oferecer.

## Endurecimento

O ladder inteiro: `ReadOnly=true`, todas as capacidades descartadas,
`User=1000`. Medido com ele conectado — `Connected to Docker` no log e a
interface respondendo —, não só com o container de pé.

O healthcheck é o subcomando do próprio binário, `/dozzle healthcheck`, em
forma exec: a imagem não traz shell, então o `CMD-SHELL` falharia.

## Atualizar

```bash
qh dozzle --update --apply
```

Fixado em `v10.7.1`.

## Backup

Não há o que copiar. Removê-lo não perde dado nenhum — os logs são do Podman.

## Remover

```bash
qh dozzle --remove --apply
```

## Comandos

```bash
systemctl --user status dozzle
podman logs -f dozzle
```

## Créditos

[amir20/dozzle](https://github.com/amir20/dozzle) — MIT.

[Documentação oficial](https://dozzle.dev/)
