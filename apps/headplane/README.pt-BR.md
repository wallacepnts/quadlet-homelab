# Headplane

<img src="https://cdn.jsdelivr.net/gh/homarr-labs/dashboard-icons/svg/headscale.svg" width="64" height="64" alt="">

**[🇺🇸 Read in English](./README.md)**

A interface web que o [Headscale](../headscale/README.pt-BR.md) não traz. Nós,
usuários, chaves de pré-autenticação e ACLs numa tela, em vez de um CLI dentro
de um container.

Ela lê a configuração do próprio headscale e conversa com a API dele — então o
headscale precisa existir antes, e isto não serve pra nada sem ele.

## Instalação

```bash
qh headplane            # mostra o plano
qh headplane --apply
```

Abrir `http://<ip-do-host>:8116/admin` — a interface vive em `/admin`, e a raiz
responde 404 de propósito.

Entrar exige uma chave de API do headscale:

```bash
podman exec headscale headscale apikeys create --expiration 90d
```

<details>
<summary><b>Instalação manual (avançado)</b></summary>

```bash
mkdir -p ~/.config/containers/systemd
mkdir -p ~/.config/containers/volumes/headplane/{config,data}

wget -P ~/.config/containers/systemd/ \
  https://raw.githubusercontent.com/wallacepnts/quadlet-homelab/main/apps/headplane/headplane.container
wget -O ~/.config/containers/volumes/headplane/config/config.yaml \
  https://raw.githubusercontent.com/wallacepnts/quadlet-homelab/main/apps/headplane/config/config.yaml

openssl rand -hex 16 | tr -d '\n' | podman secret create headplane-cookie-secret -

# O container roda como uid 1000, que não é o seu depois do mapeamento
podman unshare chown -R 1000:1000 ~/.config/containers/volumes/headplane

systemctl --user daemon-reload
systemctl --user start headplane
```

</details>

## Arquivos

```
headplane.container   unit
config/config.yaml    a configuração, para dentro do volume
install.ini
```

O `data/` guarda o `hp_persist.db`, que é sessão e estado de interface. Nada
ali é a tailnet: perder isso é logar de novo, só. A tailnet mesmo está no banco
do headscale.

## Ele monta a configuração do headscale

```ini
Volume=%h/.config/containers/volumes/headscale/config:/etc/headscale:ro,Z
```

O Headplane lê esse arquivo para saber o formato da tailnet — domínio base,
prefixos, onde fica o banco. A pasta inteira e não só o arquivo: a política de ACL do
headscale cai ali também, e diretório não deixa dúvida sobre o que o `mkdir -p`
deve criar. Vem somente-leitura, do volume do próprio headscale, o que
significa que **o headscale precisa estar instalado antes** — bind mount de
caminho inexistente falha.

## O que ela muda e o que não muda

Por padrão ela é leitora e cliente de API: lista nós, cria chaves, edita ACL
pela API do headscale.

Reiniciar o headscale quando uma ACL muda exige a integração `docker.enabled` e
o socket do Podman montado dentro deste container. Isso é uma entrega de
verdade — um container que reinicia outros containers — e vem desligado. Ligue
só se quiser essa troca, e acrescente o socket na unit você mesmo.

## Endurecimento

O ladder inteiro: `ReadOnly=true`, todas as capacidades descartadas,
`User=1000`. Medido com a interface de fato respondendo em `/admin/` e gravando
o banco dela no volume.

O healthcheck roda `node` em vez de `curl` ou `wget`: a imagem não tem nenhum
dos dois, e o Node está ali do lado.

## Atualizar

```bash
qh headplane --update --apply
```

Fixado em `0.7.0`.

## Backup

```bash
qh headplane --backup --apply --out ~/backups
```

Pouco a perder, como acima. O que importa é o `qh headscale --backup`.

## Remover

```bash
qh headplane --remove --apply           # para e mantém as sessões
qh headplane --remove --purge --apply   # e apaga o volume e o secret
```

Removê-la não muda nada na tailnet: o headscale segue sem interface.

## Comandos

```bash
systemctl --user status headplane
podman logs -f headplane
```

## Créditos

[tale/headplane](https://github.com/tale/headplane) — MIT.

[Documentação oficial](https://headplane.net/)
