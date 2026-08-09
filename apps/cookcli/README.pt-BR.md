# CookCLI

<img src="https://cdn.simpleicons.org/gnubash" width="64" height="64" alt="">

**[🇺🇸 Read in English](./README.md)**

Receitas em texto puro no formato CookLang — versionáveis em git, sem banco e sem formulário.

## Instalar

```bash
qh cookcli            # mostra o plano
qh cookcli --apply
```

Abrir `http://<ip-do-host>:9080` ou `https://cookcli.<your-tailnet>.ts.net`.

<details>
<summary><b>Instalação manual</b></summary>

```bash
# 1. Baixar a unit (sem precisar clonar o repositório)
mkdir -p ~/.config/containers/systemd
wget -P ~/.config/containers/systemd/ \
  https://raw.githubusercontent.com/wallacepnts/quadlet-homelab/main/apps/cookcli/cookcli.container

# 2. A pasta das receitas. NÃO fazer chown aqui: ela é sua, e o keep-id da
#    unit é justamente o que faz o container aceitar isso.
mkdir -p ~/.config/containers/volumes/cookcli/recipes

# 3. Subir
systemctl --user daemon-reload
systemctl --user start cookcli
```

</details>

## Arquivos

```
cookcli.container
aisle.conf.example
bolo-de-cenoura.cook.example
calda-de-chocolate.cook.example
pantry.conf.example
semana.menu.example
install.ini
```

## Atualizar

```bash
qh cookcli --update --apply
```

Fixado em `0.32.1`. Nada atualiza sozinho — versão nova entra quando você
roda o comando acima.

## Backup

```bash
qh cookcli --backup --apply --out ~/backups
```

Ele para o serviço, empacota os dados, o `.env` e os secrets, e sobe de novo.
A frio de propósito: copiar banco vivo dá um arquivo que só falha na hora de
restaurar.

Pra restaurar, por cima dos dados atuais:

```bash
qh cookcli --restore ~/backups/cookcli-20260809-1200.tar.gz --apply
```

Ele pede que você digite `cookcli` pra confirmar, porque os dados atuais são
apagados antes de o arquivo ser extraído.

## Remover

```bash
qh cookcli --remove --apply           # para e tira, mantendo os dados
qh cookcli --remove --purge --apply   # e apaga volumes, secrets e .env
```

O `--purge` também pede o nome digitado. O nó da tailnet não é desregistrado
por isso — isso é no admin do Tailscale.

## Comandos

```bash
systemctl --user status cookcli
podman logs -f cookcli
```

## Créditos

[cooklang/cookcli](https://github.com/cooklang/cookcli) — MIT

[Documentação oficial](https://demo.cooklang.org)
