# Gitea Runner

<img src="https://cdn.jsdelivr.net/gh/homarr-labs/dashboard-icons/svg/gitea.svg" width="64" height="64" alt="">

**[🇬🇧 Read in English](./README.md)**

Executa os workflows do Actions do [Gitea](../gitea) ao lado — o mesmo CI que
este repositório recebe do GitHub, numa máquina sua.

> **Ele cria containers pelo socket do Podman.** É assim que roda um job, e é
> também todo o seu raio de alcance: um workflow em qualquer repositório que
> este runner atenda pode fazer o que o `podman` faz com o seu usuário. Aponte
> para repositórios em que você confia, como faria com um shell.

O Actions vem ligado por padrão no Gitea desde a 1.21, então não há nada a
habilitar antes — este repositório fixa a 1.27.3.

## Instalar

```bash
qh gitea-runner            # mostra o plano
qh gitea-runner --apply
```

Ele pede o token de registro. Pegue no Gitea, em **Administração do site →
Actions → Runners → Criar novo Runner**, ou pela linha de comando:

```bash
podman exec -u git gitea gitea actions generate-runner-token
```

O token se gasta no primeiro registro. Depois disso o runner usa o arquivo
`.runner` do volume e nunca mais o lê.

<details>
<summary><b>Instalação manual (avançado)</b></summary>

```bash
# 1. Baixe a unit (sem precisar clonar o repositório)
mkdir -p ~/.config/containers/systemd
wget -P ~/.config/containers/systemd/ \
  https://raw.githubusercontent.com/wallacepnts/quadlet-homelab/main/apps/gitea-runner/gitea-runner.container

# 2. O volume guarda três coisas: a config, o arquivo de registro .runner e o
#    cache do Actions
mkdir -p ~/.config/containers/volumes/gitea-runner/data
wget -O ~/.config/containers/volumes/gitea-runner/data/config.yaml \
  https://raw.githubusercontent.com/wallacepnts/quadlet-homelab/main/apps/gitea-runner/config.yaml

# 3. Qual Gitea, qual nome, e que imagens os labels significam
mkdir -p ~/.config/containers/env
wget -O ~/.config/containers/env/gitea-runner.env \
  https://raw.githubusercontent.com/wallacepnts/quadlet-homelab/main/apps/gitea-runner/gitea-runner.env.example

# 4. O token de registro, vindo do Gitea
mkdir -p ~/.config/containers/secrets/gitea-runner
podman exec -u git gitea gitea actions generate-runner-token \
  > ~/.config/containers/secrets/gitea-runner/token.txt
chmod 600 ~/.config/containers/secrets/gitea-runner/token.txt
podman secret create gitea-runner-token ~/.config/containers/secrets/gitea-runner/token.txt

# 5. O socket que ele dirige, que o podman só serve com isto ligado
systemctl --user enable --now podman.socket

systemctl --user daemon-reload
systemctl --user start gitea-runner
```

</details>

## Arquivos

```
gitea-runner.container
gitea-runner.env.example
config.yaml                 instalado no volume, não ao lado da unit
install.ini
```

## Os labels decidem quanto custa um job

O `runs-on:` de um workflow casa com um label, e um label nomeia uma imagem.
Registrar sem escolher faz o runner pedir `ubuntu-latest` e as irmãs — imagens
feitas para parecer um worker do GitHub, medidas em gigabytes, baixadas no
primeiro job. O `.env` nomeia imagens pequenas no lugar:

```ini
GITEA_RUNNER_LABELS=alpine:docker://docker.io/library/alpine:3
```

Aí o workflow diz `runs-on: alpine`. Os labels são lidos **uma vez**, no
registro: mudá-los depois exige apagar o `.runner` do volume e registrar de
novo com um token novo.

## Dois ajustes que não são o padrão do upstream

O `config.yaml` daqui difere do exemplo distribuído em dois pontos, ambos
medidos e não adivinhados:

- **`cache.dir: /data/cache`.** O padrão é `$HOME/.cache/actcache`, que fica
  dentro da imagem — e a unit a monta somente-leitura. O runner então sobe,
  responde ao health check, e registra `cannot init cache server, it will be
  disabled`. Saudável e pela metade, que é a falha em que este repositório vive
  esbarrando. Apontar para o volume resolve e ainda mantém o cache entre
  reinícios.
- **`metrics.enabled: true`.** Desligado no upstream. O `Notify=healthy` exige
  um `HealthCmd` (regra 14 das convenções), e o `/healthz` em `127.0.0.1:9101`
  é a única coisa que o runner serve. Fica no loopback: a porta não é publicada
  e não há autenticação na frente dela.

## Atualizar

```bash
qh gitea-runner --update --apply
```

Fixado em `3.4.2`. Nada atualiza sozinho — uma versão nova é aplicada quando
você roda o comando acima.

O projeto mudou de nome: era publicado como `gitea/act_runner`, que parou na
`0.6.1`, e hoje é `gitea/runner` com versionamento próprio. Ele também vive no
`gitea.com` e não no GitHub, então o `install.ini` compara com o registry em
vez de uma página de releases que não existe.

## Backup

```bash
qh gitea-runner --backup --apply --out ~/backups
```

Vale pouco: o volume guarda um registro que se refaz em um minuto e um cache
que existe para ser descartado. Restaurar o `.runner` noutra máquina dá dois
runners reivindicando um registro só.

## Remover

```bash
qh gitea-runner --remove --apply           # para, mantém os dados
qh gitea-runner --remove --purge --apply   # e apaga o volume e o secret
```

O Gitea mantém o runner na lista dele de qualquer jeito — apague lá também, em
Administração do site → Actions → Runners.

## Comandos

```bash
systemctl --user status gitea-runner
podman logs -f gitea-runner
podman exec gitea-runner wget -qO- http://127.0.0.1:9101/readyz   # está consultando o Gitea?
```

## Créditos

[gitea/runner](https://gitea.com/gitea/runner) — MIT

[Documentação oficial](https://docs.gitea.com/usage/actions/overview)
